# -*- coding: utf-8 -*-
"""Собирает статические страницы для поисковиков: товары, категории, марки,
sitemap.xml и robots.txt. Запускается после build.py.

Запуск:  ./venv/bin/python seo_build.py
"""
import json, os, re, shutil, html
from seo_lib import (CAT_SEO, translit, brand_slug, part_url, cat_url, brand_url,
                     money, car_line, part_title, part_description,
                     cat_title, cat_description)

SITE = os.environ.get("SITE_URL", "https://dvigatel-ekb.ru")
PER_PAGE = 48
MIN_FOR_PAGE = 3          # не плодим пустые страницы

cfg = open("config.js", encoding="utf-8").read()
def cfg_val(key, default=""):
    m = re.search(key + r':\s*"([^"]*)"', cfg)
    return m.group(1) if m else default

SHOP = cfg_val("name", "Двигатели и КПП")
CITY = cfg_val("city", "Екатеринбурге")
CITY_IN = "Екатеринбурге" if CITY == "Екатеринбург" else CITY
PHONE = cfg_val("phone")
PHONE_TEL = cfg_val("phoneTel")
WA = cfg_val("whatsapp")
TELEGRAM = cfg_val("telegram")
HOURS = cfg_val("hours")
ADDRESS = cfg_val("address", "")

d = json.load(open("data/parts.json", encoding="utf-8"))
ITEMS = d["items"]

def brands_of(it):
    return it.get("bs") or [it["b"]]


def models_of(it):
    return it.get("ms") or ([it["m"]] if it["m"] else [])


# сколько позиций в каждом разрезе — по ним решаем, какие страницы создавать
PAIRS, TRIPLES, BRANDS = {}, {}, {}
for _it in ITEMS:
    for _b in brands_of(_it):
        BRANDS[_b] = BRANDS.get(_b, 0) + 1
        PAIRS[(_it["n"], _b)] = PAIRS.get((_it["n"], _b), 0) + 1
        for _m in models_of(_it):
            TRIPLES[(_it["n"], _b, _m)] = TRIPLES.get((_it["n"], _b, _m), 0) + 1


def has_pair(cat, brand):
    return PAIRS.get((cat, brand), 0) >= MIN_FOR_PAGE


def has_triple(cat, brand, model):
    return TRIPLES.get((cat, brand, model), 0) >= MIN_FOR_PAGE


def tiles(items, title=None):
    """Плитки-ссылки: название и количество. Заменяют строку ссылок через точку."""
    if not items:
        return ""
    cells = "".join(
        f'<a class="tile" href="../{url}"><span class="tile-n">{E(name)}</span>'
        f'<span class="tile-c">{count}</span></a>'
        for name, url, count in items)
    head = f'<h2 class="tiles-h">{E(title)}</h2>' if title else ""
    return f'{head}<div class="tiles">{cells}</div>'
E = lambda s: html.escape(str(s or ""), quote=True)


def head(title, desc, url, image=None, extra=""):
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{url}">
<meta property="og:type" content="{'product' if url.startswith('p/') else 'website'}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{url}">
<meta property="og:site_name" content="{E(SHOP)}">
<meta property="og:locale" content="ru_RU">
{f'<meta property="og:image" content="{SITE}/{image}">' if image else ''}
<meta name="theme-color" content="#161a23">
<link rel="icon" href="{'../' if '/' in url else ''}favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{'../' if '/' in url else ''}apple-touch-icon.png">
<link rel="stylesheet" href="{'../' if '/' in url else ''}styles.css">
{extra}
</head>
<body>"""


def header(depth, active=None):
    up = "../" * depth
    menu = "".join(
        f'<a class="nav-item{" on" if k == active else ""}" href="{up}{cat_url(k)}">{E(v["short"])}</a>'
        for k, v in CAT_SEO.items())
    return f"""<header class="top">
  <div class="wrap top-in">
    <a class="logo" href="{up}"><img class="logo-mark" src="{up}logo.png" alt="{E(SHOP)}" width="34" height="34"><span class="logo-text">{E(SHOP)}</span></a>
    <div class="top-contacts">
      <a class="phone" href="tel:{E(PHONE_TEL)}">{E(PHONE)}</a>
      {f'<a class="btn-wa" href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp</a>' if WA else ''}
    </div>
  </div>
