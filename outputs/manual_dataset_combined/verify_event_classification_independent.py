"""Independent raw-byte count verifier; intentionally does not import classifier helpers."""
import csv,hashlib,json,struct,zipfile,xml.etree.ElementTree as E
from collections import Counter,defaultdict
from pathlib import Path
B=Path(__file__).resolve().parent;ROOT=B.parents[1];P=B/'ORAN_All_Current_Datasets_FINAL_PCAP_v2_CLASSIFIED.xlsx';ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def h(p):
 x=hashlib.sha256();x.update(p.read_bytes());return x.hexdigest()
def pc(p):
 with p.open('rb') as f:
  g=f.read(24);magic=struct.unpack_from('<I',g)[0];nano=magic in (0xA1B23C4D,0x4D3CB2A1)
  while r:=f.read(16):
   sec,frac,n,*_=struct.unpack('<IIII',r);data=f.read(n);yield data
a=json.loads((B/'source_traceability_audit.json').read_text());g=defaultdict(list)
for x in a['external_inventory']:
 if x.get('suffix')=='.pcap':g[x['sha256']].append(x['path'])
expected=Counter()
for digest,paths in g.items():
 state={}
 for fr in pc(ROOT/paths[0]):
  if len(fr)<14 or fr[12:14]!=b'\x88\xf7':expected[('NOT_APPLICABLE','NOT_APPLICABLE')]+=1;continue
  q=fr[14:]
  if len(q)<34:expected[('UNKNOWN','UNKNOWN_INSUFFICIENT_ANNOUNCE')]+=1;continue
  typ=q[0]&15
  if typ!=11:expected[('NOT_APPLICABLE','NOT_APPLICABLE')]+=1;continue
  if (q[1]&15)!=2 or int.from_bytes(q[2:4],'big')<64 or int.from_bytes(q[2:4],'big')>len(q):expected[('UNKNOWN','UNKNOWN_INSUFFICIENT_ANNOUNCE')]+=1;continue
  ctx=(digest,q[0]>>4,q[1]&15,q[4],q[20:30]);cur=(q[53:61],(q[47],q[48],q[49],int.from_bytes(q[50:52],'big'),q[52],int.from_bytes(q[61:63],'big'),q[63]));old=state.get(ctx);state[ctx]=cur
  if old is None:expected[('NO_PREVIOUS_OBSERVATION','NO_PREVIOUS_OBSERVATION')]+=1
  elif old==cur:expected[('C0','VALID_COMPARABLE_ANNOUNCE')]+=1
  elif old[0]!=cur[0] and old[1]==cur[1]:expected[('C1','VALID_COMPARABLE_ANNOUNCE')]+=1
  elif old[0]==cur[0]:expected[('C2','VALID_COMPARABLE_ANNOUNCE')]+=1
  else:expected[('C3','VALID_COMPARABLE_ANNOUNCE')]+=1
with zipfile.ZipFile(P) as z:
 w=E.fromstring(z.read('xl/workbook.xml'));r=E.fromstring(z.read('xl/_rels/workbook.xml.rels'));rid=next(x.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') for x in w.find(ns+'sheets') if x.get('name')=='Event classification');tar=next(x.get('Target') for x in r if x.get('Id')==rid);actual=Counter()
 for e,n in E.iterparse(z.open('xl/'+tar),events=('end',)):
  if n.tag==ns+'row' and n.get('r')!='1':v=[''.join(c.itertext()) for c in n];actual[(v[15],v[16])]+=1;n.clear()
assert actual==expected,(actual,expected)
out={'independent_raw_byte_class_status_counts':{f'{a}|{b}':n for (a,b),n in sorted(expected.items())},'matches_saved_output':True};(B/'EVENT_CLASSIFICATION_INDEPENDENT_VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
