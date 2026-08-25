# -*- coding: utf-8 -*-
"""Обработка фото: зеркало, обрезка, поворот, контраст, плашка с телефоном."""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

PHONE = "+7 982 025-28-92"
SITE = "Двигатели и КПП · Екатеринбург"
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

MIRROR = False     # зеркало отключено: патрубки и разъёмы должны быть на своих местах
CROP = 0.18        # сколько срезать по краям
ANGLE = 3.0        # поворот, градусы
CONTRAST = 1.06    # лёгкий сдвиг контраста
SATURATION = 0.94

WM_TEXT = "Двигатели и коробки передач"
WM_OPACITY = 72    # плотность диагонального знака (0-255)
WM_ANGLE = 30


def process(path, size=1000, watermark="bar"):
    im = Image.open(path).convert("RGB")
    if MIRROR:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = im.size
    dx, dy = int(w * CROP / 2), int(h * CROP / 2)
    im = im.crop((dx, dy, w - dx, h - dy))
    im = im.rotate(ANGLE, resample=Image.BICUBIC, expand=False)
    w, h = im.size
    m = int(min(w, h) * 0.04)          # срезаем пустые углы после поворота
    im = im.crop((m, m, w - m, h - m))
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = ImageEnhance.Color(im).enhance(SATURATION)
    im.thumbnail((size, size), Image.LANCZOS)
    if watermark:
        im = tiled(im)
        im = stamp(im, watermark)
    return im


def tiled(im, opacity=WM_OPACITY, angle=WM_ANGLE, scale=0.055):
    """Диагональный повтор надписи — его не отрезать, как плашку."""
    w, h = im.size
    f = ImageFont.truetype(FONT, max(14, int(h * scale)))
    tile = Image.new("RGBA", (int(w * 1.8), int(h * 1.8)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    tw = d.textlength(WM_TEXT, font=f)
    step_x, step_y = int(tw + w * 0.10), int(f.size * 3.4)
    for y in range(0, tile.height, step_y):
        offset = 0 if (y // step_y) % 2 == 0 else step_x // 2
        for x in range(-step_x, tile.width, step_x):
            d.text((x + offset, y), WM_TEXT, font=f, fill=(255, 255, 255, opacity))
    tile = tile.rotate(angle, resample=Image.BICUBIC)
    left, top = (tile.width - w) // 2, (tile.height - h) // 2
    return Image.alpha_composite(
        im.convert("RGBA"), tile.crop((left, top, left + w, top + h))).convert("RGB")


def stamp(im, kind="bar"):
    w, h = im.size
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if kind == "corner":
        f = ImageFont.truetype(FONT, max(15, int(h * 0.040)))
        tw = d.textlength(PHONE, font=f)
        pad = int(h * 0.018)
        x0, y0 = w - tw - pad * 3, h - f.size - pad * 3
        d.rounded_rectangle([x0, y0, w - pad, h - pad], radius=pad, fill=(232, 68, 42, 220))
        d.text((x0 + pad, y0 + pad), PHONE, font=f, fill=(255, 255, 255, 255))
    else:
        bar_h = max(34, int(h * 0.085))
        d.rectangle([0, h - bar_h, w, h], fill=(15, 18, 26, 190))
        f_big = ImageFont.truetype(FONT, int(bar_h * 0.46))
        f_small = ImageFont.truetype(FONT, int(bar_h * 0.30))
        d.text((int(w * 0.025), h - bar_h + bar_h * 0.16), PHONE, font=f_big, fill=(255, 255, 255, 235))
        d.text((int(w * 0.025), h - bar_h + bar_h * 0.62), SITE, font=f_small, fill=(200, 206, 220, 220))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
