#!/usr/bin/env python3
"""After build_parsha_page.py: add EN data, names, index entry. Usage: finish_parsha.py name Name heb vowelled_heb range"""
import re,json,glob,io,sys
name,Name,heb,vheb,rng=sys.argv[1:6]
f=f'Rashi-{Name}.html'
h=io.open(f,encoding='utf-8',newline='').read()
trans={}
for p in sorted(glob.glob(f'_sef/{name}_trans/out_*.json')):
    for it in json.load(open(p,encoding='utf-8')): trans[it['id']]=it
gen=json.load(open('_sef/gen_en.json',encoding='utf-8'))['text']; rsh=json.load(open('_sef/rashi_en.json',encoding='utf-8'))['text']
def clean(s):
    s=re.sub(r'<sup[^>]*>.*?</sup>','',s,flags=re.S); s=re.sub(r'<i class="footnote">.*?</i>','',s,flags=re.S); s=re.sub(r'<[^>]+>','',s)
    return re.sub(r'\s+',' ',s.replace('&nbsp;',' ').replace('&thinsp;',' ')).strip()
m=re.search(r'const DATA = (\[.*?\])(;\s*\n)',h,re.S); d=json.loads(m.group(1)); EN={}
for x in d:
    t=trans[Name+'|'+x['id']]; ch,v,n=int(x['ch']),int(x['v']),int(x['n'])
    assert len(t['points'])==len(x['points'])
    try: pe=clean(gen[ch-1][v-1])
    except Exception: pe=''
    try:
        r=rsh[ch-1][v-1]; re_=clean(r[n-1] if isinstance(r,list) else r)
    except Exception: re_=''
    EN[x['id']]={'e':t['explanation'],'pe':pe,'re':re_,'p':[{'q':p['q'],'o':p['options']} for p in t['points']]}
m2=re.search(r'const EN = .*?;\n(?=const|/\*|\n|let|function)',h[m.end():],re.S)
s,e=m.end()+m2.start(),m.end()+m2.end()
h=h[:s]+'const EN = '+json.dumps(EN,ensure_ascii=False,separators=(',',':'))+';\n'+h[e:]
h=h.replace('const PNAME=["תולדות", "Toldot"]',f'const PNAME=["{heb}", "{Name}"]')
h=h.replace("Finished Parshas Toldot",f"Finished Parshas {Name}").replace("T('סליק פרשת תולדות'",f"T('סליק פרשת {heb}'")
h=h.replace("'וירא':'וַיֵּרָא'",f"'וירא':'וַיֵּרָא','{heb}':'{vheb}'",1)
assert 'Toldot' not in h.replace('Rashi-Toldot','')
io.open(f,'w',encoding='utf-8',newline='').write(h)
ix=io.open('index.html',encoding='utf-8',newline='').read(); nl='\r\n' if '\r\n' in ix else '\n'
add=f'''    <a href="Rashi-{Name}.html">
      <span class="heb">{heb}</span>
      <span class="meta">
        <span class="en">{Name}</span>
        <span class="desc">Bereishis {rng}</span>
      </span>
      <span class="arrow">&rsaquo;</span>
    </a>
'''.replace('\n',nl)
mk='  </div>\n</div>\n</body>'.replace('\n',nl); assert mk in ix
io.open('index.html','w',encoding='utf-8',newline='').write(ix.replace(mk,add+mk,1))
print('ok',len(EN))
