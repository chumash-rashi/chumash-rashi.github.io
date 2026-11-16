#!/usr/bin/env python3
"""Add an English version (language toggle) and a printable test with answer key to every Rashi-*.html.
Usage: python add_english.py <dir with out_*.json translations>
Idempotent: skips pages that already contain /*EN*/."""
import sys, re, json, glob, os
TR = sys.argv[1]
names = {'Toldot': ('תולדות', 'Toldot'), 'Chayei-Sarah': ('חיי שרה', 'Chayei Sarah'), 'Lech-Lecha': ('לך לך', 'Lech Lecha'),
         'Vayera': ('וירא', 'Vayera'), 'Vayetze': ('ויצא', 'Vayetze')}
trans = {}
for f in sorted(glob.glob(os.path.join(TR, 'out_*.json'))):
    for it in json.load(open(f, encoding='utf-8')): trans[it['id']] = it
gen = json.load(open('_sef/gen_en.json', encoding='utf-8'))['text']
rsh = json.load(open('_sef/rashi_en.json', encoding='utf-8'))['text']

def clean(s):
    s = re.sub(r'<sup[^>]*>.*?</sup>', '', s, flags=re.S)
    s = re.sub(r'<i class="footnote">.*?</i>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s.replace('&nbsp;', ' ').replace('&thinsp;', ' ')).strip()

def rep(h, old, new, cnt=1):
    assert h.count(old) == cnt, (h.count(old), old[:70])
    return h.replace(old, new)

CSS = r'''
/*EN*/
html[dir=ltr] .opt{direction:ltr;text-align:left}
html[dir=ltr] .q{direction:ltr;text-align:left}
html[dir=ltr] .pnum{direction:ltr}
.q .hb,.opt .hb{font-family:var(--f-heb);font-size:1.12em}
.pasuk .pen{direction:ltr;text-align:left;font-family:var(--f-body);font-size:17px;line-height:1.4;letter-spacing:0;word-spacing:0;margin-top:.6em;color:var(--muted)}
.quote .enx{direction:ltr;text-align:left;font-family:var(--f-body);font-size:.82em;line-height:1.4;margin-top:6px;padding-top:6px;border-top:1px solid var(--line)}
.quote .enx i{color:var(--muted)}
.quote .src{direction:ltr}
.hint .ghost{padding:2px 8px;font-size:11px}
.hint select{font-size:11px;padding:2px 4px}
#pa{display:none}
@media print{
  @page{margin:14mm}
  html,body{height:auto!important;overflow:visible!important;background:#fff!important;color:#000!important}
  body>*:not(#pa){display:none!important}
  #pa{display:block;font-family:var(--f-body);font-size:11.5pt;line-height:1.4;color:#000}
  #pa h1{font-size:18pt;margin:0 0 4pt}
  #pa .pr-meta{display:flex;justify-content:space-between;gap:16pt;border-bottom:1.5pt solid #000;padding:4pt 0 8pt;margin-bottom:10pt;font-size:11pt}
  #pa .pr-r{break-inside:avoid;margin:0 0 12pt;border-top:.75pt solid #999;padding-top:6pt}
  #pa .pr-ref{font-size:9.5pt;color:#444;margin-bottom:3pt}
  #pa .pr-pasuk{font-family:var(--f-heb);font-size:15pt;line-height:1.6;direction:rtl;text-align:right}
  #pa .pr-pasuk mark{background:#e8e8e8;color:#000;text-decoration:underline;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  #pa .pr-pen{font-size:9.5pt;color:#333;margin:2pt 0 4pt}
  #pa .pr-q{margin:6pt 0 0}
  #pa .pr-qt{font-weight:600}
  #pa .pr-o{margin:1.5pt 0 0 14pt;display:flex;gap:6pt}
  #pa[dir=rtl] .pr-o{margin:1.5pt 14pt 0 0}
  #pa .pr-o b{flex:none}
  #pa .hb{font-family:var(--f-heb);font-size:1.12em}
  #pa .pr-key{break-before:page}
  #pa .pr-a{break-inside:avoid;margin:0 0 6pt;font-size:10.5pt}
  #pa .pr-ex{display:block;color:#444;font-size:9.5pt}
}
'''

JS_HEAD = r'''/*EN*/
let LANG='he';try{LANG=localStorage.getItem('rashi-lang')==='en'?'en':'he'}catch(e){}
const T=(h,e)=>LANG==='en'?e:h;
const PNAME=%s;
function applyLang(){const d=document.documentElement;d.lang=LANG==='en'?'en':'he';d.dir=LANG==='en'?'ltr':'rtl';document.body.dir=d.dir;document.body.classList.toggle('en',LANG==='en');document.title=(LANG==='en'?PNAME[1]:PNAME[0])+' · Rashi'}
const E=(x,j)=>{const e=EN[x.id];return (e&&e.p&&e.p[j])||{q:x.points[j].q,o:x.points[j].options}};
const enWrap=s=>esc(s).replace(/[֐-׿]+(?:[ \-־׳״]+[֐-׿]+)*/g,'<span class="hb" lang="he" dir="rtl">$&</span>');
function enBlock(x){const e=EN[x.id];if(LANG!=='en'||!e)return '';
  return '<div class="enx" lang="en">'+(e.e?'<div>'+esc(e.e)+'</div>':'')+(e.re?'<div><i>Rashi (Metsudah): </i>'+esc(e.re)+'</div>':'')+'</div>'}
function buildPrint(sel){const en=LANG==='en';const lets=en?['A','B','C']:['א','ב','ג'];
  const set=DATA.filter(x=>sel==='all'||String(x.ch)===sel);let qn=0,body='',key='';
  set.forEach(x=>{const e=EN[x.id];
    body+='<section class="pr-r"><div class="pr-ref">'+T('בראשית '+gem(x.ch)+':'+gem(x.v),'Genesis '+x.ch+':'+x.v)+' · '+(en?'Rashi on ':'רש״י ד״ה ')+'<span lang="he" dir="rtl">'+esc(x.dh)+'</span></div><div class="pr-pasuk" lang="he">'+x.pasuk_html+'</div>'+(en&&e&&e.pe?'<div class="pr-pen">'+esc(e.pe)+'</div>':'');
    x.points.forEach((pt,j)=>{qn++;const ord=order(x.id+'#'+j);const q=E(x,j);
      body+='<div class="pr-q"><div class="pr-qt">'+qn+'. '+(en?enWrap(q.q):heWrap(pt.q))+'</div>'+ord.map((o,k)=>'<div class="pr-o"><b>'+lets[k]+'.</b><span>'+(en?enWrap(q.o[o]):heWrap(pt.options[o]))+'</span></div>').join('')+'</div>';
      key+='<div class="pr-a"><b>'+qn+'. '+lets[ord.indexOf(0)]+'</b> — '+(en?enWrap(q.o[0]):heWrap(pt.options[0]))+'<span class="pr-ex">'+T('בראשית '+gem(x.ch)+':'+gem(x.v),'Genesis '+x.ch+':'+x.v)+' · '+(en?'Rashi on ':'רש״י ד״ה ')+'<span lang="he" dir="rtl">'+esc(x.dh)+'</span>'+(j===0&&en&&e&&e.e?' — '+esc(e.e):'')+'</span></div>'});
    body+='</section>'});
  const ttl=en?'Rashi on '+PNAME[1]+(sel==='all'?'':' — Chapter '+sel):'רש״י על פרשת '+PNAME[0]+(sel==='all'?'':' — פרק '+gem(+sel));
  return '<h1>'+ttl+'</h1><div class="pr-meta"><span>'+T('שם: ______________________','Name: ______________________')+'</span><span>'+T('תאריך: ____________','Date: ____________')+'</span><span>'+T('ציון: ______ / '+qn,'Score: ______ / '+qn)+'</span></div>'+body+
    '<div class="pr-key"><h1>'+T('מפתח תשובות','Answer Key')+'</h1>'+key+'</div>'}
function doPrint(){let pa=$('pa');if(!pa){pa=document.createElement('div');pa.id='pa';document.body.appendChild(pa)}
  pa.dir=LANG==='en'?'ltr':'rtl';pa.lang=LANG==='en'?'en':'he';pa.innerHTML=buildPrint(window._prSel||'all');window.print()}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('#langBtn,#printBtn');if(!b)return;
  if(b.id==='langBtn'){LANG=LANG==='en'?'he':'en';try{localStorage.setItem('rashi-lang',LANG)}catch(_){}applyLang();render()}
  else doPrint()});
document.addEventListener('change',e=>{if(e.target.id==='prSel')window._prSel=e.target.value});
'''

done = 0
for f in sorted(glob.glob('Rashi-*.html')):
    key = f[6:-5]
    if key not in names: continue
    h = open(f, encoding='utf-8', newline='').read()
    if '/*EN*/' in h: print('skip', f); continue
    he, en = names[key]
    m = re.search(r'const DATA = (\[.*?\])(;\s*\n)', h, re.S)
    d = json.loads(m.group(1))
    EN = {}
    for x in d:
        t = trans[key + '|' + x['id']]
        assert len(t['points']) == len(x['points']) and all(len(p['options']) == len(q['options']) for p, q in zip(t['points'], x['points'])), x['id']
        ch, v, n = int(x['ch']), int(x['v']), int(x['n'])
        try: pe = clean(gen[ch - 1][v - 1])
        except Exception: pe = ''
        try:
            r = rsh[ch - 1][v - 1]; re_ = clean(r[n - 1] if isinstance(r, list) else r)
        except Exception: re_ = ''
        EN[x['id']] = {'e': t['explanation'], 'pe': pe, 're': re_, 'p': [{'q': p['q'], 'o': p['options']} for p in t['points']]}
    h = h[:m.end()] + 'const EN = ' + json.dumps(EN, ensure_ascii=False, separators=(',', ':')) + ';\n' + h[m.end():]
    # CSS
    h = rep(h, '</style>\n\n<div class="wrap">', CSS + '</style>\n\n<div class="wrap">')
    # JS head after KEY line
    km = re.search(r"const KEY='[^']+';\n", h)
    h = h[:km.end()] + JS_HEAD % json.dumps([he, en], ensure_ascii=False) + h[km.end():]
    # header count
    h = rep(h, "' רש״יות · '+s.נכון+' / '+s.pts+' נכון'", "T(' רש״יות · ',' Rashis · ')+s.נכון+' / '+s.pts+T(' נכון',' correct')")
    # point number
    h = rep(h, '>נקודה ${j+1} מתוך ${x.points.length}<', ">${T('נקודה '+(j+1)+' מתוך '+x.points.length,'Point '+(j+1)+' of '+x.points.length)}<")
    # question / options
    h = rep(h, '${heWrap(pt.q)}', "${LANG==='en'?enWrap(E(x,j).q):heWrap(pt.q)}")
    h = rep(h, '${heWrap(pt.options[o])}', "${LANG==='en'?enWrap(E(x,j).o[o]):heWrap(pt.options[o])}")
    # rashi quote: english block + source label
    h = rep(h, '${rashiHTML(x,pt)}<span class="src">בראשית ${gem(x.ch)}:${gem(x.v)} · <a target="_blank" rel="noopener" href="https://www.sefaria.org/Rashi_on_Genesis.${x.ch}.${x.v}.${x.n}?lang=he">ספריא ↗</a></span>',
            '${rashiHTML(x,pt)}${enBlock(x)}<span class="src">${T(\'בראשית \'+gem(x.ch)+\':\'+gem(x.v),\'Genesis \'+x.ch+\':\'+x.v)} · <a target="_blank" rel="noopener" href="https://www.sefaria.org/Rashi_on_Genesis.${x.ch}.${x.v}.${x.n}?lang=${LANG===\'en\'?\'bi\':\'he\'}">${T(\'ספריא\',\'Sefaria\')} ↗</a></span>')
    # done screen
    h = rep(h, "'<section class=\"card done\"><h2>סליק פרשת %s</h2><p>סיימת '+s.done+' מתוך '+DATA.length+' רש״יות · '+s.נכון+' מתוך '+s.pts+' נכון.</p>'+" % he,
            "'<section class=\"card done\"><h2>'+T('סליק פרשת %s','Finished Parshas %s')+'</h2><p>'+T('סיימת '+s.done+' מתוך '+DATA.length+' רש״יות · '+s.נכון+' מתוך '+s.pts+' נכון.','You finished '+s.done+' of '+DATA.length+' Rashis · '+s.נכון+' of '+s.pts+' correct.')+'</p>'+" % (he, en))
    h = rep(h, "'<p>'+skipped.length+' רש״יות not finished. <button class=\"ghost\" id=\"gs\" type=\"button\">עבור אל first one</button></p>'",
            "'<p>'+skipped.length+T(' רש״יות לא הושלמו. ',' Rashis not finished. ')+'<button class=\"ghost\" id=\"gs\" type=\"button\">'+T('עבור אל הראשונה','Go to the first one')+'</button></p>'")
    h = rep(h, "'<p>'+missed.length+' רש״יות לחזרה: '+", "'<p>'+missed.length+T(' רש״יות לחזרה: ',' Rashis to review: ')+")
    h = rep(h, '<button class="btn sec" id="back" type="button">חזור →</button></div></section>', "<button class=\"btn sec\" id=\"back\" type=\"button\">'+T('חזור →','← Back')+'</button></div></section>")
    # nav
    h = rep(h, '${st.i===0?\'disabled\':\'\'}>חזור →</button>', "${st.i===0?'disabled':''}>${T('חזור →','← Back')}</button>")
    h = rep(h, "${all?'רש״י הבא ←':(ans?'נקודה הבאה ←':'ענה כדי להמשיך')}", "${all?T('רש״י הבא ←','Next Rashi →'):(ans?T('נקודה הבאה ←','Next point →'):T('ענה כדי להמשיך','Answer to continue'))}")
    # pasuk english
    h = rep(h, '<div class="pasuk" lang="he">${x.pasuk_html}</div>', '<div class="pasuk" lang="he">${x.pasuk_html}${LANG===\'en\'&&EN[x.id]&&EN[x.id].pe?`<div class="pen" lang="en">${esc(EN[x.id].pe)}</div>`:\'\'}</div>')
    # keyboard: ignore keys pressed on footer controls
    h = rep(h, "if(e.target.tagName==='SELECT'||e.metaKey", "if(e.target.tagName==='SELECT'||(e.target.closest&&e.target.closest('.hint'))||e.metaKey")
    # footer
    h = rep(h, "h.innerHTML='<span>בראשית '+x.ch+':'+x.v+' · '+gem(x.ch)+':'+gem(x.v)+'</span><span>רש״י '+x.n+' מתוך '+on+' על פסוק זה · #'+(st.i+1)+'</span><span>'+esc(c)+'</span><span>מקשים: 1-3 לתשובה · Enter להבא · ← / → לניווט</span>'",
            "h.innerHTML='<span>'+T('בראשית '+x.ch+':'+x.v+' · '+gem(x.ch)+':'+gem(x.v),'Genesis '+x.ch+':'+x.v)+'</span><span>'+T('רש״י '+x.n+' מתוך '+on+' על פסוק זה · #'+(st.i+1),'Rashi '+x.n+' of '+on+' on this verse · #'+(st.i+1))+'</span><span>'+esc(c)+'</span><span>'+T('מקשים: 1-3 לתשובה · Enter להבא · ← / → לניווט','Keys: 1-3 to answer · Enter for next · ← / → to navigate')+'</span>'")
    h = rep(h, ">משוב / Feedback</a></span>')}", ">'+T('משוב / Feedback','Feedback')+'</a></span>');\n  const chs=[...new Set(DATA.map(y=>y.ch))];\n  h.insertAdjacentHTML('beforeend','<span><button class=\"ghost\" id=\"langBtn\" type=\"button\">'+T('English','עברית')+'</button> <select id=\"prSel\" aria-label=\"print range\"><option value=\"all\">'+T('הכל','Whole parsha')+'</option>'+chs.map(c=>'<option value=\"'+c+'\"'+(String(window._prSel)===String(c)?' selected':'')+'>'+T('פרק '+gem(c),'Chapter '+c)+'</option>').join('')+'</select> <button class=\"ghost\" id=\"printBtn\" type=\"button\">'+T('הדפסה + מפתח תשובות','Print test + answer key')+'</button></span>');\n  if(LANG==='en')h.insertAdjacentHTML('beforeend','<span>English: Metsudah Chumash &amp; Rashi (via Sefaria, CC-BY)</span>')}")
    # init
    h = rep(h, "if(document.fonts)document.fonts.ready.then(refit);\nrender();", "if(document.fonts)document.fonts.ready.then(refit);\napplyLang();\nrender();")
    open(f, 'w', encoding='utf-8', newline='').write(h)
    print('patched', f, len(EN)); done += 1
print(done)
