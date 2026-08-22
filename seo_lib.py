# -*- coding: utf-8 -*-
"""Транслитерация, ЧПУ-адреса и шаблоны заголовков."""
import re

TRANSLIT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i',
    'й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'',
    'э':'e','ю':'yu','я':'ya',
}

CAT_SEO = {
    "двс": {
        "slug": "dvigateli",
        "one": "контрактный двигатель",
        "many": "Контрактные двигатели",
        "keys": "купить контрактный двигатель, двигатель бу в сборе, мотор бу",
    },
    "акпп": {
        "slug": "akpp",
        "one": "контрактная АКПП",
        "many": "Контрактные АКПП, вариаторы и роботы",
        "keys": "купить акпп бу, автоматическая коробка передач бу, вариатор бу, dsg бу",
    },
    "мкпп": {
        "slug": "mkpp",
        "one": "контрактная МКПП",
        "many": "Контрактные МКПП",
        "keys": "купить мкпп бу, механическая коробка передач бу",
    },
    "раздаточная коробка": {
        "slug": "razdatki",
        "one": "контрактная раздаточная коробка",
        "many": "Контрактные раздаточные коробки",
        "keys": "купить раздатку бу, раздаточная коробка бу",
    },
}


def translit(s):
    s = (s or "").lower()
    out = "".join(TRANSLIT.get(ch, ch) for ch in s)
    out = re.sub(r"[^a-z0-9]+", "-", out)
    return re.sub(r"-{2,}", "-", out).strip("-")


def brand_slug(brand):
    """AUDI/VOLKSWAGEN -> audi-volkswagen"""
    return translit(brand.replace("/", "-").replace(" ", "-"))


def part_url(it):
    """ЧПУ товара: тип-марка-модель-артикул"""
    cat = CAT_SEO.get(it["n"], {}).get("slug", "agregat")
    parts = [cat, it["b"], it["m"], it["e"] or it["d"], it["a"]]
    return "p/" + translit("-".join(str(x) for x in parts if x))[:110] + ".html"


def cat_url(cat, brand=None, model=None, page=1):
    slug = CAT_SEO[cat]["slug"]
    if brand:
        slug += "-" + brand_slug(brand)
    if model:
        slug += "-" + translit(model)[:40]
    if page > 1:
        slug += f"-{page}"
    return f"k/{slug}.html"


def brand_url(brand, page=1):
    slug = brand_slug(brand)
    if page > 1:
        slug += f"-{page}"
    return f"m/{slug}.html"


def money(n):
    return f"{n:,}".replace(",", " ") + " ₽" if n else "цена по запросу"


def car_line(it):
    return " ".join(x for x in (it["b"], it["m"], it["k"]) if x)


def part_title(it, city):
    """До ~70 знаков: что это, для какой машины, где купить, цена."""
    base = f'{it["ti"]}'
    if it["e"] and it["e"] not in base:
        base += f' {it["e"]}'
    tail = f' — купить в {city}'
    if it["p"]:
        tail += f', {money(it["p"])}'
    return (base + tail)[:120]


def part_description(it, city, phone):
    bits = [it["ti"]]
    if it["e"]:
        bits.append("двигатель " + it["e"])
    if it["km"]:
        bits.append(f'пробег {it["km"] * 1000:,}'.replace(",", " ") + " км")
    if it["d"]:
        bits.append("номер " + it["d"])
    head = ", ".join(bits)
    price = f'Цена {money(it["p"])}. ' if it["p"] else ""
    return (f'{head}. {price}В наличии в {city}, артикул {it["a"]}. '
            f'Гарантия, проверка перед отправкой, доставка по России. Тел. {phone}')[:320]


def cat_title(cat, brand, city, count):
    c = CAT_SEO[cat]
    if brand:
        return f'{c["many"]} {brand.title()} — купить бу в {city}, {count} в наличии'
    return f'{c["many"]} — купить бу в {city} с гарантией, {count} в наличии'


def cat_description(cat, brand, city, count, phone):
    c = CAT_SEO[cat]
    who = f'для {brand.title()} ' if brand else ""
    return (f'{c["many"]} {who}в наличии в {city}: {count} позиций с фото, ценами и пробегом. '
            f'Проверка перед отправкой, гарантия, доставка по России до транспортной компании. '
            f'Подбор по VIN бесплатно. Тел. {phone}')[:320]
