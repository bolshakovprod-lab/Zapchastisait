# -*- coding: utf-8 -*-
"""Свои описания и артикулы вместо текстов поставщика.
Используется из build.py — отдельно запускать не нужно.
"""
import re

ART_PREFIX = "ДК-"

# пометки поставщика -> человеческий текст
NOTE_WORDS = {
    "б/навеса": "без навесного оборудования",
    "б/навесного": "без навесного оборудования",
    "б/разд.": "без раздаточной коробки",
    "без разд.": "без раздаточной коробки",
    "без раздатки": "без раздаточной коробки",
    "б/актуатора": "без актуатора",
    "б/датч.": "без датчиков",
    "в пути": "в пути на склад",
    "корпус брак": "повреждён корпус",
    "поддон брак": "повреждён поддон",
    "фишка управл. брак": "повреждён разъём управления",
}
# сокращения внутри «б/генер./гур/конд./сцепл.»
PART_WORDS = {
    "генер": "генератора", "гур": "ГУР", "конд": "кондиционера", "сцепл": "сцепления",
    "кат": "катализатора", "натяж": "натяжителя", "нат": "натяжителя",
    "засл": "дроссельной заслонки", "старт": "стартера",
}
# скобки, которые несут тип агрегата, а не примечание
SKIP_NOTE = re.compile(r"^(кпп|двс|акпп|мкпп|ркпп|робот|вариатор|раздаточная коробка|"
                       r"угловая передача|\d+\s*ткм|[a-z0-9/\s.\-]+)$", re.I)

BRACKETS = re.compile(r"\(([^)]*)\)")
JUNK_NO = re.compile(r"^\d+\s*(km|км|ткм|тыс)\.?$", re.I)
VOLUME = re.compile(r"\b(\d[.,]\d)\b")
POWER = re.compile(r"(\d{2,3})\s*hp", re.I)

TYPE_WORDS = {
    "двс": "Контрактный двигатель",
    "мкпп": "Контрактная МКПП",
    "раздаточная коробка": "Контрактная раздаточная коробка",
}
KIND_WORDS = {
    "Вариатор": "Контрактный вариатор",
    "Робот DSG": "Контрактный робот DSG",
    "Автомат": "Контрактная АКПП",
    "Механика": "Контрактная МКПП",
}


def article(invnn):
    """Свой артикул. Обратимо для нас, но не читается снаружи."""
    return ART_PREFIX + str(int(invnn) * 7 + 13)


def file_stem(article_no):
    """ДК-586326 -> dk586326: имя файла с фото."""
    return "dk" + article_no.replace(ART_PREFIX, "").replace("-", "")


def _expand(chunk):
    """«б/генер./гур/конд.» -> «без генератора, ГУР, кондиционера»"""
    if chunk.startswith("б/"):
        body = chunk[2:]
    elif chunk.startswith("без "):
        body = chunk[4:]
    else:
        body = chunk
    parts = []
    for piece in re.split(r"[/,]", body):
        piece = piece.strip(" .").lower()
        if not piece:
            continue
        parts.append(PART_WORDS.get(piece, piece))
    return "без " + ", ".join(parts) if parts else ""


def notes(remark):
    """Пометки о комплектации и состоянии — их терять нельзя."""
    out = []
    for chunk in BRACKETS.findall(remark or ""):
        chunk = chunk.strip().lower().rstrip(",")
        if not chunk or not re.search(r"[а-я]", chunk) or SKIP_NOTE.match(chunk):
            continue
        if chunk in NOTE_WORDS:
            out.append(NOTE_WORDS[chunk])
        elif chunk.startswith(("б/", "без ")):
            out.append(_expand(chunk))
        else:
            out.append(chunk)
    seen, uniq = set(), []
    for n in out:
        if n and n not in seen:
            seen.add(n)
            uniq.append(n)
    return "; ".join(uniq)


def title_of(cat, kind, brand, model, kuzov):
    head = KIND_WORDS.get(kind) or TYPE_WORDS.get(cat) or "Контрактный агрегат"
    car = " ".join(x for x in (brand.title(), model.upper()) if x).strip()
    tail = kuzov.upper() if kuzov and kuzov.upper() not in model.upper() else ""
    return " ".join(x for x in (head, car, tail) if x)


def describe(cat, kind, brand, model, kuzov, engine, part_no, km, year, remark):
    """Заголовок и полное описание — собраны из полей, а не скопированы."""
    src = remark or ""
    title = title_of(cat, kind, brand, model, kuzov)

    bits = []
    vol = VOLUME.search(src)
    hp = POWER.search(src)
    if cat == "двс":
        if vol:
            bits.append(vol.group(1).replace(",", ".") + " л")
        if hp:
            bits.append(hp.group(1) + " л.с.")
    if engine:
        bits.append(("двигатель " if cat != "двс" else "") + engine)
    if km:
        bits.append(f"пробег {km * 1000:,}".replace(",", " ") + " км")
    if year:
        bits.append(f"{year} г.")
    if part_no and not JUNK_NO.match(part_no) and part_no.lower() != engine.lower():
        # у коробок в этом поле код агрегата, а не номер детали
        bits.append(("код " if cat in ("акпп", "мкпп") else "номер ") + part_no)

    text = title + (" — " + ", ".join(bits) if bits else "") + "."
    note = notes(src)
    return title, text, note


# Марки кириллицей — клиенты ищут «мазда», а не «mazda»
BRAND_RU = {
    "MAZDA": "мазда", "NISSAN": "ниссан нисан", "AUDI": "ауди", "VOLVO": "вольво",
    "MERCEDES": "мерседес мерс мерин", "MITSUBISHI": "митсубиси мицубиси",
    "FORD": "форд", "BMW": "бмв", "HONDA": "хонда", "JEEP": "джип",
    "RENAULT": "рено", "CADILLAC": "кадиллак", "LINCOLN": "линкольн",
    "OPEL": "опель", "CHEVROLET": "шевроле шеви", "TOYOTA": "тойота",
    "VOLKSWAGEN": "фольксваген фольц вольксваген", "SKODA": "шкода",
    "JAGUAR": "ягуар", "ALFA ROMEO": "альфа ромео", "CHRYSLER": "крайслер",
    "SUBARU": "субару", "PEUGEOT": "пежо", "SUZUKI": "сузуки судзуки",
    "DAIHATSU": "дайхатсу", "ROVER": "ровер", "LAND ROVER": "ленд ровер",
    "SAAB": "сааб", "SMART": "смарт", "HYUNDAI": "хендай хундай хёндай",
    "KIA": "киа", "ISUZU": "исузу", "FIAT": "фиат", "HINO": "хино",
    "DODGE": "додж", "MINI COOPER": "мини купер", "PORSCHE": "порше",
    "CITROEN": "ситроен", "SSANG YONG": "ссангйонг саньенг", "HUMMER": "хаммер",
    "LEXUS": "лексус", "LANCIA": "лянча",
}


def brand_ru(marka):
    """Кириллические варианты для марки, в том числе для сдвоенных «CITROEN/PEUGEOT»."""
    out = []
    for part in re.split(r"[/,]", marka):
        part = part.strip().upper()
        if part in BRAND_RU:
            out.append(BRAND_RU[part])
    return " ".join(out)