</header>
<nav class="subnav" aria-label="Разделы каталога">
  <div class="wrap subnav-in">
    <a class="nav-item" href="{up}">Весь каталог</a>
    {menu}
    <a class="nav-item" href="{up}service.html">Установка</a>
  </div>
</nav>"""


def footer(depth, links=""):
    up = "../" * depth
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <p><b>{E(SHOP)}</b> · {E(CITY)} · <a href="tel:{E(PHONE_TEL)}">{E(PHONE)}</a></p>
      <p class="muted">{E(HOURS)}</p>
      <p class="muted"><a href="{up}service.html">Установочный центр</a> ·
      <a href="{up}privacy.html">Политика конфиденциальности</a> ·
      <a href="{up}terms.html">Условия продажи</a> · <a href="{up}">Каталог</a></p>
    </div>
    <div class="muted">{links}</div>
  </div>
</footer>
<script src="{up}config.js"></script>
<script src="{up}analytics.js"></script>
<script src="{up}chat.js"></script>
<script src="{up}form.js"></script>
</body>
</html>"""


def crumbs(depth, chain):
    """chain: [(название, url или None)]"""
    up = "../" * depth
    parts, ld = [], []
    for n, (name, url) in enumerate(chain, 1):
        if url:
            parts.append(f'<a href="{up}{url}">{E(name)}</a>')
        else:
            parts.append(f'<span>{E(name)}</span>')
        ld.append({"@type": "ListItem", "position": n, "name": name,
                   **({"item": f"{SITE}/{url}"} if url else {})})
    schema = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                         "itemListElement": ld}, ensure_ascii=False)
    return (f'<nav class="crumbs">{" › ".join(parts)}</nav>'
            f'<script type="application/ld+json">{schema}</script>')


def card(it, depth):
    up = "../" * depth
    url = up + part_url(it)
    img = f'{up}photos/thumb/{it["ph"]}_1.jpg' if it["f"] else ""
    tags = []
    if it["kind"]:
        tags.append(f'<span class="tag">{E(it["kind"])}</span>')
    if it["km"]:
        tags.append(f'<span class="tag km">{it["km"] * 1000:,}'.replace(",", " ") + ' км</span>')
    return f"""<a class="card" href="{url}">
  <div class="thumb">{f'<img loading="lazy" src="{img}" alt="{E(it["ti"])} — фото">' if img else '<span class="nophoto">без фото</span>'}
    {f'<div class="tags">{"".join(tags)}</div>' if tags else ''}</div>
  <div class="card-b">
    <div class="card-title">{E(it["ti"])}</div>
    <div class="card-car">{E((it["t"].split(" — ")[1:] or [""])[0].rstrip("."))}</div>
    <div class="card-price">{money(it["p"])}</div>
  </div>
</a>"""


