"""Independent raw-PCAP-to-saved-classification lockstep verification."""
import importlib.util,json,zipfile,xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('ec',B/'append_event_classification.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def val(c):return ''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext(ns+'v','')
with zipfile.ZipFile(m.OUT) as z:
 w=E.fromstring(z.read('xl/workbook.xml'));r=E.fromstring(z.read('xl/_rels/workbook.xml.rels'));rid=next(x.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') for x in w.find(ns+'sheets') if x.get('name')=='Event classification');target=next(x.get('Target') for x in r if x.get('Id')==rid);part='xl/'+target; rows=E.iterparse(z.open(part),events=('end',));it=(n for e,n in rows if n.tag==ns+'row');header=[val(c) for c in next(it)];assert header==m.H
 actual=[]
 for n in it:actual.append([val(c) for c in n]);n.clear()
assert len(actual)==359233
i=0;counts=Counter()
for d,p,paths in m.captures():
 org,disp=m.origin(d,paths);state={}
 for ordinal,(ts,frame) in enumerate(m.read_pcap(str(p)),1):
  expected=[str(x) for x in m.values(d,org,disp,ordinal,ts,frame,state)];got=actual[i];assert len(got)==19 and got==expected,(i+2,d,ordinal);counts[(got[15],got[16])]+=1;i+=1
out={'rows':i,'header_exact':True,'every_row_exact_raw_reconciliation':True,'class_status_counts':{f'{a}|{b}':n for (a,b),n in sorted(counts.items())}}
(B/'EVENT_CLASSIFICATION_SAVED_VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
