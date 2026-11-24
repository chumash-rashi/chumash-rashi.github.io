#!/usr/bin/env python3
"""English translations of the quiz for the language toggle -> _sef/<name>_trans/out_<n>.json
Usage: python gen_trans_cli.py vayishlach Vayishlach"""
import sys, re, json, time, os, subprocess
from concurrent.futures import ThreadPoolExecutor
name, Name = sys.argv[1], sys.argv[2]
SYSTEM = """You translate a Hebrew Chumash/Rashi quiz for children into clear, natural English. You receive a JSON array; each item has "id", "simple" (a plain-Hebrew explanation of a Rashi), and "points" (each with "q" and "options"). Return ONLY a JSON array (no code fences) of objects {"id": same id, "explanation": English translation of simple, "points": [{"q": ..., "options": [...]}]} with the same number of points and options, same order (do NOT reorder options). Keep Hebrew words that are quoted from the verse in Hebrew letters (with their vowels) inside the English sentence. Simple, accurate, child-friendly English; do not add information."""
quiz = json.load(open(f'_sef/{name}_quiz.json', encoding='utf-8'))
nik = json.load(open(f'_sef/{name}_niqqud.json', encoding='utf-8'))
v = lambda s: nik.get(s, s)
items = [{'id': k, 'simple': o['simple'], 'points': [{'q': v(p['q']), 'options': [v(x) for x in p['options']]} for p in o['points']]} for k, o in quiz.items()]
os.makedirs(f'_sef/{name}_trans', exist_ok=True)
bs = [items[i:i + 8] for i in range(0, len(items), 8)]
def call(a):
    n, b = a
    path = f'_sef/{name}_trans/out_{n}.json'
    if os.path.exists(path): return
    last = None
    for t in range(4):
        try:
            p = subprocess.run(['claude', '-p', '--model', 'sonnet', '--system-prompt', 'Follow the task in the user message exactly and output only what it asks.'], input=SYSTEM+'\n\n=== INPUT JSON ===\n'+json.dumps(b, ensure_ascii=False),
                               capture_output=True, text=True, encoding='utf-8', shell=True, timeout=600)
            assert p.returncode == 0, p.stderr[:200]
            out = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', p.stdout.strip()))
            assert [o['id'] for o in out] == [e['id'] for e in b]
            for o, e in zip(out, b):
                assert len(o['points']) == len(e['points']) and all(len(x['options']) == len(y['options']) for x, y in zip(o['points'], e['points']))
                o['id'] = Name + '|' + o['id']
            json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False); print('ok', n, flush=True); return
        except Exception as ex: last = ex; time.sleep(5 * (t + 1))
    print('FAILED', n, last, flush=True)
with ThreadPoolExecutor(6) as pool: list(pool.map(call, enumerate(bs)))
print('done')
