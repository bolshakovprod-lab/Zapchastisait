# -*- coding: utf-8 -*-
"""Скачивает фото поставщика в photos/orig/. Можно прерывать и запускать снова —
уже скачанные файлы пропускаются.

Запуск:  ./venv/bin/python download_photos.py
"""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

OUT = "photos/orig"
THREADS = 8
RETRIES = 3
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"

# Адрес фотоархива поставщика лежит в supplier.py — этот файл в репозиторий не попадает.
try:
    from supplier import PHOTO_BASE
except ImportError:
    sys.exit("Нет файла supplier.py с адресом фотоархива поставщика — см. README")

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
    for n in range(1, it["f"] + 1):
        name = f"{invnn.zfill(8)}_{n}.jpg"
        jobs.append((PHOTO_BASE + name, os.path.join(OUT, name)))

os.makedirs(OUT, exist_ok=True)
todo = [(u, p) for u, p in jobs if not os.path.exists(p) or os.path.getsize(p) == 0]
print(f"всего фото: {len(jobs)} | уже есть: {len(jobs) - len(todo)} | качаем: {len(todo)}", flush=True)

done = skipped = failed = 0
bytes_got = 0
start = time.time()

def grab(job):
    """Возвращает (размер, ошибка). 404 у поставщика — обычное дело, не ошибка."""
    url, path = job
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) < 500:          # заглушка вместо фото
                return 0, None
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
            return len(data), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0, None
            if attempt == RETRIES - 1:
                return 0, f"{e.code} {url}"
        except Exception as e:
            if attempt == RETRIES - 1:
                return 0, f"{type(e).__name__} {url}"
            time.sleep(1.5 * (attempt + 1))
    return 0, "не вышло " + url

with ThreadPoolExecutor(THREADS) as pool:
    for size, err in pool.map(grab, todo):
        done += 1
        if err:
            failed += 1
            if failed <= 20:
                print("  ошибка:", err, flush=True)
        elif size:
            bytes_got += size
        else:
            skipped += 1
        if done % 250 == 0 or done == len(todo):
            el = time.time() - start
            speed = done / el if el else 0
            left = (len(todo) - done) / speed if speed else 0
            print(f"{done}/{len(todo)} · {bytes_got/1048576:.0f} МБ · "
                  f"{speed:.1f} файл/с · осталось ~{left/60:.0f} мин · "
                  f"нет фото: {skipped} · ошибок: {failed}", flush=True)

print(f"\nГОТОВО за {(time.time()-start)/60:.1f} мин: скачано {bytes_got/1073741824:.2f} ГБ, "
      f"пропущено (нет на сервере) {skipped}, ошибок {failed}", flush=True)
