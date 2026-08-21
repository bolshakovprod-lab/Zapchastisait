# -*- coding: utf-8 -*-
"""Заливает фото на GitHub частями: одним куском в 680 МБ push обрывается."""
import os, subprocess, sys, math

CHUNK_MB = 110


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def files_of(folder):
    out = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        out.append((p, os.path.getsize(p)))
    return out


def chunks(files, limit_bytes):
    cur, size = [], 0
    for p, s in files:
        if size + s > limit_bytes and cur:
            yield cur
            cur, size = [], 0
        cur.append(p)
        size += s
    if cur:
        yield cur


todo = files_of("photos/thumb") + files_of("photos/big")
groups = list(chunks(todo, CHUNK_MB * 1024 * 1024))
print(f"файлов: {len(todo)} | частей: {len(groups)}", flush=True)

for n, group in enumerate(groups, 1):
    with open("/tmp/pathspec.txt", "w") as f:
        f.write("\n".join(group))
    r = run(["git", "add", "--pathspec-from-file=/tmp/pathspec.txt"])
    if r.returncode:
        print("add:", r.stderr[:300], flush=True)
        sys.exit(1)
    r = run(["git", "-c", "user.name=Andrey", "-c", "user.email=andrej.bolschakov2014@gmail.com",
             "commit", "-q", "-m", f"Фото агрегатов, часть {n} из {len(groups)}\n\n"
             f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"])
    if r.returncode and "nothing to commit" not in r.stdout:
        print("commit:", r.stderr[:300], flush=True)
        sys.exit(1)
    for attempt in range(3):
        r = run(["git", "push"], env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if r.returncode == 0:
            print(f"часть {n}/{len(groups)} залита ({len(group)} файлов)", flush=True)
            break
        print(f"  попытка {attempt+1} не прошла: {r.stderr.strip()[:160]}", flush=True)
    else:
        print("не удалось залить часть", n, flush=True)
        sys.exit(1)

print("ГОТОВО: все фото на GitHub", flush=True)
