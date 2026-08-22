# -*- coding: utf-8 -*-
"""Фото для Авито: та же обработка, но БЕЗ телефона и водяного знака —
площадка запрещает контакты и посторонние надписи на изображениях.

Запуск:  ./venv/bin/python process_avito_photos.py
"""
import json, os, time
from concurrent.futures import ProcessPoolExecutor
from describe import file_stem
import photo_tools

SRC = "photos/orig"
OUT = "photos/avito"
SIDE, QUALITY = 1200, 82     # Авито любит крупные снимки
WORKERS = 8
MAX_PHOTOS = 5


def build_jobs():
    src_by_art = {}
    with open("articles.csv", encoding="utf-8") as f:
        next(f)
        for line in f:
            art, invnn = line.split(";", 2)[:2]
            src_by_art[art] = invnn
    d = json.load(open("data/parts.json", encoding="utf-8"))
    jobs = []
    for it in d["items"]:
        invnn = src_by_art.get(it["a"])
        if not invnn:
            continue
        stem = file_stem(it["a"])
        for n in range(1, min(it["f"], MAX_PHOTOS) + 1):
            src = os.path.join(SRC, f"{invnn.zfill(8)}_{n}.jpg")
            if os.path.exists(src):
                jobs.append((src, f"{stem}_{n}.jpg"))
    return jobs


def one(job):
    src, name = job
    out = os.path.join(OUT, name)
    if os.path.exists(out):
        return 0
    try:
        im = photo_tools.process(src, size=SIDE, watermark=None)   # без знака и плашки
        im.save(out, quality=QUALITY, optimize=True)
        return os.path.getsize(out)
    except Exception as e:
        print("  ошибка:", name, type(e).__name__, e, flush=True)
        return 0


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    jobs = build_jobs()
    print(f"фото для Авито: {len(jobs)}", flush=True)
    start, done, total = time.time(), 0, 0
    with ProcessPoolExecutor(WORKERS) as pool:
        for size in pool.map(one, jobs, chunksize=20):
            done += 1
            total += size
            if done % 500 == 0 or done == len(jobs):
                el = time.time() - start
                sp = done / el if el else 0
                print(f"{done}/{len(jobs)} · {sp:.0f} фото/с · "
                      f"осталось ~{(len(jobs)-done)/sp/60:.1f} мин · {total/1048576:.0f} МБ", flush=True)
    print(f"\nГОТОВО за {(time.time()-start)/60:.1f} мин, {total/1048576:.0f} МБ", flush=True)
