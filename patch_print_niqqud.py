"""Print test: vowel the Rashi headings (dibbur hamaschil) and labels; enlarge the on-screen footer ~30%. Idempotent."""
import glob, re, io

VDH = r'''/*VDH*/
const VDICT={'הוא':'הוּא','היא':'הִיא','לו':'לוֹ','וגו׳':'וְגוֹ׳',"וגו'":'וְגוֹ׳','וגומר':'וְגוֹמֵר','ההיא':'הַהִיא','כל':'כֹּל','טוב':'טוֹב','מאה':'מֵאָה','מאוד':'מְאֹד','סדום':'סְדֹם','אורח':'אֹרַח',"לה'":'לַה׳','אותה':'אוֹתָהּ','חלילה':'חָלִילָה','יושב':'יוֹשֵׁב','עושה':'עֹשֶׂה','לדרוש':'לִדְרֹשׁ','חום':'חֹם','כחום':'כְּחֹם','באלוני':'בְּאֵלֹנֵי','לספוד':'לִסְפֹּד','ולבכותה':'וְלִבְכֹּתָהּ','לטושים':'לִטּוּשִׁים','ומגדנות':'וּמִגְדָּנוֹת','בקולי':'בְּקֹלִי','אחזת':'אֲחֻזַּת','תעבורו':'תַּעֲבֹרוּ','ויתרוצצו':'וַיִּתְרֹצֲצוּ','תולדות':'תּוֹלְדֹת','מארצך':'מֵאַרְצְךָ','אראך':'אַרְאֶךָּ','נתת':'נָתַתָּ',"בה'":'בַּה׳',"וה'":'וַה׳','ולרבקה':'וּלְרִבְקָה','ארץ':'אֶרֶץ','וגו':'וְגוֹ׳','סורו':'סוּרוּ','שוב':'שׁוּב'};
function vdh(x){const nz=w=>w.replace(/[֑-ׇ]/g,'').replace(/[^א-ת]/g,'');const loose=k=>k.replace(/[וי]/g,'');
  const strip=t=>t.replace(/[֑-ֽ֯׀׃-ׅ]/g,'').replace(/[^א-תְ-ׇ]/g,'');
  const m={},l={};const src=(x.pasuk_html.replace(/<[^>]+>/g,'').replace(/־/g,' ')+' '+String(x.rashi_he).replace(/<[^>]+>/g,'')).split(/\s+/);
  src.forEach(t=>{const s=strip(t),k=nz(t);if(k&&/[ְ-ֻ]/.test(s)){if(!m[k])m[k]=s;const q=loose(k);if(q&&!l[q])l[q]=s}});
  return x.dh.split(/\s+/).map(w=>{const k=nz(w);if(!k)return w;if(VDICT[w])return VDICT[w];if(VDICT[k])return VDICT[k];return m[k]||l[loose(k)]||w}).join(' ')}
const LBL={'בראשית':'בְּרֵאשִׁית','רש״י ד״ה ':'רַשִׁ״י דִּבּוּר הַמַּתְחִיל ','רש״י על פרשת ':'רַשִׁ״י עַל פָּרָשַׁת ','פרק':'פֶּרֶק','שם:':'שֵׁם:','תאריך:':'תַּאֲרִיךְ:','ציון:':'צִיּוּן:','מפתח תשובות':'מַפְתֵּחַ תְּשׁוּבוֹת'};
const PNV={'תולדות':'תּוֹלְדֹת','חיי שרה':'חַיֵּי שָׂרָה','לך לך':'לֶךְ לְךָ','וירא':'וַיֵּרָא','ויצא':'וַיֵּצֵא'};
'''
files = sorted(glob.glob('Rashi-*.html'))
for f in files:
    h = io.open(f, encoding='utf-8', newline='').read()
    o = h
    if '/*VDH*/' not in h:
        h = h.replace('function buildPrint(sel)', VDH + 'function buildPrint(sel)', 1)
        h = h.replace("'<span lang=\"he\" dir=\"rtl\">'+esc(x.dh)+'</span>", "'<span lang=\"he\" dir=\"rtl\">'+esc(vdh(x))+'</span>")
        h = h.replace("T('בראשית '+gem(x.ch)", "T(LBL['בראשית']+' '+gem(x.ch)")
        h = h.replace("(en?'Rashi on ':'רש״י ד״ה ')", "(en?'Rashi on ':LBL['רש״י ד״ה '])")
        h = h.replace("'רש״י על פרשת '+PNAME[0]", "LBL['רש״י על פרשת ']+(PNV[PNAME[0]]||PNAME[0])")
        h = h.replace("' — פרק '+gem(+sel)", "' — '+LBL['פרק']+' '+gem(+sel)")
        h = h.replace("T('שם: ______________________'", "T(LBL['שם:']+' ______________________'")
        h = h.replace("T('תאריך: ____________'", "T(LBL['תאריך:']+' ____________'")
        h = h.replace("T('ציון: ______ / '+qn", "T(LBL['ציון:']+' ______ / '+qn")
        h = h.replace("T('מפתח תשובות','Answer Key')", "T(LBL['מפתח תשובות'],'Answer Key')")
    # footer ~30% bigger
    h = h.replace('.hint{font-size:11px;color:var(--muted)', '.hint{font-size:14px;color:var(--muted)')
    h = h.replace('.hint{font-size:11px;display:flex', '.hint{font-size:14px;display:flex')
    h = h.replace('.hint .ghost{padding:2px 8px;font-size:11px}', '.hint .ghost{padding:3px 10px;font-size:14px}')
    h = h.replace('.hint select{font-size:11px;padding:2px 4px}', '.hint select{font-size:14px;padding:3px 5px}')
    if h != o:
        io.open(f, 'w', encoding='utf-8', newline='').write(h); print('patched', f)
