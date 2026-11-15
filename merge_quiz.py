#!/usr/bin/env python3
"""Merge agent-generated Hebrew quiz chunks into _sef/<name>_quiz.json and validate.
Usage: python merge_quiz.py <name> <scratchdir> <nchunks>"""
import sys, json, re, os
name, S, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
strip = lambda s: re.sub(r'[\u0591-\u05c7]', '', re.sub(r'</?mark>', '', s))
nz = lambda s: re.sub(r'[^\u05d0-\u05ea ]', '', strip(s).replace('־', ' '))
nz = lambda s: ' '.join(re.sub(r'[^\u05d0-\u05ea ]', '', strip(s).replace('\u05be', ' ')).split())
sk = json.load(open(f'_sef/{name}_skeleton.json', encoding='utf-8'))
by = {x['id']: x for x in sk}
quiz, bad = {}, []
for i in range(n):
    p = f'{S}/out_{name}_{i}.json'
    if not os.path.exists(p): print('MISSING chunk', i); continue
    for o in json.load(open(p, encoding='utf-8')): quiz[o['id']] = o
for id_, x in by.items():
    o = quiz.get(id_)
    if not o: bad.append((id_, 'missing')); continue
    r = nz(x['rashi_he'])
    for pt in o['points']:
        if len(pt['options']) != 3: bad.append((id_, 'options'))
        pt['kp'] = [k for k in pt.get('kp', []) if nz(k) and nz(k) in r]
        if not pt['kp']: bad.append((id_, 'nokp'))
    if not o.get('simple'): bad.append((id_, 'nosimple'))
    if re.search('[A-Za-z]', json.dumps([o['simple']]+[[pt['q'],pt['kasha'],pt['answer']]+pt['options'] for pt in o['points']], ensure_ascii=False)): bad.append((id_, 'latin'))
json.dump(quiz, open(f'_sef/{name}_quiz.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(name, 'entries', len(quiz), '/', len(by), 'points', sum(len(o['points']) for o in quiz.values()), 'issues', len(bad), bad[:15])