def part_page(it):
    url = part_url(it)
    title = part_title(it, CITY_IN)
    desc = part_description(it, CITY_IN, PHONE)
    shots = [f'photos/big/{it["ph"]}_{n}.jpg' for n in range(1, it["f"] + 1)]
    cat = CAT_SEO.get(it["n"], {})

    product = {
        "@context": "https://schema.org", "@type": "Product",
        "name": it["ti"], "description": it["t"], "sku": it["a"],
        "brand": {"@type": "Brand", "name": it["b"]},
        "itemCondition": "https://schema.org/UsedCondition",
        "image": [f"{SITE}/{s}" for s in shots[:3]],
    }
    if it["o"]:
        product["mpn"] = it["o"].split(",")[0].strip()
    if it["p"]:
        product["offers"] = {
            "@type": "Offer", "price": it["p"], "priceCurrency": "RUB",
            "availability": "https://schema.org/InStock",
            "url": f"{SITE}/{url}",
            "itemCondition": "https://schema.org/UsedCondition",
            "seller": {"@type": "Organization", "name": SHOP},
        }
    ld = f'<script type="application/ld+json">{json.dumps(product, ensure_ascii=False)}</script>'

    rows = [("Марка", it["b"]), ("Модель", it["m"]), ("Кузов", it["k"]),
            ("Двигатель", it["e"]), ("Пробег", f'{it["km"] * 1000:,}'.replace(",", " ") + " км" if it["km"] else ""),
            ("Тип", it["kind"]), ("Год", it["y"]), ("Номер детали", it["d"]),
            ("OEM-номера", it["o"]), ("Состояние", it["c"]), ("Артикул", it["a"])]
    table = "".join(f"<tr><td>{E(k)}</td><td>{E(v)}</td></tr>" for k, v in rows if v)

    msg = (f'Здравствуйте! Интересует {it["ti"]}, артикул {it["a"]}, {money(it["p"])}. В наличии?')
    wa = f'https://wa.me/{WA}?text={msg.replace(" ", "%20")}' if WA else ""
    tg = f'https://t.me/{TELEGRAM}' if TELEGRAM else ""

    similar = [x for x in ITEMS if x["n"] == it["n"] and x["b"] == it["b"] and x["a"] != it["a"]][:4]

    gallery = ""
    if shots:
        gallery = f"""<img class="gal-main" id="galMain" src="../{shots[0]}" alt="{E(it["ti"])} — фото агрегата">
      <div class="gal-strip">{"".join(f'<img src="../photos/thumb/{it["ph"]}_{n+1}.jpg" data-u="../{s}" class="{"on" if n==0 else ""}" alt="{E(it["ti"])} — фото {n+1}" onerror="this.remove()">' for n, s in enumerate(shots))}</div>"""

    body = f"""{header(1)}
<main class="wrap doc part">
  {crumbs(1, [("Главная", ""), (cat.get("many", "Каталог"), cat_url(it["n"]))]
             + ([(f'{cat.get("many", "")} {it["b"].title()}', cat_url(it["n"], it["b"]))]
                if has_pair(it["n"], it["b"]) else [])
             + [(it["ti"], None)])}
  <div class="m-top">
    <div>{gallery or '<div class="gal-main" style="display:grid;place-items:center;color:var(--muted)">Фото нет</div>'}</div>
    <div>
      <h1 class="m-title">{E(it["ti"])}</h1>
      <div class="m-tags">
        <span class="tag">{E(it["c"])}</span>
        {f'<span class="tag">{E(it["kind"])}</span>' if it["kind"] else ''}
        {f'<span class="tag">пробег {it["km"] * 1000:,} км</span>'.replace(",", " ") if it["km"] else ''}
        <span class="tag">арт. {E(it["a"])}</span>
      </div>
      <div class="m-price">{money(it["p"])}</div>
      <p class="m-desc">{E(it["t"])}</p>
      {f'<p class="m-note-warn">Комплектация: {E(it["note"])}</p>' if it["note"] else ''}
      <table class="specs">{table}</table>
      <div class="cta">
        <a class="call" href="tel:{E(PHONE_TEL)}">Позвонить {E(PHONE)}</a>
        {f'<a class="wa" href="{wa}" target="_blank" rel="noopener">Написать в WhatsApp</a>' if wa else ''}
        {f'<a class="tg" href="{tg}" target="_blank" rel="noopener">Telegram</a>' if tg else ''}
      </div>
      <div class="m-guarantee">
        <span>Гарантия на проверку и установку · бесплатная доставка до транспортной компании ·
        отправим фото и видео агрегата до оплаты</span>
      </div>
    </div>
  </div>

  <section class="seo-text">
    <h2>{E(it["ti"])} — что важно знать</h2>
    <p>Агрегат снят с автомобиля {E(car_line(it))}{f', пробег {it["km"] * 1000:,} км'.replace(",", " ") if it["km"] else ""}.
    {'Двигатель ' + E(it["e"]) + '. ' if it["e"] else ''}
    {'Номер детали ' + E(it["d"]) + '. ' if it["d"] else ''}
    {'Подходящие OEM-номера: ' + E(it["o"]) + '. ' if it["o"] else ''}</p>
    <p>Перед отправкой агрегат проверяем и фотографируем. Пришлём фотографии и видео работы
    именно этого экземпляра, поможем проверить совместимость по VIN вашего автомобиля.
    Отправка из {E(CITY_IN)} до транспортной компании — бесплатно, дальше — любой ТК до вашего города.</p>
  </section>

  {help_block(f'{cat.get("one", "агрегат")} {it["b"].title()} {it["m"]}'.strip())}

  {f'''<section class="similar">
    <h2>Похожие агрегаты {E(it["b"].title())}</h2>
    <div class="grid">{"".join(card(x, 1) for x in similar)}</div>
    <p><a class="more-link" href="../{cat_url(it["n"], it["b"]) if has_pair(it["n"], it["b"]) else cat_url(it["n"])}">Все {E(cat.get("many", "").lower())} {E(it["b"].title()) if has_pair(it["n"], it["b"]) else ""} →</a></p>
  </section>''' if similar else ''}
</main>
<script>
document.querySelectorAll('.gal-strip img').forEach(t => t.onclick = () => {{
  document.getElementById('galMain').src = t.dataset.u;
  document.querySelectorAll('.gal-strip img').forEach(i => i.classList.toggle('on', i === t));
}});
</script>
{footer(1)}"""
    return head(title, desc, url, shots[0] if shots else None, ld) + body


