#!/usr/bin/env python3
"""Assemble Rashi-<Name>.html from the Toldot page as a template.
Inputs (all produced earlier): _sef/<name>_skeleton.json, _sef/<name>_quiz.json, and a niqqud map
(_sef/<name>_niqqud.json: unvowelled string -> vowelled string) for every quiz question/option.
Usage: python build_parsha_page.py vayetze Vayetze ויצא "ויצא" vayetze-rashi-v1 "Bereishis 28:10 – 32:3"
"""
import sys, re, json, difflib

name, Name, heb, key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
strip = lambda s: re.sub(r'[֑-ׇ]', '', s)
clean = lambda w: re.sub(r'[֑-ֽֿ֯׀׃-ׇ]', '', w)   # drop taamim, keep vowels

def toks(v):
    out = []
    for ch in v:
        if '֑' <= ch <= 'ׇ' and out: out[-1] += ch
        else: out.append(ch)
    return out

def align(k, v):
    """Return v's vowels laid over k's exact letters (restores any letter the model dropped/changed)."""
    t = toks(v); sm = difflib.SequenceMatcher(None, list(k), [strip(x) for x in t], autojunk=False); res = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'equal': res += t[b1:b2]
        elif op in ('delete', 'replace'): res += list(k[a1:a2])
    return ''.join(res)

def pwords(x):
    t = re.sub(r'</?mark>', '', x['pasuk_html']).replace('־', '־ ')
    return [w for w in t.split() if w]

QUOTE = re.compile(r'"([^"]+)"')
def quote_fix(s, words):
    sw = [strip(w).replace('־', '') for w in words]
    def rep(mo):
        q = mo.group(1); qw = q.split(); n = len(qw); qs = [strip(w).replace('־', '') for w in qw]
        for i in range(len(words) - n + 1):
            if sw[i:i + n] == qs:
                new = ' '.join(clean(w) for w in words[i:i + n]).replace('־ ', '־').strip()
                return mo.group(0).replace(q, new)
        return mo.group(0)
    return QUOTE.sub(rep, s)

sk = json.load(open(f'_sef/{name}_skeleton.json', encoding='utf-8'))
quiz = json.load(open(f'_sef/{name}_quiz.json', encoding='utf-8'))
nik = json.load(open(f'_sef/{name}_niqqud.json', encoding='utf-8'))
miss = 0
def vow(s, words):
    global miss
    if s not in nik: miss += 1; return s
    return quote_fix(align(s, nik[s]), words)
for x in sk:
    q = quiz[x['id']]; w = pwords(x)
    x['rashi_en'] = q['simple']
    x['points'] = [{'q': vow(p['q'], w), 'options': [vow(o, w) for o in p['options']], 'kasha': p.get('kasha', ''), 'answer': p['answer'], 'kp': p.get('kp', [])} for p in q['points']]
print('entries', len(sk), 'strings without niqqud', miss)

h = open('Rashi-Toldot.html', encoding='utf-8', newline='').read()
m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', h, re.S)
h = h[:m.start()] + m.group(1) + json.dumps(sk, ensure_ascii=False) + m.group(3) + h[m.end():]
h = h.replace('<title>Toldot Rashi</title>', f'<title>{Name} Rashi</title>')
h = h.replace('רש״י · תולדות <span>רש״י על תולדות</span>', f'רש״י · {heb} <span>רש״י על {heb}</span>')
h = h.replace('סליק פרשת תולדות', f'סליק פרשת {heb}')
h = h.replace("const KEY='toldot-rashi-v2'", f"const KEY='{key}'")
assert h.count(f"KEY='{key}'") == 1
open(f'Rashi-{Name}.html', 'w', encoding='utf-8', newline='').write(h)
print('wrote', f'Rashi-{Name}.html', len(h))
