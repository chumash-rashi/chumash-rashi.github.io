#!/usr/bin/env python3
"""Apply compact no-scroll, keyboard-first, full-RTL layout to quiz HTML files."""

import re
import sys
import os

def transform(html: str, parsha_he: str) -> str:
    # === CSS REPLACEMENTS ===

    # Compact body padding and sizing
    html = html.replace(
        'padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:12px',
        'padding:8px max(10px,env(safe-area-inset-right,0px)) 6px max(10px,env(safe-area-inset-left,0px))'
    )
    # Vayera variant
    html = html.replace(
        'padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 48px',
        'padding:8px max(10px,env(safe-area-inset-right,0px)) 6px max(10px,env(safe-area-inset-left,0px))'
    )

    # Ensure body has overflow hidden and 100dvh
    html = html.replace('html,body{background:var(--bg)}', 'html,body{background:var(--bg);height:100dvh;overflow:hidden}')

    # Compact wrap gap
    html = re.sub(r'\.wrap\{[^}]*\}', '.wrap{max-width:640px;margin:0 auto;display:flex;flex-direction:column;gap:4px;height:100%}', html)

    # Main: flex grow, no overflow (clip instead)
    html = re.sub(r'main\{[^}]*\}', 'main{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column}', html)

    # Compact header
    html = re.sub(r'header\{[^}]*\}', 'header{display:flex;align-items:center;gap:8px;flex-shrink:0;flex-wrap:wrap}', html)
    html = re.sub(r'\.top\{[^}]*\}', '.top{display:contents}', html)

    # Smaller title
    html = re.sub(r'h1\{[^}]*\}', 'h1{margin:0;font-family:var(--f-heb);font-weight:700;font-size:16px;letter-spacing:.01em;white-space:nowrap}', html)
    html = html.replace('h1 span{font-family:var(--f-ui);font-weight:500;font-size:13px;color:var(--muted);margin-inline-start:8px}',
                        'h1 span{display:none}')

    # Compact count
    html = html.replace('.count{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13px}',
                        '.count{font-variant-numeric:tabular-nums;color:var(--muted);font-size:11px}')

    # Thinner progress bar
    html = html.replace('.bar{height:4px;', '.bar{height:3px;')

    # Compact toolbar
    html = re.sub(r'\.tools\{[^}]*\}', '.tools{display:none}', html)

    # Compact card
    html = re.sub(r'\.card\{[^}]*\}',
        '.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;overflow-y:auto}', html)

    # Smaller pasuk
    html = html.replace('.pasuk{font-family:var(--f-heb);font-size:24px;line-height:1.75;direction:rtl;text-align:right}',
                        '.pasuk{font-family:var(--f-heb);font-size:17px;line-height:1.6;direction:rtl;text-align:right}')
    html = html.replace('.pasuk{font-family:var(--f-heb);font-size:22px;',
                        '.pasuk{font-family:var(--f-heb);font-size:17px;')

    # Hide English verse (pasuk-en) — going all-Hebrew
    html = re.sub(
        r'\.pasuk-en\{[^}]*\}',
        '.pasuk-en{display:none}',
        html
    )

    # Compact dh
    html = html.replace('border-top:1px solid var(--line);padding-top:14px',
                        'border-top:1px solid var(--line);padding-top:6px')

    # Smaller dh text
    html = html.replace('.dh .w{font-family:var(--f-rashi);font-size:20px;font-weight:600}',
                        '.dh .w{font-family:var(--f-rashi);font-size:16px;font-weight:600}')

    # Compact question
    html = html.replace('.q{font-family:var(--f-body);font-size:17px;line-height:1.5;margin:0}',
                        '.q{font-family:var(--f-body);font-size:14px;line-height:1.4;margin:0}')

    # Compact options
    html = re.sub(r'\.opts\{[^}]*\}', '.opts{display:flex;flex-direction:column;gap:4px}', html)
    html = re.sub(
        r'\.opt\{display:flex;gap:10px;[^}]*\}',
        '.opt{display:flex;gap:8px;align-items:center;text-align:right;background:var(--bg);border:1.5px solid var(--line);border-radius:8px;padding:7px 10px;cursor:pointer;font-family:var(--f-body);font-size:13px;line-height:1.35;width:100%;direction:rtl}',
        html
    )

    # Smaller key badges
    html = html.replace('.opt .k{flex:none;font-family:var(--f-ui);font-size:12px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:6px;width:22px;height:22px;display:grid;place-items:center;margin-top:1px}',
                        '.opt .k{flex:none;font-family:var(--f-ui);font-size:11px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:5px;width:20px;height:20px;display:grid;place-items:center}')

    # Compact reveal
    html = html.replace('.reveal{display:flex;flex-direction:column;gap:12px;border-top:1px solid var(--line);padding-top:14px}',
                        '.reveal{display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--line);padding-top:8px}')

    # Compact row
    html = re.sub(r'\.row\{display:grid;[^}]*\}',
                  '.row{display:flex;flex-direction:column;gap:2px}', html)
    html = re.sub(r'\.row \.t\{[^}]*\}',
                  '.row .t{font-size:10px;font-weight:600;letter-spacing:.06em;color:var(--accent);direction:rtl}', html)
    html = html.replace('.row p{margin:0;font-family:var(--f-body);font-size:15.5px;line-height:1.55;min-width:0}',
                        '.row p{margin:0;font-family:var(--f-body);font-size:13px;line-height:1.4;direction:rtl}')

    # Compact nav
    html = html.replace('.btn{border:none;border-radius:10px;padding:11px 18px;font-weight:600;cursor:pointer;background:var(--accent);color:var(--surface)}',
                        '.btn{border:none;border-radius:8px;padding:8px 14px;font-weight:600;cursor:pointer;background:var(--accent);color:var(--surface);font-size:13px}')
    html = html.replace(".btn.sec{background:none;color:var(--muted);border:1px solid var(--line)}",
                        ".btn.sec{background:none;color:var(--muted);border:1px solid var(--line);font-size:13px}")

    # Compact point separator
    html = html.replace('.point+.point{border-top:1px dashed var(--line);padding-top:16px}',
                        '.point+.point{border-top:1px dashed var(--line);padding-top:8px}')

    # Smaller hint
    html = html.replace('.hint{font-size:12px;color:var(--muted);text-align:center;flex-shrink:0}',
                        '.hint{font-size:10px;color:var(--muted);text-align:center;flex-shrink:0}')

    # Compact verdict
    html = html.replace('.verdict{font-weight:600;font-size:14px}',
                        '.verdict{font-weight:600;font-size:12px}')

    # Smaller full rashi text
    html = html.replace('.full .he{font-family:var(--f-rashi);font-size:18px;line-height:1.8;direction:rtl;text-align:right}',
                        '.full .he{font-family:var(--f-rashi);font-size:14px;line-height:1.6;direction:rtl;text-align:right}')

    # Compact done screen
    html = html.replace('.done h2{font-family:var(--f-heb);margin:0;font-size:26px}',
                        '.done h2{font-family:var(--f-heb);margin:0;font-size:20px}')

    # === RTL: add dir to html and body ===
    html = html.replace('<html lang="en">', '<html lang="he" dir="rtl">')
    html = html.replace('<body>', '<body dir="rtl">')
    # Don't double-add if already there
    html = html.replace('<body dir="rtl" dir="rtl">', '<body dir="rtl">')

    # === JS: remaining English strings ===
    html = html.replace("'1 רש״י על this posuk'", "'רש״י 1 על פסוק זה'")
    html = html.replace("and got '+s.נכון+' מתוך '+s.pts+' questions נכון", "· '+s.נכון+' מתוך '+s.pts+' נכון")
    html = html.replace("' רש״יות not finished. <button class=\"ghost\" id=\"gs\" type=\"button\">עבור אל first one</button>'",
                        "' רש״יות לא הושלמו. <button class=\"ghost\" id=\"gs\" type=\"button\">לראשון</button>'")
    html = html.replace("' רש״יות to review: '", "' רש״יות לחזרה: '")
    html = html.replace("${x.points.length} points", "${x.points.length} נקודות")

    # Swap nav button order for RTL (back on right, next on left)
    # Arrow keys hint - swap for RTL
    html = html.replace('מקשים: 3-1 לתשובה · Enter או ← להבא · → לחזור',
                        'מקשים: 1-3 לתשובה · Enter להבא · ← / → לניווט')

    return html


if __name__ == '__main__':
    files = {
        'Rashi-Lech-Lecha.html': 'לך לך',
        'Rashi-Vayera.html': 'וירא',
        'Rashi-Chayei-Sarah.html': 'חיי שרה',
    }
    base = os.path.dirname(os.path.abspath(__file__))
    for fname, parsha_he in files.items():
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        html = transform(html, parsha_he)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'{fname}: compact + RTL applied')
