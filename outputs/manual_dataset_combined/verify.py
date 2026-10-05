import json, zipfile, re, math, hashlib, csv
import xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from itertools import zip_longest

B=Path(__file__).resolve().parent; ROOT=B.parents[1]
m=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
report=[]; seen=Counter(); totalcells=0
def expected(s):
    yield s['headers']
    for fn in s['parts']:
        p=json.loads((B/fn).read_text(encoding='utf-8'))
        yield from p['rows']
def actual(z,path,n):
    with z.open(path) as f:
        for _,e in E.iterparse(f,events=['end']):
            if e.tag!=NS+'row':continue
            row=[None]*n
            for c in e:
                ref=c.get('r'); letters=re.match('[A-Z]+',ref)[0]; col=0
                for x in letters:col=col*26+ord(x)-64
                v=c.find(NS+'v');t=c.get('t')
                if t=='inlineStr':val=''.join(c.itertext())
                elif v is None:val=None
                elif t in ['str','s']:val=v.text or ''
                elif t=='b':val=v.text=='1'
                elif t=='e':raise AssertionError('Excel error '+str(v.text))
                else:
                    text=v.text or ''
                    val=float(text) if '.' in text or 'e' in text.lower() else int(text)
                row[col-1]=val
            yield row
            e.clear()

with zipfile.ZipFile(B/'ORAN_All_Current_Datasets.xlsx') as z:
    assert z.testzip() is None
    for i,s in enumerate(m['sheets'],1):
        n=0
        for num,pair in enumerate(zip_longest(expected(s),actual(z,f'xl/worksheets/sheet{i}.xml',s['columns'])),1):
            a,b=pair; assert a is not None and b is not None,(s['name'],'row count',num)
            for j,(x,y) in enumerate(zip(a,b)):
                if isinstance(x,(int,float)) and not isinstance(x,bool):
                    assert isinstance(y,(int,float)) and math.isclose(x,y,rel_tol=2e-15,abs_tol=1e-15),(s['name'],num,j,x,y)
                else:assert x==y,(s['name'],num,j,x,y)
            if num>1 and s['headers'][0]=='Source_ID' and s['name']!='Sources':seen[a[0]]+=1
            n+=1;totalcells+=len(a)
        assert n==s['rows']+1
        report.append([s['name'],n-1,s['columns'],'Every cell matched prepared source data'])
        print('VERIFIED',s['name'],n-1,flush=True)
for sid,path,sheet,n,cols,evidence,dup,sha in m['sources']:
    p=ROOT/path
    assert seen[sid]==n,(sid,seen[sid],n)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,('Source changed',sid)
    with p.open(encoding='utf-8-sig',newline='') as f:
        r=csv.reader(f);hs=next(r);assert len(hs)==cols
        assert sum(1 for _ in r)==n
summary={'data_rows':sum(seen.values()),'sources':len(seen),'sheets':len(m['sheets']),'cells_compared':totalcells,'checks':report}
(B/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('ALL VERIFIED',summary['data_rows'],summary['cells_compared'],flush=True)
