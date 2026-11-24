#!/usr/bin/env python3
"""Generate the Hebrew quiz for a new parsha via the `claude` CLI (no API key needed).
Usage: python gen_quiz_cli.py vayishlach   -> _sef/<name>_quiz.json  (cache: _sef/<name>_quiz_cache.json)"""
import sys, re, json, time, subprocess
from concurrent.futures import ThreadPoolExecutor
name = sys.argv[1]
src_txt = open('regen_quiz_hebrew.py', encoding='utf-8').read()
SYSTEM = re.search(r'SYSTEM = """(.*?)"""', src_txt, re.S).group(1)
SYSTEM = SYSTEM.replace('"kasha": מה הקושי', '"kp": רשימה של 1–3 ביטויים קצרים (2–8 מילים כל אחד) המועתקים אות באות מטקסט הרש״י (ללא ניקוד), שמהם נלמדת התשובה הנכונה.\n- "kasha": מה הקושי')
SYSTEM = SYSTEM.replace('"answer": "..."}]}', '"answer": "...", "kp": ["..."]}]}')
strip = lambda s: re.sub(r'[֑-ׇ]', '', s)
sk = json.load(open(f'_sef/{name}_skeleton.json', encoding='utf-8'))
src = json.load(open(f'{name}_source.json', encoding='utf-8'))
entries = []
for x in sk:
    r = src[f"{x['ch']}:{x['v']}"]['rashis'][x['n'] - 1]
    entries.append({'id': x['id'], 'pasuk': strip(src[f"{x['ch']}:{x['v']}"]['he']), 'rashi_he': strip(r['he']), 'rashi_en': r['en']})
cp = f'_sef/{name}_quiz_cache.json'
try: done = json.load(open(cp, encoding='utf-8'))
except FileNotFoundError: done = {}
todo = [e for e in entries if e['id'] not in done]
print(len(done), 'cached', len(todo), 'todo', flush=True)
def call(b):
    last = None
    for a in range(4):
        try:
            p = subprocess.run(['claude', '-p', '--model', 'opus', '--system-prompt', 'Follow the task in the user message exactly and output only what it asks.'], input=SYSTEM+'\n\n=== INPUT JSON ===\n'+json.dumps(b, ensure_ascii=False),
                               capture_output=True, text=True, encoding='utf-8', shell=True, timeout=600)
            assert p.returncode == 0, p.stderr[:200]
            out = json.loads(re.sub(r'^```(?:json)?\s*|\s*```$', '', p.stdout.strip()))
            assert {o['id'] for o in out} == {e['id'] for e in b}
            for o in out:
                assert 1 <= len(o['points']) <= 2 and all(len(q['options']) == 3 for q in o['points'])
            return out
        except Exception as ex: last = ex; time.sleep(5 * (a + 1))
    print('FAILED', [e['id'] for e in b], last, flush=True); return []
bs = [todo[i:i + 4] for i in range(0, len(todo), 4)]
with ThreadPoolExecutor(6) as pool:
    for n, res in enumerate(pool.map(call, bs), 1):
        for o in res: done[o['id']] = o
        json.dump(done, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
        print('batch', n, '/', len(bs), flush=True)
json.dump(done, open(f'_sef/{name}_quiz.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('done', len(done), '/', len(entries))
