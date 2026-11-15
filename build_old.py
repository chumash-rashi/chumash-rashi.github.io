import sys, re, json
# usage: build_old.py <skelname> <PageName> <hebname> <key>  -- builds from Toldot template with quiz (unvowelled; run add_niqqud.py after)
name, Name, heb, key = sys.argv[1:5]
sk = json.load(open(f'_sef/{name}_skeleton.json', encoding='utf-8')); quiz = json.load(open(f'_sef/{name}_quiz.json', encoding='utf-8'))
for x in sk:
    q = quiz[x['id']]; x['rashi_en'] = q['simple']
    x['points'] = [{'q': p['q'], 'options': p['options'], 'kasha': p.get('kasha', ''), 'answer': p['answer'], 'kp': p['kp']} for p in q['points']]
h = open('Rashi-Toldot.html', encoding='utf-8', newline='').read()
m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', h, re.S)
h = h[:m.start()] + m.group(1) + json.dumps(sk, ensure_ascii=False) + m.group(3) + h[m.end():]
h = h.replace('<title>Toldot Rashi</title>', f'<title>{Name} Rashi</title>')
h = h.replace('רש״י · תולדות <span>רש״י על תולדות</span>', f'רש״י · {heb} <span>רש״י על {heb}</span>')
h = h.replace('סליק פרשת תולדות', f'סליק פרשת {heb}')
h = re.sub(r"const KEY='[^']+'", f"const KEY='{key}'", h)
open(f'Rashi-{Name}.html', 'w', encoding='utf-8', newline='').write(h); print('wrote', Name, len(h))
