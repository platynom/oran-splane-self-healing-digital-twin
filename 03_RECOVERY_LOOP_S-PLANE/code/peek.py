import json,sys
O=sys.argv[1]
tl=json.load(open(O+'/timeline.json')); t0=tl['t0_mono']
for l in open(O+'/loop.jsonl'):
    d=json.loads(l)
    if d['kind']=='eval':
        if d.get('verdict')!='BENIGN' or d.get('violations'): print('E',round(d['t_mono']-t0,1),d.get('verdict'),d.get('hint'),d.get('n'),list(d.get('violations',{}).items())[:2])
    elif d['kind'] not in ('start',):
        print('*',round(d['t_mono']-t0,1),d['kind'],{k:v for k,v in d.items() if k in('action','target','ok','detail','reason','actions','escalations','standby_active')})
rows=[json.loads(l) for l in open(O+'/observer.jsonl')]
last={}
for r in rows:
    key=(r.get('portState'),r.get('parentPortIdentity'),r.get('grandmasterIdentity'))
    if last.get(r['node'])!=key:
        print('O',r['node'],round(r['t']-t0,1),key); last[r['node']]=key
