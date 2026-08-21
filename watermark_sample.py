# -*- coding: utf-8 -*-
"""Образцы плашки на фото: два варианта расположения."""
from PIL import Image, ImageDraw, ImageFont
import os, sys

PHONE = "+7 982 633-74-06"
SITE = "Двигатели и КПП · Екатеринбург"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def prepare(path, size=1000, crop=0.06, angle=1.2):
    """Обрезка краёв + лёгкий поворот — чтобы снимок не сходился с оригиналом."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    dx, dy = int(w * crop), int(h * crop)
    im = im.crop((dx, dy, w - dx, h - dy))
    im = im.rotate(angle, resample=Image.BICUBIC, expand=False)
    # после поворота срезаем края с пустотой
    w, h = im.size
    m = int(min(w, h) * 0.02)
    im = im.crop((m, m, w - m, h - m))
    im.thumbnail((size, size), Image.LANCZOS)
    return im


def bar(im):
    """Вариант 1: полоса внизу кадра."""
    im = im.copy()
    w, h = im.size
    bar_h = max(34, int(h * 0.085))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, h - bar_h, w, h], fill=(15, 18, 26, 190))
    f_big = ImageFont.truetype(FONT, int(bar_h * 0.46))
    f_small = ImageFont.truetype(FONT, int(bar_h * 0.30))
    d.text((int(w * 0.025), h - bar_h + bar_h * 0.16), PHONE, font=f_big, fill=(255, 255, 255, 235))
    d.text((int(w * 0.025), h - bar_h + bar_h * 0.62), SITE, font=f_small, fill=(200, 206, 220, 220))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def corner(im):
    """Вариант 2: бейдж в углу."""
    im = im.copy()
    w, h = im.size
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(FONT, max(15, int(h * 0.040)))
    tw = d.textlength(PHONE, font=f)
    pad = int(h * 0.018)
    x0, y0 = w - tw - pad * 3, h - f.size - pad * 3
    d.rounded_rectangle([x0, y0, w - pad, h - pad], radius=pad, fill=(232, 68, 42, 220))
    d.text((x0 + pad, y0 + pad), PHONE, font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


src = "photos/orig/00083759_1.jpg"
base = prepare(src)
Image.open(src).convert("RGB").save(os.path.join(OUT, "0-original.jpg"), quality=88)
base.save(os.path.join(OUT, "1-bez-plashki.jpg"), quality=88)
bar(base).save(os.path.join(OUT, "2-plashka-vnizu.jpg"), quality=88)
corner(base).save(os.path.join(OUT, "3-badge-v-uglu.jpg"), quality=88)
for n in ("0-original", "1-bez-plashki", "2-plashka-vnizu", "3-badge-v-uglu"):
    p = os.path.join(OUT, n + ".jpg")
    print(n, Image.open(p).size, f"{os.path.getsize(p)/1024:.0f} КБ")
