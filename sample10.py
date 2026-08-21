# -*- coding: utf-8 -*-
"""10 образцов: разные категории и марки."""
import json, os, sys, random
from photo_tools import process

OUT = sys.argv[1]
d = json.load(open("data/parts.json", encoding="utf-8"))
# случайные позиции из всего каталога
pool = []
for it in d["items"]:
    if it["f"]:
        p = f'photos/orig/{str(it["i"]).zfill(8)}_1.jpg'
        if os.path.exists(p):
            pool.append((it, p))
random.shuffle(pool)
picked = pool

for n, (it, p) in enumerate(picked[:10], 1):
    out = os.path.join(OUT, f"obrabotka-{n:02d}.jpg")
    process(p).save(out, quality=86, optimize=True)
    print(f'{n:2}. {os.path.getsize(out)/1024:4.0f} КБ  {it["ti"]}')
