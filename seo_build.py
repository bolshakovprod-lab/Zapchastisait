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
HOURS = cfg_val("hours")
ADDRESS = cfg_val("address", "")

d = json.load(open("data/parts.json", encoding="utf-8"))
ITEMS = d["items"]

# для каких пар «категория + марка» страница вообще создаётся
PAIRS = {}
for _it in ITEMS:
    PAIRS[(_it["n"], _it["b"])] = PAIRS.get((_it["n"], _it["b"]), 0) + 1


def has_pair(cat, brand):
    return PAIRS.get((cat, brand), 0) >= MIN_FOR_PAGE
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
<link rel="stylesheet" href="{'../' if '/' in url else ''}styles.css">
{extra}
</head>
<body>"""


def header(depth):
    up = "../" * depth
    return f"""<header class="top">
  <div class="wrap top-in">
    <a class="logo" href="{up}"><span class="logo-mark">ДК</span><span class="logo-text">{E(SHOP)}</span></a>
    <div class="top-contacts">
      <a class="phone" href="tel:{E(PHONE_TEL)}">{E(PHONE)}</a>
      {f'<a class="btn-wa" href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp</a>' if WA else ''}
    </div>
  </div>
</header>"""


def footer(depth, links=""):
    up = "../" * depth
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <div>
      <p><b>{E(SHOP)}</b> · {E(CITY)} · <a href="tel:{E(PHONE_TEL)}">{E(PHONE)}</a></p>
      <p class="muted">{E(HOURS)}</p>
      <p class="muted"><a href="{up}privacy.html">Политика конфиденциальности</a> ·
      <a href="{up}terms.html">Условия продажи</a> · <a href="{up}">Каталог</a></p>
    </div>
    <div class="muted">{links}</div>
  </div>
</footer>
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


def listing_page(items, url, title, desc, h1, intro, chain, pages=None, page=1):
    """Страница списка: категория, категория+марка или марка."""
    cards = "".join(card(it, 1) for it in items)
    nav = ""
    if pages and len(pages) > 1:
        links = "".join(
            f'<span class="pg on">{n}</span>' if n == page
            else f'<a class="pg" href="../{u}">{n}</a>'
            for n, u in enumerate(pages, 1))
        nav = f'<div class="pager">{links}</div>'

    ld = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": n,
             "url": f"{SITE}/{part_url(it)}", "name": it["ti"]}
            for n, it in enumerate(items[:20], 1)]
    }, ensure_ascii=False)

    return head(title, desc, url, extra=f'<script type="application/ld+json">{ld}</script>') + f"""{header(1)}
<main class="wrap doc">
  {crumbs(1, chain)}
  <h1>{E(h1)}</h1>
  {intro}
  <div class="grid">{cards}</div>
  {nav}
</main>
{footer(1)}"""


def build_listings():
    made = []
    by_cat = {}
    by_brand = {}
    for it in ITEMS:
        by_cat.setdefault(it["n"], []).append(it)
        by_brand.setdefault(it["b"], []).append(it)

    # категории и связки «категория + марка»
    for cat, rows in by_cat.items():
        c = CAT_SEO[cat]
        chunks = [rows[i:i + PER_PAGE] for i in range(0, len(rows), PER_PAGE)] or [[]]
        urls = [cat_url(cat, page=n) for n in range(1, len(chunks) + 1)]
        brands = sorted({it["b"] for it in rows})
        brand_links = " · ".join(
            f'<a href="../{cat_url(cat, b)}">{E(b.title())}</a>'
            for b in brands if len([x for x in rows if x["b"] == b]) >= MIN_FOR_PAGE)
        for n, (chunk, u) in enumerate(zip(chunks, urls), 1):
            intro = f"""<p class="lead">{E(c["many"])} в наличии в {E(CITY_IN)} — {len(rows)} позиций
            с фотографиями, ценами и пробегом. Проверяем перед отправкой, отправляем фото и видео
            до оплаты, помогаем подобрать по VIN.</p>
            <p class="muted">Марки: {brand_links}</p>""" if n == 1 else ""
            made.append((u, listing_page(
                chunk, u,
                cat_title(cat, None, CITY_IN, len(rows)) + (f" — страница {n}" if n > 1 else ""),
                cat_description(cat, None, CITY_IN, len(rows), PHONE),
                c["many"] + (f" — страница {n}" if n > 1 else ""),
                intro, [("Главная", ""), (c["many"], None)], urls, n)))

        for b in brands:
            rows_b = [x for x in rows if x["b"] == b]
            if len(rows_b) < MIN_FOR_PAGE:
                continue
            u = cat_url(cat, b)
            models = sorted({x["m"] for x in rows_b if x["m"]})[:12]
            intro = f"""<p class="lead">{E(c["many"])} для {E(b.title())} — {len(rows_b)} шт. в наличии
            в {E(CITY_IN)}. Гарантия, доставка по России, бесплатный подбор по VIN.</p>
            <p class="muted">Модели: {E(", ".join(models))}</p>"""
            made.append((u, listing_page(
                rows_b, u, cat_title(cat, b, CITY_IN, len(rows_b)),
                cat_description(cat, b, CITY_IN, len(rows_b), PHONE),
                f'{c["many"]} {b.title()}', intro,
                [("Главная", ""), (c["many"], cat_url(cat)), (b.title(), None)])))

    # страницы марок целиком
    for b, rows in by_brand.items():
        if len(rows) < MIN_FOR_PAGE:
            continue
        u = brand_url(b)
        cats = " · ".join(f'<a href="../{cat_url(c)}">{E(CAT_SEO[c]["many"])}</a>'
                          for c in sorted({x["n"] for x in rows}))
        intro = f"""<p class="lead">Контрактные двигатели и коробки передач {E(b.title())} —
        {len(rows)} агрегатов в наличии в {E(CITY_IN)}: с фото, ценами и пробегом.</p>
        <p class="muted">Разделы: {cats}</p>"""
        made.append((u, listing_page(
            rows[:PER_PAGE], u,
            f'Контрактные двигатели и КПП {b.title()} — купить бу в {CITY_IN}, {len(rows)} в наличии',
            f'Контрактные двигатели, АКПП и МКПП {b.title()} в наличии в {CITY_IN}: {len(rows)} агрегатов '
            f'с фото и ценами. Гарантия, доставка по России, подбор по VIN. Тел. {PHONE}',
            f'Двигатели и коробки {b.title()}', intro,
            [("Главная", ""), (b.title(), None)])))
    return made


def sitemap(urls):
    body = "".join(
        f"<url><loc>{SITE}/{u}</loc><changefreq>weekly</changefreq>"
        f"<priority>{pri}</priority></url>"
        for u, pri in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace("www.sitemap.org", "www.sitemaps.org")
            + body + "</urlset>")


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

    listings = build_listings()
    for u, html_text in listings:
        open(u, "w", encoding="utf-8").write(html_text)
    print(f"страниц категорий и марок: {len(listings)}")

    urls += [(u, "0.6") for u, _ in listings]
    urls += [("privacy.html", "0.2"), ("terms.html", "0.3")]
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
