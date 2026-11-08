"""Fuzzy highlighting of a dibbur hamaschil inside a pasuk (HTML with taamim).

Exact substring matching misses when the pasuk has maqaf-joined words, plene/chaser
spelling differences (ויעשו vs ויעש), or the dh writes the divine name as ה'.
We match word-by-word on a skeleton (no nikkud/taamim, no ו/י) instead.
"""
import re
import difflib

WORD = re.compile(r'[֑-ֽֿ-ׇא-ת]+')
LETTERS = re.compile(r'[א-ת]')


def _skel(w):
    return ''.join(c for c in LETTERS.findall(w) if c not in 'וי')


def _dh_segments(dh):
    segs = []
    dh = re.sub(r'\([^)]*\)', '', dh)
    for part in re.split(r"\.{2,}|…|וגו['׳’]?(?=\s|$)", dh):
        toks = []
        for t in re.split(r'[\s־\-]+', part):
            if not t or re.fullmatch(r"וגו['׳’]?", t):
                continue
            if re.fullmatch(r"[וכלמבש]?ה['׳’]", t):   # ה' (with optional prefix)
                toks.append(t[:-2] + 'יהוה' if len(t) > 2 else 'יהוה')
            else:
                toks.append(t)
        if toks:
            segs.append(toks)
    return segs


def _sim(a, b):
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _find(tokens, dh_toks):
    """Best (start, end) token window for dh_toks, or None."""
    want = [_skel(t) for t in dh_toks]
    full = [''.join(LETTERS.findall(t)) for t in dh_toks]
    n = len(want)
    best, best_score = None, 0.0
    for s in range(len(tokens) - n + 1):
        sc = sum(_sim(tokens[s + k][2], want[k]) for k in range(n)) / n
        # tie-break: prefer the occurrence spelled exactly like the dh (e.g. אלי vs אל־)
        sc += 0.01 * sum(tokens[s + k][3] == full[k] for k in range(n)) / n
        if sc > best_score:
            best, best_score = (s, s + n - 1), sc
    return best if best_score >= 0.8 else None


def mark_dh(pasuk_html, dh):
    """Return pasuk_html with the dh wrapped in <mark>; unchanged-but-unmarked if no match."""
    html = pasuk_html.replace('<mark>', '').replace('</mark>', '')
    tokens = [(m.start(), m.end(), _skel(m.group()), ''.join(LETTERS.findall(m.group()))) for m in WORD.finditer(html) if LETTERS.search(m.group())]
    spans = []
    for seg in _dh_segments(dh):
        r = _find(tokens, seg)
        if r:
            spans.append((tokens[r[0]][0], tokens[r[1]][1]))
    for a, b in sorted(spans, reverse=True):
        html = html[:a] + '<mark>' + html[a:b] + '</mark>' + html[b:]
    return html
