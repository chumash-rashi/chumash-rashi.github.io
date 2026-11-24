#!/bin/bash
# usage: run_parsha.sh name
export PYTHONIOENCODING=utf-8
python gen_quiz_cli.py $1 && python - <<PY
import json,re
strip=lambda s: re.sub(r'[֑-ׇ]','',re.sub(r'</?mark>','',s))
nz=lambda s:' '.join(re.sub(r'[^א-ת ]','',strip(s).replace('־',' ')).split())
sk={x['id']:x for x in json.load(open('_sef/$1_skeleton.json',encoding='utf-8'))}
q=json.load(open('_sef/$1_quiz.json',encoding='utf-8'))
for i,o in q.items():
    r=nz(sk[i]['rashi_he'])
    for p in o['points']: p['kp']=[k for k in p.get('kp',[]) if nz(k) and nz(k) in r]
json.dump(q,open('_sef/$1_quiz.json','w',encoding='utf-8'),ensure_ascii=False)
PY
python gen_niqqud_cli.py $1 && python gen_trans_cli.py $1 $2 && echo ALLDONE