def help_block(what="агрегат"):
    """Главный призыв: не «купить», а «спросить». Продаёт консультация."""
    wa = f'https://wa.me/{WA}?text=Здравствуйте!%20Помогите%20подобрать%20{what}' if WA else ""
    return f"""<section class="help">
  <div class="help-in">
    <div>
      <h2>Не нашли свой {E(what)}?</h2>
      <p>Пришлите VIN или марку с моделью — проверим по складу и подберём то,
      что точно встанет на вашу машину. Ответим и подскажем, даже если у нас этого нет.</p>
    </div>
    <div class="help-cta">
      <a class="call" href="tel:{E(PHONE_TEL)}">Позвонить {E(PHONE)}</a>
      {f'<a class="wa" href="{wa}" target="_blank" rel="noopener">Спросить в WhatsApp</a>' if wa else ''}
    </div>
  </div>
</section>"""


def listing_page(items, url, title, desc, h1, intro, chain, nav_html="",
                 pages=None, page=1, what="агрегат", active=None):
    """Страница списка: категория, марка, модель."""
    cards = "".join(card(it, 1) for it in items)
    pager = ""
    if pages and len(pages) > 1:
        links = "".join(
            f'<span class="pg on">{n}</span>' if n == page
            else f'<a class="pg" href="../{u}">{n}</a>'
            for n, u in enumerate(pages, 1))
        pager = f'<div class="pager">{links}</div>'

    ld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": n,
             "url": f"{SITE}/{part_url(it)}", "name": it["ti"]}
            for n, it in enumerate(items[:20], 1)]
    }, ensure_ascii=False)

    return head(title, desc, url, extra=f'<script type="application/ld+json">{ld}</script>') + f"""{header(1, active)}
<main class="wrap doc">
  {crumbs(1, chain)}
  <h1>{E(h1)}</h1>
  {intro}
  {nav_html}
  <div class="grid">{cards}</div>
  {pager}
  {help_block(what)}
</main>
{footer(1)}"""


