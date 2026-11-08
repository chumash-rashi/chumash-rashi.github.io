"""Declutter the quiz card and auto-size fonts so each question fits without scrolling."""
import glob

CSS = """
/* fit layout: only pasuk + question + options in the card; fine print lives in the footer */
.wrap{max-width:min(1100px,100%)}
header .top,.tools,.ref,.dh{display:none}
.card{gap:calc(var(--s,1)*8px)}
.pasuk{font-size:calc(var(--s,1)*22px)}
.q{font-size:calc(var(--s,1)*18px)}
.opt{font-size:calc(var(--s,1)*17px);padding:calc(var(--s,1)*7px) calc(var(--s,1)*10px)}
.opt .k{width:calc(var(--s,1)*20px);height:calc(var(--s,1)*20px);font-size:calc(var(--s,1)*11px)}
.row p{font-size:calc(var(--s,1)*16px)}
.verdict{font-size:calc(var(--s,1)*16px)}
.point{gap:calc(var(--s,1)*10px)}
.reveal{gap:calc(var(--s,1)*8px)}
@media (max-width:460px){.pasuk{font-size:calc(var(--s,1)*22px)}}
.hint{font-size:11px;display:flex;flex-wrap:wrap;gap:4px 12px;justify-content:center}
"""

JS = """
function foot(){const h=document.querySelector('.hint');const x=DATA[st.i];
  const c=$('count').textContent;
  if(!x){h.textContent=c;return}
  const on=DATA.filter(y=>y.ch===x.ch&&y.v===x.v).length;
  h.innerHTML='<span>בראשית '+x.ch+':'+x.v+' · '+gem(x.ch)+':'+gem(x.v)+'</span><span>רש״י '+x.n+' מתוך '+on+' על פסוק זה · #'+(st.i+1)+'</span><span>'+esc(c)+'</span><span>מקשים: 1-3 לתשובה · Enter להבא · ← / → לניווט</span>'}
function fit(){const c=document.querySelector('.card');if(!c)return;const r=document.documentElement;
  let lo=.6,hi=2.6;for(let i=0;i<9;i++){const m=(lo+hi)/2;r.style.setProperty('--s',m);if(c.scrollHeight>c.clientHeight+1)hi=m;else lo=m}
  r.style.setProperty('--s',lo)}
const _render=render;render=function(){_render();foot();fit()};
addEventListener('resize',fit);
"""

for f in glob.glob('Rashi-*.html'):
    t = open(f, encoding='utf-8').read()
    if 'fit layout' in t:
        continue
    i = t.index('</style>', t.index('.done p{'))
    t = t[:i] + CSS + t[i:]
    j = t.rindex('render();\n</script>')
    t = t[:j] + JS + t[j:]
    open(f, 'w', encoding='utf-8', newline='').write(t)
    print('patched', f)
