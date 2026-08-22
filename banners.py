# -*- coding: utf-8 -*-
"""Баннеры для Авито Рекламы (ADS) из фотографий каталога.

Запуск:  ./venv/bin/python banners.py
Результат: папка banners/
"""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

OUT = "banners"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_R = "/System/Library/Fonts/Supplemental/Arial.ttf"

DARK = (18, 21, 29)
ACCENT = (232, 68, 42)
WHITE = (255, 255, 255)
GREY = (176, 184, 200)

SIZES = {                      # форматы Авито Рекламы
    "400x300": (400, 300),
    "300x300": (300, 300),
    "300x600": (300, 600),
    "300x900": (300, 900),
}

CREATIVES = [
    {"file": "dvigateli", "cat": "двс",
     "top": "КОНТРАКТНЫЕ ДВИГАТЕЛИ", "big": "609 в наличии",
     "sub": "Гарантия · подбор по VIN", "cta": "Смотреть каталог"},
    {"file": "akpp", "cat": "акпп",
     "top": "АКПП, ВАРИАТОРЫ, DSG", "big": "467 коробок",
     "sub": "Проверены · пробег указан", "cta": "Подобрать коробку"},
    {"file": "vin", "cat": "двс",
     "top": "НЕ ЗНАЕТЕ, ЧТО ПОДОЙДЁТ?", "big": "Подбор по VIN",
     "sub": "Бесплатно · ответим за 15 минут", "cta": "Написать"},
]


def font(path, size):
    return ImageFont.truetype(path, size)


def fit(draw, text, f, max_w):
    """Разбивает строку по ширине баннера."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        probe = (cur + " " + w).strip()
        if draw.textlength(probe, font=f) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def photo_for(cat, items, used):
    """Фото с крупным агрегатом, без водяного знака — берём из набора для Авито."""
    for it in items:
        if it["n"] != cat or not it["f"] or it["ph"] in used:
            continue
        p = f'photos/avito/{it["ph"]}_1.jpg'
        if os.path.exists(p):
            used.add(it["ph"])
            return p
    return None


def make(size_name, size, c, photo):
    w, h = size
    tall = h >= 600
    im = Image.new("RGB", (w, h), DARK)
    d0 = ImageDraw.Draw(im)
    pad = int(w * 0.07)

    # ── сначала считаем, сколько места нужно тексту снизу
    scale = 1.0 if w >= 400 else 0.92
    f_big = font(FONT_B, int(w * (0.13 if tall else 0.10) * scale))
    f_sub = font(FONT_R, int(w * 0.05 * scale))
    f_cta = font(FONT_B, int(w * 0.052 * scale))
    f_city = font(FONT_R, int(w * 0.036))

    big_lines = fit(d0, c["big"], f_big, w - pad * 2)
    sub_lines = fit(d0, c["sub"], f_sub, w - pad * 2)

    bh = int(h * (0.075 if tall else 0.115))          # высота кнопки
    gap = int(h * 0.02)
    need = (len(big_lines) * int(f_big.size * 1.12)
            + gap + len(sub_lines) * int(f_sub.size * 1.3)
            + gap + int(f_city.size * 1.5)
            + gap + bh + pad)
    band = max(int(h * 0.34), h - need)               # где заканчивается фото

    # ── фотография сверху, затемнённая
    if photo:
        ph = Image.open(photo).convert("RGB")
        ratio = max(w / ph.width, band / ph.height)
        ph = ph.resize((int(ph.width * ratio), int(ph.height * ratio)), Image.LANCZOS)
        left = max(0, (ph.width - w) // 2)
        ph = ph.crop((left, 0, left + w, band))
        ph = ImageEnhance.Brightness(ph).enhance(0.6)
        im.paste(ph, (0, 0))

    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, band - int(h * 0.06), w, band], fill=(18, 21, 29, 200))

    f_top = font(FONT_B, int(w * 0.046))
    ty = pad
    for line in fit(d, c["top"], f_top, w - pad * 2):
        d.text((pad, ty), line, font=f_top, fill=WHITE)
        ty += int(f_top.size * 1.2)

    # ── текстовый блок под фото
    y = band + gap
    for line in big_lines:
        d.text((pad, y), line, font=f_big, fill=WHITE)
        y += int(f_big.size * 1.12)
    y += gap
    for line in sub_lines:
        d.text((pad, y), line, font=f_sub, fill=GREY)
        y += int(f_sub.size * 1.3)

    by = h - bh - pad
    d.text((pad, by - int(f_city.size * 1.7)), "Екатеринбург · отправка по России",
           font=f_city, fill=GREY)
    d.rounded_rectangle([pad, by, w - pad, by + bh], radius=int(bh * 0.28), fill=ACCENT)
    tw = d.textlength(c["cta"], font=f_cta)
    d.text(((w - tw) / 2, by + (bh - f_cta.size) / 2 - 1), c["cta"], font=f_cta, fill=WHITE)

    path = os.path.join(OUT, f'{c["file"]}_{size_name}.jpg')
    im.save(path, quality=88, optimize=True)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    items = json.load(open("data/parts.json", encoding="utf-8"))["items"]
    used = set()
    made = 0
    for c in CREATIVES:
        photo = photo_for(c["cat"], items, used)
        for name, size in SIZES.items():
            p = make(name, size, c, photo)
            made += 1
    print(f"баннеров готово: {made} ({len(CREATIVES)} макета × {len(SIZES)} формата)")
    for f in sorted(os.listdir(OUT)):
        print(f'  {f}  {os.path.getsize(os.path.join(OUT, f))//1024} КБ')
