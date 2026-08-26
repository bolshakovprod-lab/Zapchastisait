# -*- coding: utf-8 -*-
"""Баннеры v2: фото на весь холст, мягкий градиент, нормальная типографика."""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

OUT = "banners"
# IBM Plex: в системном Arial нет символа рубля
_HERE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.join(_HERE, "fonts", "PlexSans-SemiBold.ttf")
FR = os.path.join(_HERE, "fonts", "PlexSans-Regular.ttf")
ACCENT = (232, 68, 42)
WHITE = (255, 255, 255)
SOFT = (198, 206, 220)


def f(path, size):
    return ImageFont.truetype(path, max(9, int(size)))


def spaced(text, gap=" "):
    """Разрядка для мелкого заголовка — выглядит дороже."""
    return gap.join(text)


def gradient(size, start=0.0, power=1.25, floor=0.30):
    """Сверху лёгкая дымка, снизу почти чёрный — текст читается на любом фото."""
    w, h = size
    grad = Image.new("L", (1, h))
    px = grad.load()
    for y in range(h):
        t = max(0.0, (y / h - start) / (1 - start))
        px[0, y] = int(255 * min(1.0, floor + (1 - floor) * (t ** power)))
    return grad.resize(size)


def collage(photos, size, bright=0.8, cols=None):
    """Сетка из фотографий агрегатов — вместо одного снимка «стена товара»."""
    w, h = size
    if cols is None:
        cols = 3 if w >= h else 2
    rows = max(2, round(cols * h / w))
    cw, ch = w // cols + 1, h // rows + 1
    canvas = Image.new("RGB", size, (14, 17, 24))
    i = 0
    for r in range(rows):
        for col in range(cols):
            src = photos[i % len(photos)]
            i += 1
            try:
                tile = Image.open(src).convert("RGB")
            except Exception:
                continue
            ratio = max(cw / tile.width, ch / tile.height)
            tile = tile.resize((int(tile.width * ratio), int(tile.height * ratio)), Image.LANCZOS)
            left = (tile.width - cw) // 2
            top = (tile.height - ch) // 2
            tile = tile.crop((left, top, left + cw, top + ch))
            canvas.paste(tile, (col * cw, r * ch))
    # тонкие тёмные швы между плитками — чтобы читалось как стеллаж
    d = ImageDraw.Draw(canvas)
    for col in range(1, cols):
        d.line([(col * cw, 0), (col * cw, h)], fill=(14, 17, 24), width=max(2, w // 150))
    for r in range(1, rows):
        d.line([(0, r * ch), (w, r * ch)], fill=(14, 17, 24), width=max(2, w // 150))
    return ImageEnhance.Brightness(canvas).enhance(bright)


def cover(photo, size, bright=0.82):
    w, h = size
    im = Image.open(photo).convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    im = im.crop(((im.width - w) // 2, (im.height - h) // 2,
                  (im.width - w) // 2 + w, (im.height - h) // 2 + h))
    return ImageEnhance.Brightness(im).enhance(bright)


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        probe = (cur + " " + wd).strip()
        if d.textlength(probe, font=fnt) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


def build_wide(size, c, photo):
    """Раскладка для растяжек вроде 1256×300: текст слева, кнопка справа.
    Обычный макет там наезжает сам на себя — высоты не хватает."""
    w, h = size
    base = collage(photo, size, 0.62, cols=max(4, w // (h or 1)))
    im = base.convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, int(w * 0.66), h], fill=(10, 13, 20, 205))

    pad = int(h * 0.13)
    f_top = f(FB, h * 0.10)
    f_big = f(FB, h * 0.23)
    f_sub = f(FR, h * 0.093)
    f_cta = f(FB, h * 0.115)

    y = int(h * 0.12)
    f_city = f(FB, h * 0.075)
    d.text((pad, y), spaced("ЕКАТЕРИНБУРГ · В НАЛИЧИИ"), font=f_city, fill=ACCENT)
    y += int(f_city.size * 1.7)

    d.text((pad, y), c["top"], font=f_top, fill=SOFT)
    y += int(f_top.size * 1.4)
    d.rounded_rectangle([pad, y, pad + int(h * 0.28), y + max(2, int(h * 0.018))],
                        radius=2, fill=ACCENT)
    y += int(h * 0.045)
    # ужимаем кегль, пока оффер не влезет в одну строку
    box_w = int(w * 0.60) - pad * 2
    size_big = h * 0.23
    while size_big > h * 0.13:
        f_big = f(FB, size_big)
        if d.textlength(c["big"], font=f_big) <= box_w:
            break
        size_big *= 0.94
    d.text((pad, y), c["big"], font=f_big, fill=WHITE)
    y += int(f_big.size * 1.1)
    y += int(h * 0.02)
    for line in wrap(d, c["sub"], f_sub, int(w * 0.60) - pad * 2)[:2]:
        d.text((pad, y), line, font=f_sub, fill=SOFT)
        y += int(f_sub.size * 1.3)

    # кнопка справа, по центру высоты; ширину и кегль подгоняем под надпись
    bh = int(h * 0.34)
    size_cta = h * 0.125
    while size_cta > h * 0.075:
        f_cta = f(FB, size_cta)
        if d.textlength(c["cta"], font=f_cta) <= w * 0.24 - bh * 0.6:
            break
        size_cta *= 0.94
    bw = int(min(w * 0.30, d.textlength(c["cta"], font=f_cta) + bh * 1.1))
    bx, by = w - bw - pad, (h - bh) // 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=int(bh * 0.3), fill=ACCENT)
    tw = d.textlength(c["cta"], font=f_cta)
    d.text((bx + (bw - tw) / 2, by + (bh - f_cta.size) / 2 - f_cta.size * 0.08),
           c["cta"], font=f_cta, fill=WHITE)
    return im.convert("RGB")


def build(size, c, photo, style="dark"):
    w, h = size
    if w / h >= 2.2:
        return build_wide(size, c, photo)
    base = (collage(photo, size, 0.78) if isinstance(photo, list)
            else cover(photo, size, 0.8))
    dark = Image.new("RGB", size, (10, 13, 20))
    base = Image.composite(dark, base, gradient(size, 0.3 if h > w else 0.22))
    im = base.convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    pad = int(w * 0.075)

    # ── верх: плашка города и наличия
    city = "ЕКАТЕРИНБУРГ · В НАЛИЧИИ"
    size_city = w * 0.036
    while size_city > w * 0.022:
        f_city = f(FB, size_city)
        if d.textlength(spaced(city), font=f_city) <= w - pad * 3.4:
            break
        size_city *= 0.94
    tw = d.textlength(spaced(city), font=f_city)
    d.rounded_rectangle([pad, pad, pad + tw + pad * 0.9, pad + f_city.size * 2.0],
                        radius=int(f_city.size * 0.9), fill=(10, 13, 20, 165))
    d.text((pad + pad * 0.45, pad + f_city.size * 0.5), spaced(city), font=f_city, fill=WHITE)

    top_limit = pad + f_city.size * 2.4        # ниже плашки города

    # ── низ: кнопка, подпись, оффер — считаем снизу вверх
    f_cta = f(FB, w * 0.05)
    bh = int(h * (0.085 if h > w else 0.13))
    by = h - bh - pad
    d.rounded_rectangle([pad, by, w - pad, by + bh], radius=int(bh * 0.3), fill=ACCENT)
    ctw = d.textlength(c["cta"], font=f_cta)
    d.text(((w - ctw) / 2, by + (bh - f_cta.size) / 2 - f_cta.size * 0.08),
           c["cta"], font=f_cta, fill=WHITE)

    # подбираем кегли так, чтобы весь блок уместился под плашкой города
    k = 1.0
    for _ in range(14):
        f_sub = f(FR, w * 0.045 * k)
        f_big = f(FB, w * (0.155 if h >= w else 0.125) * k)
        f_top = f(FB, w * 0.042 * k)
        sub_l = wrap(d, c["sub"], f_sub, w - pad * 2)
        big_l = wrap(d, c["big"], f_big, w - pad * 2)
        block = (len(sub_l) * f_sub.size * 1.35 + len(big_l) * f_big.size * 1.06
                 + f_big.size * 0.35 + h * 0.022 + f_top.size * 1.5)
        if by - block > top_limit:
            break
        k -= 0.06

    y = by - int(f_sub.size * 1.5)
    for line in reversed(sub_l):
        d.text((pad, y), line, font=f_sub, fill=SOFT)
        y -= int(f_sub.size * 1.35)

    y -= int(f_big.size * 0.3)
    for line in reversed(big_l):
        y -= int(f_big.size * 1.06)
        d.text((pad, y), line, font=f_big, fill=WHITE)

    # красная черта над оффером — акцент и разделитель
    y -= int(h * 0.022)
    d.rounded_rectangle([pad, y, pad + int(w * 0.13), y + max(3, int(h * 0.007))],
                        radius=2, fill=ACCENT)

    # ── надзаголовок над чертой
    y -= int(f_top.size * 1.5)
    d.text((pad, y), c["top"], font=f_top, fill=WHITE)

    return im.convert("RGB")


# Форматы Авито Рекламы
SIZES = {"400x300": (400, 300), "300x300": (300, 300),
         "300x600": (300, 600), "300x900": (300, 900)}

# Форматы Яндекс.Директа: квадрат и широкий для РСЯ, плюс запас под ретину
SIZES_DIRECT = {"1080x1080": (1080, 1080), "1080x607": (1080, 607),
                "1256x300": (1256, 300)}

# Цены «от» — реальные минимумы каталога, пересчитываются вместе с прайсом
CREATIVES = [
    {"file": "dvigateli", "cat": "двс",
     "top": "ДВИГАТЕЛИ НА ИНОМАРКИ", "big": "от 27 000 ₽",
     "sub": "609 моторов · пробег указан · гарантия",
     "cta": "Смотреть каталог"},
    {"file": "akpp", "cat": "акпп",
     "top": "АКПП · ВАРИАТОРЫ · DSG", "big": "от 19 000 ₽",
     "sub": "467 коробок · проверены перед отправкой",
     "cta": "Подобрать коробку"},
    {"file": "katalog", "cat": "двс",
     "top": "ДВИГАТЕЛИ И КОРОБКИ", "big": "1 182 в наличии",
     "sub": "Подберём по VIN за 15 минут · гарантия · доставка",
     "cta": "Смотреть каталог"},
    {"file": "ustanovka", "cat": "акпп",
     "top": "ДВИГАТЕЛЬ С УСТАНОВКОЙ", "big": "от 27 000 ₽",
     "sub": "Привезём и поставим в Екатеринбурге · гарантия на работу",
     "cta": "Смотреть каталог"},
]


def photos_for(cat, items, used, count=12):
    """Набор фото одной категории — для коллажа."""
    out = []
    for it in items:
        if it["n"] != cat or not it["f"] or it["ph"] in used:
            continue
        p = f'photos/avito/{it["ph"]}_1.jpg'
        if os.path.exists(p):
            used.add(it["ph"])
            out.append(p)
        if len(out) >= count:
            break
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    items = json.load(open("data/parts.json", encoding="utf-8"))["items"]
    used, made = set(), 0
    for c in CREATIVES:
        photo = photos_for(c["cat"], items, used)
        for name, size in SIZES.items():
            build(size, c, photo).save(os.path.join(OUT, f'{c["file"]}_{name}.jpg'),
                                       quality=90, optimize=True)
            made += 1
    print("баннеров:", made)
