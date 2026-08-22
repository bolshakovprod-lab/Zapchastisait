# -*- coding: utf-8 -*-
"""XML-фид автозагрузки Авито из каталога.

Запуск:  ./venv/bin/python avito_feed.py
Проверка файла: http://autoload.avito.ru/format/xmlcheck/
"""
import json, os, re, html
from datetime import datetime

# ─── настройки ────────────────────────────────────────────────
PHOTO_BASE = os.environ.get("AVITO_PHOTO_BASE",
                            "https://bolshakovprod-lab.github.io/avito-foto/")
MANAGER = "Андрей"
PHONE = "+79826337406"
ADDRESS = "Свердловская область, Екатеринбург"
MAX_PHOTOS = 5
MAX_ADS = int(os.environ.get("AVITO_MAX_ADS", "0"))   # 0 = все позиции
OUT = "avito.xml"

# Тип запчасти в терминах Авито
SPARE_TYPE = {
    "двс": "Двигатель",
    "акпп": "Коробка передач",
    "мкпп": "Коробка передач",
    "раздаточная коробка": "Раздаточная коробка",
}

E = lambda s: html.escape(str(s or ""), quote=True)


def money(n):
    return f"{n:,}".replace(",", " ") + " ₽" if n else "по запросу"


def title_of(it):
    """До 50 знаков — ограничение Авито."""
    base = it["ti"]
    if it["e"] and it["e"] not in base and len(base) + len(it["e"]) < 46:
        base += " " + it["e"]
    return base[:50]


def description_of(it):
    """Описание: что за агрегат, состояние, условия. Без контактов и ссылок —
    Авито их запрещает в тексте объявления."""
    bits = [it["t"].rstrip(".")]
    if it["note"]:
        bits.append(f'Комплектация: {it["note"]}')
    rows = []
    if it["b"]:
        rows.append(f'Марка: {it["b"].title()}')
    if it["m"]:
        rows.append(f'Модель: {it["m"]}')
    if it["k"]:
        rows.append(f'Кузов: {it["k"]}')
    if it["e"]:
        rows.append(f'Двигатель: {it["e"]}')
    if it["km"]:
        rows.append(f'Пробег: {it["km"] * 1000:,}'.replace(",", " ") + " км")
    if it["d"]:
        rows.append(f'Номер агрегата: {it["d"]}')
    if it["o"]:
        rows.append(f'OEM-номера: {it["o"]}')
    rows.append(f'Артикул: {it["a"]}')

    text = "\n".join(bits) + "\n\n" + "\n".join(rows) + """

Контрактный агрегат, привезён из Японии, Кореи или Европы, без пробега по России.
Перед отправкой проверяем и фотографируем — пришлём фото и видео именно вашего
экземпляра до оплаты.

Гарантия на проверку и установку. Поможем подобрать по VIN бесплатно.
Отправляем по всей России, до транспортной компании доставка бесплатно."""
    return text.strip()


def images_of(it):
    return [f'{PHOTO_BASE}{it["ph"]}_{n}.jpg'
            for n in range(1, min(it["f"], MAX_PHOTOS) + 1)]


def ad_xml(it):
    imgs = images_of(it)
    if not imgs:
        return ""       # объявление без фото на Авито бессмысленно
    parts = [
        f'    <Id>{E(it["a"])}</Id>',
        f'    <Category>Запчасти и аксессуары</Category>',
        f'    <GoodsType>Запчасти</GoodsType>',
        f'    <SparePartType>{E(SPARE_TYPE.get(it["n"], "Двигатель"))}</SparePartType>',
        f'    <Condition>Б/у</Condition>',
        f'    <Title>{E(title_of(it))}</Title>',
        f'    <Description><![CDATA[{description_of(it)}]]></Description>',
    ]
    if it["p"]:
        parts.append(f'    <Price>{it["p"]}</Price>')
    if it["o"]:
        parts.append(f'    <OEM>{E(it["o"].split(",")[0].strip())}</OEM>')
    parts += [
        f'    <Address>{E(ADDRESS)}</Address>',
        f'    <ManagerName>{E(MANAGER)}</ManagerName>',
        f'    <ContactPhone>{E(PHONE)}</ContactPhone>',
        '    <Images>',
        *[f'      <Image url="{E(u)}"/>' for u in imgs],
        '    </Images>',
    ]
    return "  <Ad>\n" + "\n".join(parts) + "\n  </Ad>"


if __name__ == "__main__":
    d = json.load(open("data/parts.json", encoding="utf-8"))
    items = [it for it in d["items"] if it["f"]]
    if MAX_ADS:
        # сначала самые маржинальные — если размещаем не весь каталог
        items = sorted(items, key=lambda x: -(x["p"] or 0))[:MAX_ADS]

    ads = [ad_xml(it) for it in items]
    ads = [a for a in ads if a]
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<Ads formatVersion="3" target="Avito.ru">\n'
           + "\n".join(ads) + "\n</Ads>\n")
    open(OUT, "w", encoding="utf-8").write(xml)

    print(f"объявлений в фиде: {len(ads)}")
    print(f"файл: {OUT}, {os.path.getsize(OUT)/1048576:.1f} МБ")
    print(f"фото берутся с: {PHOTO_BASE}")