def build_listings():
    made = []
    by_cat = {}
    for it in ITEMS:
        by_cat.setdefault(it["n"], []).append(it)

    for cat, rows in by_cat.items():
        c = CAT_SEO[cat]
        one = c["one"]

        # какие марки есть в этой категории
        brands = sorted({b for it in rows for b in brands_of(it)})
        brand_tiles = tiles(
            [(b.title(), cat_url(cat, b), PAIRS[(cat, b)])
             for b in brands if has_pair(cat, b)],
            "Выберите марку")

        # ── страница категории (с пагинацией)
        chunks = [rows[i:i + PER_PAGE] for i in range(0, len(rows), PER_PAGE)] or [[]]
        urls = [cat_url(cat, page=n) for n in range(1, len(chunks) + 1)]
        for n, (chunk, u) in enumerate(zip(chunks, urls), 1):
            intro = (f'<p class="lead">{E(c["many"])} в наличии в {E(CITY_IN)} — {len(rows)} позиций '
                     f'с фотографиями, ценами и пробегом. Проверяем перед отправкой, отправляем фото '
                     f'и видео до оплаты, помогаем подобрать по VIN.</p>') if n == 1 else ""
            made.append((u, listing_page(
                chunk, u,
                cat_title(cat, None, CITY_IN, len(rows)) + (f" — страница {n}" if n > 1 else ""),
                cat_description(cat, None, CITY_IN, len(rows), PHONE),
                c["many"] + (f" — страница {n}" if n > 1 else ""),
                intro, [("Главная", ""), (c["many"], None)],
                brand_tiles if n == 1 else "", urls, n, one, cat)))

        # ── категория + марка, с плиткой моделей
        for b in brands:
            if not has_pair(cat, b):
                continue
            rows_b = [it for it in rows if b in brands_of(it)]
            models = sorted({m for it in rows_b for m in models_of(it)})
            model_tiles = tiles(
                [(m, cat_url(cat, b, m), TRIPLES[(cat, b, m)])
                 for m in models if has_triple(cat, b, m)],
                "Выберите модель")
            u = cat_url(cat, b)
            intro = (f'<p class="lead">{E(c["many"])} для {E(b.title())} — {len(rows_b)} шт. в наличии '
                     f'в {E(CITY_IN)}. Гарантия, доставка по России, бесплатный подбор по VIN.</p>')
            made.append((u, listing_page(
                rows_b[:PER_PAGE], u, cat_title(cat, b, CITY_IN, len(rows_b)),
                cat_description(cat, b, CITY_IN, len(rows_b), PHONE),
                f'{c["many"]} {b.title()}', intro,
                [("Главная", ""), (c["many"], cat_url(cat)), (b.title(), None)],
                model_tiles, what=f'{one} {b.title()}', active=cat)))

            # ── категория + марка + модель
            for m in models:
                if not has_triple(cat, b, m):
                    continue
                rows_m = [it for it in rows_b if m in models_of(it)]
                um = cat_url(cat, b, m)
                name = f'{b.title()} {m}'
                intro_m = (f'<p class="lead">{E(c["many"])} для {E(name)} — {len(rows_m)} шт. в наличии. '
                           f'В карточке указаны пробег, номер агрегата и OEM-номера: '
                           f'сверьте со своим или пришлите VIN, проверим за вас.</p>')
                made.append((um, listing_page(
                    rows_m, um,
                    f'{c["many"]} {name} — купить бу в {CITY_IN}, {len(rows_m)} в наличии',
                    f'{c["many"]} для {name} в наличии в {CITY_IN}: {len(rows_m)} шт. с фото, '
                    f'ценами и пробегом. Гарантия, доставка по России, подбор по VIN. Тел. {PHONE}',
                    f'{c["many"]} {name}', intro_m,
                    [("Главная", ""), (c["many"], cat_url(cat)),
                     (b.title(), cat_url(cat, b)), (m, None)],
                    what=f'{one} {name}', active=cat)))

    # ── страницы марок целиком
    for b, total in BRANDS.items():
        if total < MIN_FOR_PAGE:
            continue
        rows_b = [it for it in ITEMS if b in brands_of(it)]
        u = brand_url(b)
        cat_tiles = tiles(
            [(CAT_SEO[c]["many"], cat_url(c, b), PAIRS[(c, b)])
             for c in sorted({x["n"] for x in rows_b}) if has_pair(c, b)],
            "Что есть для этой марки")
        models = sorted({m for it in rows_b for m in models_of(it)})
        model_counts = {}
        for it in rows_b:
            for m in models_of(it):
                model_counts[m] = model_counts.get(m, 0) + 1
        model_tiles = tiles(
            [(m, cat_url(rows_b[0]["n"], b, m) if has_triple(rows_b[0]["n"], b, m)
              else cat_url(next(c for c in ("двс", "акпп", "мкпп", "раздаточная коробка")
                                if has_triple(c, b, m)), b, m), model_counts[m])
             for m in models
             if any(has_triple(c, b, m) for c in ("двс", "акпп", "мкпп", "раздаточная коробка"))],
            "Модели")
        intro = (f'<p class="lead">Контрактные двигатели и коробки передач {E(b.title())} — '
                 f'{total} агрегатов в наличии в {E(CITY_IN)}: с фото, ценами и пробегом.</p>')
        made.append((u, listing_page(
            rows_b[:PER_PAGE], u,
            f'Контрактные двигатели и КПП {b.title()} — купить бу в {CITY_IN}, {total} в наличии',
            f'Контрактные двигатели, АКПП и МКПП {b.title()} в наличии в {CITY_IN}: {total} агрегатов '
            f'с фото и ценами. Гарантия, доставка по России, подбор по VIN. Тел. {PHONE}',
            f'Двигатели и коробки {b.title()}', intro,
            [("Главная", ""), (b.title(), None)],
            cat_tiles + model_tiles, what=f'агрегат на {b.title()}')))
    return made


