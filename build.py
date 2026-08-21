# -*- coding: utf-8 -*-
"""Собирает data/parts.json из прайсов поставщика (.xls).
Запуск:  ./venv/bin/python build.py
"""
import xlrd, json, os, re, sys

PRICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prices")
PHOTO_BASE = {"body": "https://avtodik.ru/picture/images_body/",
              "engine": "https://avtodik.ru/picture/images_engine/"}

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
GEARBOX_KINDS = [
    (re.compile(r"\bcvt\b|вариатор", re.I), "вариатор cvt"),
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

MARKUP = float(os.environ.get("MARKUP", "1.0"))   # наценка: 1.3 = +30%

def s(v):
    """Ячейка -> чистая строка (1С отдаёт числа как 55272425.0, пустоту как 0 и «-»)."""
    if isinstance(v, float):
        v = str(int(v)) if v == int(v) else str(v)
    v = str(v).strip()
    return "" if v in ("-", "<>", "нет", "0", "0.0") else v

def photos(cell, group, invnn):
    urls = [u.strip() for u in str(cell).split(";") if u.strip()]
    if not urls:
        return 0
    # все ссылки вида <base>00219455_N.jpg -> хватит хранить количество
    return len(urls)

def search_words(name, *texts):
    """Слова-синонимы, по которым позиция должна находиться."""
    words = [CAT_SYNONYMS.get(name, "")]
    blob = " ".join(texts)
    for rx, extra in GEARBOX_KINDS:
        if rx.search(blob):
            words.append(extra)
    return " ".join(w for w in words if w)

items, cats, brands = [], {}, {}
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
        price = sh.cell_value(r, hdr["price_min"])
        price = int(round(float(price or 0) * MARKUP))
        name = g("name").strip().lower()
        if ONLY_CATS and name not in ONLY_CATS:
            continue
        name = MERGE_CATS.get(name, name)
        marka = g("marka").upper()
        it = {
            "i": invnn,                       # номер на складе поставщика
            "g": group,                       # body | engine
            "n": name,                        # категория/наименование
            "b": marka,                       # марка
            "m": g("model"),                  # модель
            "k": g("kuzovN"),                 # кузов
            "e": g("engineN"),                # двигатель
            "d": g("modelN"),                 # номер детали
            "o": g("oem_code"),               # OEM-номера
            "p": price,
            "y": g("ayear"),                  # год
            "t": g("remark") or g("comment"), # описание
            "c": g("condition") or "Б/у",
            "f": photos(sh.cell_value(r, hdr["photo"]), group, invnn),
            "x": search_words(name, g("remark"), g("comment"), g("modelN")),
        }
        # сторона (перед/зад, лево/право, верх/низ)
        side = " ".join(x for x in (g("F_R"), g("R_L"), g("U_D")) if x)
        if side:
            it["s"] = side
        items.append(it)
        if name:
            cats[name] = cats.get(name, 0) + 1
        if marka:
            brands[marka] = brands.get(marka, 0) + 1

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
