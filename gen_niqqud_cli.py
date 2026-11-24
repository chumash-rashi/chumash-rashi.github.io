#!/usr/bin/env python3
"""Niqqud map for a new parsha's quiz strings -> _sef/<name>_niqqud.json. Usage: python gen_niqqud_cli.py vayishlach"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
from add_niqqud import call
name = sys.argv[1]
quiz = json.load(open(f'_sef/{name}_quiz.json', encoding='utf-8'))
cp = f'_sef/{name}_niqqud.json'
try: cache = json.load(open(cp, encoding='utf-8'))
except FileNotFoundError: cache = {}
texts = {t for o in quiz.values() for p in o['points'] for t in [p['q']] + p['options']}
todo = sorted(t for t in texts if t not in cache)
print(len(cache), 'cached', len(todo), 'todo', flush=True)
bs = [todo[i:i + 15] for i in range(0, len(todo), 15)]
with ThreadPoolExecutor(6) as pool:
    for n, (b, res) in enumerate(zip(bs, pool.map(lambda b: call(None, b), bs)), 1):
        cache.update(dict(zip(b, res))); json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False); print('batch', n, '/', len(bs), flush=True)
print('done', len(cache))
