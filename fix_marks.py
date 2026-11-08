import re, json, glob
from mark_dh import mark_dh

for f in sorted(glob.glob('Rashi-*.html')):
    t = open(f, encoding='utf-8').read()
    m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', t, re.S)
    d = json.loads(m.group(2))
    before = sum('<mark>' in x['pasuk_html'] for x in d)
    for x in d:
        x['pasuk_html'] = mark_dh(x['pasuk_html'], x['dh'])
    after = sum('<mark>' in x['pasuk_html'] for x in d)
    new = m.group(1) + json.dumps(d, ensure_ascii=False) + m.group(3)
    t = t[:m.start()] + new + t[m.end():]
    open(f, 'w', encoding='utf-8', newline='').write(t)
    print(f, len(d), 'marked', before, '->', after)
    for x in d:
        if '<mark>' not in x['pasuk_html']:
            print('   still unmarked', x['id'], x['dh'].encode('unicode_escape').decode()[:0], x['dh'][::-1] if False else '')
