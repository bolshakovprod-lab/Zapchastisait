# -*- coding: utf-8 -*-
"""Обрабатывает скачанные фото: обрезка, поворот, контраст, водяной знак.
Складывает в photos/big (900 px) и photos/thumb (320 px) под нашими именами.
Можно прерывать и запускать снова — готовые файлы пропускаются.

Запуск:  ./venv/bin/python process_photos.py
"""
import json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
from photo_tools import process

SRC = "photos/orig"
BIG, THUMB = "photos/big", "photos/thumb"
Q_BIG, Q_THUMB = 74, 70
BIG_SIDE, THUMB_SIDE = 900, 320
MAX_PHOTOS = 5      # больше пяти снимков на позицию покупателю не нужно,
                    # а весь сайт должен уместиться в лимит GitHub Pages (1 ГБ)
WORKERS = 8


from describe import file_stem

def build_jobs():
    """Соответствие «наш артикул -> номер файла у поставщика» берём из articles.csv."""
    src_by_art = {}
    with open("articles.csv", encoding="utf-8") as f:
        next(f)
        for line in f:
            art, invnn, _ = line.split(";", 2)
            src_by_art[art] = invnn
    d = json.load(open("data/parts.json", encoding="utf-8"))
    jobs = []
    for it in d["items"]:
        invnn = src_by_art.get(it["a"])
        if not invnn:
            continue
        stem = file_stem(it["a"])
        for n in range(1, min(it["f"], MAX_PHOTOS) + 1):
            src = os.path.join(SRC, f'{invnn.zfill(8)}_{n}.jpg')
            if os.path.exists(src):
                jobs.append((src, f"{stem}_{n}.jpg"))
    return jobs


def one(job):
    src, name = job
    big_path = os.path.join(BIG, name)
    thumb_path = os.path.join(THUMB, name)
    if os.path.exists(big_path) and os.path.exists(thumb_path):
        return 0, 0
    try:
        im = process(src, size=BIG_SIDE, watermark="bar")
        im.save(big_path, quality=Q_BIG, optimize=True)
        th = im.copy()
        th.thumbnail((THUMB_SIDE, THUMB_SIDE), 1)   # LANCZOS
        th.save(thumb_path, quality=Q_THUMB, optimize=True)
        return os.path.getsize(big_path), os.path.getsize(thumb_path)
    except Exception as e:
        print("  ошибка:", name, type(e).__name__, e, flush=True)
        return 0, 0


if __name__ == "__main__":
    os.makedirs(BIG, exist_ok=True)
    os.makedirs(THUMB, exist_ok=True)
    jobs = build_jobs()
    print(f"фото к обработке: {len(jobs)}", flush=True)
    start = time.time()
    big_b = th_b = done = 0
    with ProcessPoolExecutor(WORKERS) as pool:
        for b, t in pool.map(one, jobs, chunksize=20):
            done += 1
            big_b += b
            th_b += t
            if done % 500 == 0 or done == len(jobs):
                el = time.time() - start
                sp = done / el if el else 0
                print(f"{done}/{len(jobs)} · {sp:.0f} фото/с · "
                      f"осталось ~{(len(jobs)-done)/sp/60:.1f} мин · "
                      f"крупные {big_b/1048576:.0f} МБ · превью {th_b/1048576:.0f} МБ", flush=True)
    print(f"\nГОТОВО за {(time.time()-start)/60:.1f} мин: "
          f"крупные {big_b/1073741824:.2f} ГБ, превью {th_b/1048576:.0f} МБ", flush=True)
