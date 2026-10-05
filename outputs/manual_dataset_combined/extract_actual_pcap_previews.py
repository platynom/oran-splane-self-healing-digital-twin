"""Extract bounded, literal saved-workbook samples for render QA."""
import json, zipfile, xml.etree.ElementTree as E
from pathlib import Path
B=Path(__file__).resolve().parent; p=B/'ORAN_All_Current_Datasets_FINAL_PCAP.xlsx'; ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
def text(c): return ''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext(ns+'v','')
def sheetpart(z,name):
 w=E.fromstring(z.read('xl/workbook.xml')); rel=E.fromstring(z.read('xl/_rels/workbook.xml.rels')); rid=next(x.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') for x in w.find(ns+'sheets') if x.get('name')==name); target=next(x.get('Target') for x in rel if x.get('Id')==rid); return 'xl/'+target.lstrip('/') if not target.startswith('/xl/') else target.lstrip('/')
def extract(z,name,wanted):
 x=E.fromstring(z.read(sheetpart(z,name))); data=x.find(ns+'sheetData'); rows=[]
 for r in data:
  vals=[{'v':text(c),'s':c.get('s','0'),'r':c.get('r')} for c in r]
  if r.get('r') in wanted or (vals and vals[0]['v'] in wanted): rows.append({'r':r.get('r'),'ht':r.get('ht','15'),'cells':vals})
 return {'sheet':name,'cols':[c.attrib for c in x.find(ns+'cols')], 'rows':rows}
with zipfile.ZipFile(p) as z:
 d=extract(z,'PCAP dictionary',{'1','PTP originTimestamp ns (derived)','Packet ordinal (derived)','Captured frame length bytes (derived)','EtherType (derived)','PTP flags hex (derived)','PTP source port (derived)','Source','MessageType'})
 q=extract(z,'PCAP 0690ed95ddc3',{'1','2','3','4'})
 # include first actual event row, preserving exact workbook record values.
 for r in E.fromstring(z.read(sheetpart(z,'PCAP 0690ed95ddc3'))).find(ns+'sheetData'):
  vals=[{'v':text(c),'s':c.get('s','0'),'r':c.get('r')} for c in r]
  if len(vals)>33 and vals[33]['v']!='NONE': q['rows'].append({'r':r.get('r'),'ht':r.get('ht','15'),'cells':vals}); break
(B/'actual_saved_preview_data.json').write_text(json.dumps({'dictionary':d,'production':q},indent=2),encoding='utf8')
print('dictionary_rows',len(d['rows']),'production_rows',len(q['rows']))
