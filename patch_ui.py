import glob,re
JS = r'''function rashiHTML(x,pt){
  const nz=w=>w.replace(/[֑-ׇ]/g,'').replace(/[^א-ת]/g,'');
  const toks=String(x.rashi_he).replace(/<\/?b>/g,'').split(/\s+/).filter(Boolean),n=toks.map(nz);
  const cls=toks.map(()=>'');
  const dh=x.dh.split(/\s+/).map(nz).filter(Boolean);
  let dl=0;if(dh.length&&dh.every((w,i)=>n[i]===w))dl=dh.length;else{let k=0;while(k<dh.length&&k<n.length&&n[k]===dh[k])k++;dl=k}
  for(let i=0;i<dl;i++)cls[i]+=' dhw';
  const pw=x.pasuk_html.replace(/<[^>]+>/g,'').replace(/־/g,' ').split(/\s+/).map(nz).filter(Boolean);
  for(let i=dl;i<n.length;i++){let best=0;for(let p=0;p<pw.length;p++){let k=0;while(i+k<n.length&&p+k<pw.length&&n[i+k]&&n[i+k]===pw[p+k])k++;if(k>best)best=k}
    if(best>=2){for(let k=0;k<best;k++)cls[i+k]+=' qw';i+=best-1}}
  if(pt&&pt.kp){const kw=String(pt.kp).split(/\s+/).map(nz).filter(Boolean);
    if(kw.length)for(let i=0;i+kw.length<=n.length;i++){if(kw.every((w,k)=>n[i+k]===w)){for(let k=0;k<kw.length;k++)cls[i+k]+=' kp';break}}}
  return toks.map((t,i)=>cls[i]?`<span class="${cls[i].trim()}">${esc(t)}</span>`:esc(t)).join(' ')}
'''
CSS = '''.quote .dhw{font-weight:700}
.quote .qw{text-decoration:underline dotted;text-underline-offset:4px}
.quote .kp{background:var(--mark);color:var(--mark-ink);border-radius:4px;padding:0 2px}
.quote .src{display:block;direction:rtl;font-family:var(--f-ui);font-size:12px;color:var(--muted);margin-top:4px}
.quote .src a{color:var(--accent);font-weight:600;text-decoration:none}
'''
for fn in glob.glob('Rashi-*.html'):
    s=open(fn,encoding='utf-8',newline='').read()
    m=re.search(r"    \$\{v!==undefined\?`<div class=\"cite\">.*?</div><div class=\"quote\" lang=\"he\">\$\{x\.rashi_he\}</div>`:''\}",s)
    assert m,fn
    new="    ${v!==undefined?`<div class=\"quote\" lang=\"he\">${rashiHTML(x,pt)}<span class=\"src\">בראשית ${gem(x.ch)}:${gem(x.v)} · <a target=\"_blank\" rel=\"noopener\" href=\"https://www.sefaria.org/Rashi_on_Genesis.${x.ch}.${x.v}.${x.n}?lang=he\">ספריא ↗</a></span></div>`:''}"
    s=s[:m.start()]+new+s[m.end():]
    s=s.replace("function pointHTML(",JS+"function pointHTML(",1)
    s=s.replace(".cite a:hover{text-decoration:underline}",".cite a:hover{text-decoration:underline}\n"+CSS,1)
    s=s.replace(".pasuk{font-family:var(--f-heb);font-size:22px;line-height:1.55;",".pasuk{font-family:var(--f-heb);font-size:22px;line-height:1.7;letter-spacing:.03em;word-spacing:.08em;",1)
    open(fn,'w',encoding='utf-8',newline='').write(s)
    print(fn,'ok')