def sitemap(urls):
    body = "".join(
        f"<url><loc>{SITE}/{u}</loc><changefreq>weekly</changefreq>"
        f"<priority>{pri}</priority></url>"
        for u, pri in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace("www.sitemap.org", "www.sitemaps.org")
            + body + "</urlset>")


def fill_legal_pages():
    """Вписывает реквизиты прямо в HTML правовых страниц.
    Раньше их подставлял скрипт — без JS документы выглядели пустыми."""
    values = {
        "entity": cfg_val("entity"), "inn": cfg_val("inn"), "ogrn": cfg_val("ogrn"),
        "address": cfg_val("address"), "email": cfg_val("email"),
        "updated": cfg_val("updated", "").split("//")[0].strip(),
        "phone": PHONE, "hours": HOURS,
    }
    for name in ("privacy.html", "terms.html"):
        html_text = open(name, encoding="utf-8").read()
        for key, val in values.items():
            html_text = re.sub(
                rf'(<(\w+) data-legal="{key}">)[^<]*(</\2>)',
                lambda m, v=val: m.group(1) + E(v or "——————") + m.group(3),
                html_text)
        open(name, "w", encoding="utf-8").write(html_text)
    print("реквизиты вписаны в privacy.html и terms.html")


if __name__ == "__main__":
    for folder in ("p", "k", "m"):
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)

    urls = [("", "1.0")]
    for it in ITEMS:
        u = part_url(it)
        open(u, "w", encoding="utf-8").write(part_page(it))
        urls.append((u, "0.8"))
    print(f"страниц товаров: {len(ITEMS)}")

    fill_legal_pages()

    listings = build_listings()
    for u, html_text in listings:
        open(u, "w", encoding="utf-8").write(html_text)
    print(f"страниц категорий и марок: {len(listings)}")

    urls += [(u, "0.6") for u, _ in listings]
    urls += [("service.html", "0.9"), ("privacy.html", "0.2"), ("terms.html", "0.3")]
    open("sitemap.xml", "w", encoding="utf-8").write(sitemap(urls))
    open("robots.txt", "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /photos/orig/\n\n"
        f"Sitemap: {SITE}/sitemap.xml\n")

    # страница на случай неверного адреса
    open("404.html", "w", encoding="utf-8").write(
        head("Страница не найдена", "Такой страницы нет — вернитесь в каталог агрегатов.",
             "404.html")
        + header(0)
        + f"""<main class="wrap doc">
  <h1>Такой страницы нет</h1>
  <p class="lead">Возможно, агрегат уже продан или адрес набран с ошибкой.
  Посмотрите каталог — в наличии {len(ITEMS)} двигателей и коробок.</p>
  <nav class="cat-links">
    <a href="/">Весь каталог</a>
    <a href="/k/dvigateli.html">Двигатели</a>
    <a href="/k/akpp.html">АКПП</a>
    <a href="/k/mkpp.html">МКПП</a>
    <a href="/k/razdatki.html">Раздатки</a>
  </nav>
  <p class="muted">Или позвоните: <a href="tel:{PHONE_TEL}">{PHONE}</a> — подберём по VIN.</p>
</main>"""
        + footer(0))
    print(f"адресов в sitemap.xml: {len(urls)}")
