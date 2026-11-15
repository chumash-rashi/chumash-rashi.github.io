#!/usr/bin/env python3
"""Add full niqqud to every quiz question and answer option (points[].q / points[].options) in a Rashi-*.html file.
Usage: python add_niqqud.py Rashi-Toldot.html
Results are cached in <html>_niqqud_cache.json (keyed by the unvowelled text) so reruns only do new strings.
"""
import subprocess, sys, re, json, time, subprocess
from concurrent.futures import ThreadPoolExecutor

MODEL = "claude-sonnet-5-5"
SYSTEM = """אתה מנקד מומחה לעברית מקראית ולשון חכמים ועברית מודרנית. תקבל מערך JSON של מחרוזות בעברית. החזר מערך JSON באותו אורך ובאותו סדר, שבו כל מילה עברית מנוקדת בניקוד מלא ומדויק (קמץ, פתח, צירי, סגול, שווא, חיריק, חולם, שורוק, קובוץ, דגש וכו׳), לפי ההגייה התקנית. אל תשנה, תוסיף או תמחק אותיות, מילים או סימני פיסוק, ואל תוסיף טעמי מקרא. מילים שכבר מנוקדות השאר כפי שהן. החזר JSON בלבד, ללא גדרות קוד וללא טקסט נוסף."""

def strip(s): return re.sub(r'[֑-ׇ]', '', s)

import difflib
def _toks(v):
    out = []
    for ch in v:
        if '֑' <= ch <= 'ׇ' and out: out[-1] += ch
        else: out.append(ch)
    return out
def align(k, v):
    """v's vowels laid over k's exact letters (restores letters the model dropped/changed)."""
    t = _toks(v); sm = difflib.SequenceMatcher(None, list(strip(k)) if False else list(k), [strip(x) for x in t], autojunk=False); res = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'equal': res += t[b1:b2]
        elif op in ('delete', 'replace'): res += list(k[a1:a2])
    return ''.join(res)

def call(client, batch):
    last = None
    for attempt in range(5):
        try:
            p = subprocess.run(["claude", "-p", "--model", "sonnet", "--system-prompt", SYSTEM], input=json.dumps(batch, ensure_ascii=False),
                capture_output=True, text=True, encoding='utf-8', shell=True, timeout=300)
            assert p.returncode == 0, p.stderr[:300]
            t = re.sub(r'^```(?:json)?\s*|\s*```$', '', p.stdout.strip())
            out = json.loads(t)
            assert len(out) == len(batch)
            return [align(a, b) for a, b in zip(batch, out)]
        except Exception as ex:
            last = ex; time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"batch failed: {last}")

def main():
    path = sys.argv[1]
    html = open(path, encoding='utf-8').read()
    m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', html, re.S)
    data = json.loads(m.group(2))
    cache_path = path.replace('.html', '_niqqud_cache.json')
    try: cache = json.load(open(cache_path, encoding='utf-8'))
    except FileNotFoundError: cache = {}
    texts = []
    for x in data:
        for p in x.get("points", []):
            texts += [p["q"]] + p["options"]
    todo = sorted({t for t in texts if t not in cache})
    print(f"{len(cache)} cached, {len(todo)} to do", flush=True)
    client = None
    batches = [todo[i:i+15] for i in range(0, len(todo), 15)]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for n, (b, res) in enumerate(zip(batches, pool.map(lambda b: call(client, b), batches)), 1):
            cache.update(dict(zip(b, res)))
            json.dump(cache, open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f"  batch {n}/{len(batches)} ok", flush=True)
    for x in data:
        for p in x.get("points", []):
            p["q"] = cache[p["q"]]
            p["options"] = [cache[o] for o in p["options"]]
    new = m.group(1) + json.dumps(data, ensure_ascii=False) + m.group(3)
    html = html[:m.start()] + new + html[m.end():]
    open(path, 'w', encoding='utf-8', newline='').write(html)
    print("done", len(data), flush=True)

if __name__ == "__main__":
    main()
