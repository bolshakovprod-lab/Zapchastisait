# -*- coding: utf-8 -*-
"""Логотип для аватара: MAX, Telegram, Авито."""
import math, os
from PIL import Image, ImageDraw, ImageFont

OUT = "logo"
FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FR = "/System/Library/Fonts/Supplemental/Arial.ttf"
S = 800                      # аватар с запасом
ACCENT = (232, 68, 42)
DARK = (18, 21, 29)
WHITE = (255, 255, 255)
GREY = (150, 160, 180)


def center_text(d, box, text, font, fill):
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    d.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), text, font=font, fill=fill)


def gear(d, cx, cy, r_out, r_in, teeth=10, fill=WHITE):
    pts = []
    for i in range(teeth * 2):
        a = math.pi * i / teeth
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill)


def v1_red():
    """Красный квадрат, белая монограмма — как на сайте."""
    im = Image.new("RGB", (S, S), ACCENT)
    d = ImageDraw.Draw(im)
    center_text(d, (0, -S * 0.02, S, S), "ДК", ImageFont.truetype(FB, int(S * 0.46)), WHITE)
    return im


def v2_dark():
    """Тёмный фон, монограмма и красная черта под ней."""
    im = Image.new("RGB", (S, S), DARK)
    d = ImageDraw.Draw(im)
    center_text(d, (0, -S * 0.06, S, S), "ДК", ImageFont.truetype(FB, int(S * 0.42)), WHITE)
    w = int(S * 0.26)
    y = int(S * 0.66)
    d.rounded_rectangle([(S - w) / 2, y, (S + w) / 2, y + S * 0.035],
                        radius=int(S * 0.018), fill=ACCENT)
    return im


def v3_gear():
    """Шестерня с монограммой — читается как «агрегаты»."""
    im = Image.new("RGB", (S, S), DARK)
    d = ImageDraw.Draw(im)
    gear(d, S / 2, S / 2, S * 0.40, S * 0.335, 12, ACCENT)
    d.ellipse([S * 0.5 - S * 0.30, S * 0.5 - S * 0.30,
               S * 0.5 + S * 0.30, S * 0.5 + S * 0.30], fill=DARK)
    center_text(d, (0, -S * 0.01, S, S), "ДК", ImageFont.truetype(FB, int(S * 0.30)), WHITE)
    return im


def v4_text():
    """Без монограммы: «ДВС / КПП» в две строки."""
    im = Image.new("RGB", (S, S), DARK)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FB, int(S * 0.24))
    center_text(d, (0, S * 0.10, S, S * 0.46), "ДВС", f, WHITE)
    center_text(d, (0, S * 0.52, S, S * 0.88), "КПП", f, ACCENT)
    d.rounded_rectangle([S * 0.30, S * 0.485, S * 0.70, S * 0.508],
                        radius=int(S * 0.011), fill=(90, 100, 120))
    return im


def v4_compact():
    """Тот же макет, но буквы во всю площадь — для значка 34×34 и фавикона."""
    im = Image.new("RGB", (S, S), DARK)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FB, int(S * 0.40))
    center_text(d, (0, S * 0.02, S, S * 0.46), "ДВС", f, WHITE)
    center_text(d, (0, S * 0.54, S, S * 0.98), "КПП", f, ACCENT)
    d.rounded_rectangle([S * 0.16, S * 0.478, S * 0.84, S * 0.512],
                        radius=int(S * 0.017), fill=(90, 100, 120))
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("1-krasnyy", v1_red), ("2-tyomnyy", v2_dark),
                     ("3-shesternya", v3_gear), ("4-dvs-kpp", v4_text),
                     ("4-dvs-kpp-compact", v4_compact)]:
        im = fn()
        im.save(f"{OUT}/{name}.png")
        # предпросмотр в круге — так его увидят в мессенджерах
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, S, S], fill=255)
        prev = Image.new("RGB", (S, S), (244, 245, 248))
        prev.paste(im, (0, 0), mask)
        prev.save(f"{OUT}/{name}_krug.png")
    print("готово:", ", ".join(sorted(os.listdir(OUT))))
