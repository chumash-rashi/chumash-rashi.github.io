#!/usr/bin/env python3
"""Per-word pass: every word inside quote marks in q/options takes the pasuk's vowels, also when the quote drops a prefix letter (e.g. בַּשָּׁנָה -> "שָׁנָה")."""
import sys, re, json
strip = lambda s: re.sub('[֑-ׇ]', '', s)
clean = lambda w: re.sub('[֑-ֽֿ֯׀׃-׆]', '', w)
H = 'א-ת֑-ׇ'
Q = re.compile(r'(?<![%s])([בהולכמש][֑-ׇ]*״)([^״"\']+?)(״)(?![%s])|(?<![%s])(״)([^״"\']+?)(״)(?![%s])|(["“])([^"“”״\']+)(["”])|(?<![%s])(\')([^"“”״\']+)(\')(?![%s])' % (H, H, H, H, H, H))
def clusters(w):
    out = []
    for ch in w:
        if '֑' <= ch <= 'ׇ' and out: out[-1] += ch
        else: out.append(ch)
    return out
def fixword(w, pw):
    L = strip(w).replace('־', '')
    if not L: return w
    for p in pw:                                  # exact word
        if strip(p).replace('־', '') == L: return clean(p).rstrip('־')
    if len(L) >= 3:                               # pasuk word minus prefix
        for p in pw:
            cl = clusters(clean(p)); k = len(L)
            if len(cl) > k and len(cl) - k <= 3 and ''.join(strip(c) for c in cl[-k:]) == L and ''.join(strip(c) for c in cl[:-k]) and all(c[0] in 'בהוכלמש' for c in cl[:-k]):
                return ''.join(cl[-k:]).replace('ּ', '', 1) if cl[-k][0] not in '' and 'ּ' in cl[-k] else ''.join(cl[-k:])
    return w
def fix(s, pw):
    def rep(m):
        g = [x for x in m.groups() if x is not None]; q = g[1]
        new = ' '.join('־'.join(fixword(t, pw) for t in w.split('־')) for w in q.split(' '))
        new = new.replace('־ ', '־')
        return g[0] + new + g[2]
    return Q.sub(rep, s)
n = 0
for path in sys.argv[1:]:
    h = open(path, encoding='utf-8', newline='').read()
    m = re.search(r'(const DATA = )(\[.*?\])(;\s*\n)', h, re.S); d = json.loads(m.group(2)); c = 0
    for x in d:
        pw = [w for w in re.sub(r'</?mark>', '', x['pasuk_html']).replace('־', '־ ').split() if w]
        for p in x['points']:
            for key in ('q',):
                a = fix(p[key], pw)
                if a != p[key]: c += 1; print(path[:12], p[key][:70], '->', a[:70]) if c <= 6 else 0; p[key] = a
            b = [fix(o, pw) for o in p['options']]
            if b != p['options']: c += 1; p['options'] = b
    open(path, 'w', encoding='utf-8', newline='').write(h[:m.start()] + m.group(1) + json.dumps(d, ensure_ascii=False) + m.group(3) + h[m.end():])
    print(path, 'changed', c)
