# -*- coding: utf-8 -*-
"""Собирает data/parts.json из прайсов поставщика (.xls).
Запуск:  ./venv/bin/python build.py
"""
import xlrd, json, os, re, sys
from describe import describe, article, brand_ru, file_stem, brands_of, models_of
from seo_lib import part_url

PRICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prices")
PHOTO_BASE = {"big": "photos/big/", "thumb": "photos/thumb/"}

# Какие разделы прайса публикуем. Сейчас только моторный.
# Чтобы вернуть кузов и салон -> ONLY_GROUPS = {"engine", "body"}
ONLY_GROUPS = {"engine"}

# Какие категории публикуем: только агрегаты в сборе — двигатели и коробки.
# Вариаторы (CVT), роботы и DSG лежат внутри "акпп", отдельной категории у поставщика нет.
# Чтобы вернуть навесное (генераторы, стартеры, ЭБУ, форсунки) -> ONLY_CATS = None
ONLY_CATS = {
    "двс",                  # двигатели в сборе
    "акпп",                 # автоматы, вариаторы, роботы, DSG
    "мкпп",                 # механика
    "раздатка",
    "раздаточная коробка",
}

# "раздатка" и "раздаточная коробка" у поставщика — одно и то же
MERGE_CATS = {"раздатка": "раздаточная коробка"}

# Как категория называется на сайте
CAT_LABELS = {
    "двс": "Двигатели",
    "акпп": "АКПП, вариаторы, роботы",
    "мкпп": "МКПП",
    "раздаточная коробка": "Раздаточные коробки",
}

# Синонимы для поиска: чтобы "двигатель", "автомат", "механика" тоже находили
CAT_SYNONYMS = {
    "двс": "двигатель мотор двс",
    "акпп": "акпп автомат автоматическая коробка передач",
    "мкпп": "мкпп механика механическая коробка передач",
    "раздаточная коробка": "раздатка раздаточная коробка",
}

# Тип коробки распознаём по описанию, а не вешаем на всю категорию:
# иначе запрос "вариатор" выдаёт все автоматы подряд.
KM_RX = re.compile(r"(\d{1,3})\s*т\.?\s*км", re.I)      # в прайсе пишут "111ткм"

GEARBOX_KINDS = [
    (re.compile(r"cvt|вариатор|\bre0f|\bjf0|k310|multitronic|xtronic|lineartronic", re.I),
     "вариатор cvt"),
    (re.compile(r"dsg|\bdct\b|робот", re.I), "робот dsg"),   # в прайсе пишут "6DSG", "7DSG"
]

def detect_group(sh, photo_col):
    """Раздел определяем по ссылкам на фото: images_engine -> двигатели, иначе кузов."""
    for r in range(1, min(sh.nrows, 200)):
        v = str(sh.cell_value(r, photo_col))
        if "images_engine" in v:
            return "engine"
        if "images_body" in v:
            return "body"
    return "body"

MARKUP = float(os.environ.get("MARKUP", "1.33"))   # наценка: 1.33 = +33%
# Минимальная маржа с позиции — плавающая: 14 000 ₽ на дешёвых агрегатах,
# 17 500 ₽ на дорогих. Между 5 000 и 50 000 закупа растёт линейно.
MIN_MARGIN_LOW = 14000
MIN_MARGIN_HIGH = 17500
MIN_MARGIN_FROM = 5000
MIN_MARGIN_TO = 50000


def min_margin(buy):
    if buy <= MIN_MARGIN_FROM:
        return MIN_MARGIN_LOW
    if buy >= MIN_MARGIN_TO:
        return MIN_MARGIN_HIGH
    k = (buy - MIN_MARGIN_FROM) / (MIN_MARGIN_TO - MIN_MARGIN_FROM)
    return MIN_MARGIN_LOW + k * (MIN_MARGIN_HIGH - MIN_MARGIN_LOW)
MIN_BUY = 5000                                     # дешевле этого закупа не публикуем вовсе
ROUND_TO = 500                                     # округление цены вверх, ₽

def s(v):
    """Ячейка -> чистая строка (1С отдаёт числа как 55272425.0, пустоту как 0 и «-»)."""
    if isinstance(v, float):
        v = str(int(v)) if v == int(v) else str(v)
    v = str(v).strip()
    return "" if v in ("-", "<>", "нет", "0", "0.0") else v

MAX_PHOTOS = 5   # столько снимков публикуем; см. process_photos.py


def photos(cell, group, invnn):
    urls = [u.strip() for u in str(cell).split(";") if u.strip()]
    if not urls:
        return 0
    # ссылки вида <base>00219455_N.jpg — хватит хранить количество
    return min(len(urls), MAX_PHOTOS)

def mileage(*texts):
    """Пробег в тысячах км из описания, если он там есть."""
    m = KM_RX.search(" ".join(texts))
    if not m:
        return 0
    km = int(m.group(1))
    return km if 1 <= km <= 999 else 0


