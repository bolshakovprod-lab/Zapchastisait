# -*- coding: utf-8 -*-
"""Диагональный водяной знак разной насыщенности."""
from PIL import Image, ImageDraw, ImageFont
import sys, os
from photo_tools import process, FONT

TEXT = "Двигатели и коробки передач"
OUT = sys.argv[1]


def tiled(im, opacity, angle=30, scale=0.055):
    w, h = im.size
    f = ImageFont.truetype(FONT, max(14, int(h * scale)))
    tile = Image.new("RGBA", (int(w * 1.8), int(h * 1.8)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    tw = d.textlength(TEXT, font=f)
    step_x, step_y = int(tw + w * 0.10), int(f.size * 3.4)
    for y in range(0, tile.height, step_y):
        offset = 0 if (y // step_y) % 2 == 0 else step_x // 2
        for x in range(-step_x, tile.width, step_x):
            d.text((x + offset, y), TEXT, font=f, fill=(255, 255, 255, opacity))
    tile = tile.rotate(angle, resample=Image.BICUBIC)
    left = (tile.width - w) // 2
    top = (tile.height - h) // 2
    return Image.alpha_composite(im.convert("RGBA"), tile.crop((left, top, left + w, top + h))).convert("RGB")


src = "photos/orig/00083874_1.jpg"
base = process(src, watermark="bar")
base.save(os.path.join(OUT, "wm-0-bez.jpg"), quality=84)
for name, op in [("wm-1-slabyy-10", 26), ("wm-2-sredniy-18", 46), ("wm-3-plotnyy-28", 72)]:
    tiled(base, op).save(os.path.join(OUT, name + ".jpg"), quality=84)
    print(name, f"{os.path.getsize(os.path.join(OUT, name + '.jpg'))/1024:.0f} КБ")
