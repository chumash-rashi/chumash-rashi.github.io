#!/usr/bin/env python3
"""Build <name>_source.json and the skeleton DATA entries (no quiz yet) for a Genesis parsha
from the Sefaria export files saved in _sef/ (see CHANGELOG / README notes).
Usage: python build_parsha_data.py vayetze 28:10 32:3
"""
import sys, re, json
from mark_dh import mark_dh

name, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
a = tuple(map(int, a.split(':'))); b = tuple(map(int, b.split(':')))
L = lambda k: json.load(open(f'_sef/{k}.json', encoding='utf-8'))['text']
he, nik, rh, ren = L('gen_he'), L('gen_nik'), L('rashi_he'), L('rashi_en')
tag = re.compile(r'<[^>]+>')
clean = lambda s: re.sub(r'\s+', ' ', tag.sub('', s)).strip()
src, data = {}, []
for ch in range(a[0], b[0] + 1):
    for v in range(1, len(he[ch - 1]) + 1):
        if (ch, v) < a or (ch, v) > b: continue
        rs = rh[ch - 1][v - 1]; es = ren[ch - 1][v - 1]
        rs = [rs] if isinstance(rs, str) else rs; es = [es] if isinstance(es, str) else es
        assert len(rs) == len(es), (ch, v)
        src[f'{ch}:{v}'] = {'ch': str(ch), 'v': str(v), 'he': clean(he[ch - 1][v - 1]), 'en': clean(nik[ch - 1][v - 1]),
                            'rashis': [{'he': clean(x), 'en': clean(y)} for x, y in zip(rs, es)]}
        for n, (x, y) in enumerate(zip(rs, es), 1):
            m = re.match(r'\s*<b>(.*?)</b>', x, re.S)
            dh = clean(m.group(1)) if m else clean(x).split('.')[0]
            dh = re.sub(r'[\s.:,]+$', '', dh)
            dh = re.sub(r'^\(', '', dh)
            w = dh.split(' ')
            for i, t in enumerate(w):           # cut at first vowelled word (bold run swallowed body text)
                if re.search(r'[ְ-ׇ]', t): w = w[:i]; break
            dh = ' '.join(w) or dh
            parts = [p.strip() for p in dh.split(',')]
            if len(parts) > 1 and len(set(parts)) == 1: dh = parts[0]
            pasuk_html = he[ch - 1][v - 1]
            data.append({'id': f'{ch}:{v}.{n}', 'ch': ch, 'v': v, 'n': n, 'dh': dh,
                         'pasuk_html': mark_dh(pasuk_html, dh),
                         'pasuk_en': clean(nik[ch - 1][v - 1]), 'rashi_he': clean(x), 'rashi_en': '', 'note': '', 'points': []})
json.dump(src, open(f'{name}_source.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(data, open(f'_sef/{name}_skeleton.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(src), 'pesukim', len(data), 'rashis', sum('<mark>' in x['pasuk_html'] for x in data), 'marked')
for x in data:
    if '<mark>' not in x['pasuk_html']: print('unmarked', x['id'], x['dh'])