def gearbox_kind(name, *texts):
    """Короткая метка для карточки: Вариатор, Робот DSG, Автомат, Механика."""
    blob = " ".join(texts)
    if name in ("акпп",):
        if GEARBOX_KINDS[0][0].search(blob):
            return "Вариатор"
        if GEARBOX_KINDS[1][0].search(blob):
            return "Робот DSG"
        return "Автомат"
    if name == "мкпп":
        return "Механика"
    return ""


def search_words(name, *texts):
    """Слова-синонимы, по которым позиция должна находиться."""
    words = [CAT_SYNONYMS.get(name, "")]
    if name in ("акпп", "мкпп"):
        blob = " ".join(texts)
        for rx, extra in GEARBOX_KINDS:
            if rx.search(blob):
                words.append(extra)
    return " ".join(w for w in words if w)

items, cats, brands, sources = [], {}, {}, []
files = sorted(f for f in os.listdir(PRICES_DIR) if f.lower().endswith((".xls", ".xlsx")))
if not files:
    sys.exit("Положите прайсы поставщика (.xls) в папку prices/ и запустите снова.")
for fname in files:
    sh = xlrd.open_workbook(os.path.join(PRICES_DIR, fname)).sheet_by_index(0)
    hdr = {str(sh.cell_value(0, c)).strip(): c for c in range(sh.ncols)}
    group = detect_group(sh, hdr["photo"])
    if group not in ONLY_GROUPS:
        print(f"  {fname}: раздел {group} пропущен (см. ONLY_GROUPS)")
        continue
    print(f"  {fname}: {sh.nrows-1} строк -> раздел {group}")
    for r in range(1, sh.nrows):
        g = lambda k: s(sh.cell_value(r, hdr[k])) if k in hdr else ""
        invnn = g("invnn")
        if not invnn:
            continue
        buy = float(sh.cell_value(r, hdr["price_min"]) or 0)
        if buy and buy < MIN_BUY:
            continue                               # возиться с такой позицией смысла нет
        price = max(buy * MARKUP, buy + min_margin(buy)) if buy else 0
        # округляем вверх до ROUND_TO, чтобы в каталоге не было цен вида 86 450 ₽
        price = int(-(-price // ROUND_TO) * ROUND_TO) if price else 0
        name = g("name").strip().lower()
        if ONLY_CATS and name not in ONLY_CATS:
            continue
        name = MERGE_CATS.get(name, name)
        marka = g("marka").upper()
        km = mileage(g("remark"), g("comment"))
        kind = gearbox_kind(name, g("remark"), g("comment"), g("modelN"), g("oem_code"))
        title, text, note = describe(name, kind, marka, g("model"), g("kuzovN"),
                                     g("engineN"), g("modelN"), km, g("ayear"), g("remark"))
        art = article(invnn)
        it = {
            "a": art,                         # наш артикул
            "ph": file_stem(art),             # имя файлов с фото
            "n": name,                        # категория/наименование
            "b": marka,                       # марка как в прайсе
            "bs": brands_of(marka),           # марки по отдельности — для навигации
            "ms": models_of(marka, g("model")),  # модели по отдельности, с синонимами
            "m": g("model"),                  # модель
            "k": g("kuzovN"),                 # кузов
            "e": g("engineN"),                # двигатель
            "d": g("modelN"),                 # номер детали
            "o": g("oem_code"),               # OEM-номера
            "p": price,
            "y": g("ayear"),                  # год
            "t": text,                        # своё описание, собрано из полей
            "ti": title,
            "note": note,                     # пометки о комплектации
            "c": g("condition") or "Б/у",
            "f": photos(sh.cell_value(r, hdr["photo"]), group, invnn),
            "x": " ".join(filter(None, [
                search_words(name, g("remark"), g("comment"), g("modelN"), g("oem_code")),
                brand_ru(marka)])),
            "km": km,                         # пробег, тыс. км (0 = не указан)
            "kind": kind,
        }
        # сторона (перед/зад, лево/право, верх/низ)
        side = " ".join(x for x in (g("F_R"), g("R_L"), g("U_D")) if x)
        if side:
            it["s"] = side
        it["u"] = part_url(it)            # адрес страницы товара
        items.append(it)
        sources.append((invnn, int(buy)))
        if name:
            cats[name] = cats.get(name, 0) + 1
        for one in brands_of(marka):
            brands[one] = brands.get(one, 0) + 1

with open("articles.csv", "w", encoding="utf-8") as f:
    f.write("наш артикул;артикул поставщика;закуп;цена на сайте;маржа;описание\n")
    for it, (invnn, buy) in zip(items, sources):
        f.write(f'{it["a"]};{invnn};{buy};{it["p"]};{it["p"] - buy};{it["t"]}\n')

items.sort(key=lambda x: (x["n"], x["b"], x["m"]))
out = {
    "count": len(items),
    "brands": sorted(brands.items(), key=lambda x: -x[1]),
    "cats": sorted(cats.items(), key=lambda x: -x[1]),
    "photoBase": PHOTO_BASE,
    "catLabels": CAT_LABELS,
    "items": items,
}
os.makedirs("data", exist_ok=True)
with open("data/parts.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print("позиций:", len(items), "| марок:", len(brands), "| категорий:", len(cats))
print("размер:", round(os.path.getsize("data/parts.json") / 1048576, 2), "МБ")
