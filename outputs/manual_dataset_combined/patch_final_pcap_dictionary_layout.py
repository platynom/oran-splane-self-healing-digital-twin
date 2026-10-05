"""Patch only the final workbook's PCAP dictionary layout, preserving data sheets."""
import hashlib,json,shutil,tempfile,zipfile,xml.etree.ElementTree as E
from pathlib import Path
B=Path(__file__).resolve().parent; P=B/'ORAN_All_Current_Datasets_FINAL_PCAP.xlsx'; T=B/'ORAN_All_Current_Datasets_FINAL_PCAP.layout_tmp.xlsx'; NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'; ns='{'+NS+'}'; RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
def h(b): return hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(P) as z:
 before={n:h(z.read(n)) for n in z.namelist() if n.startswith('xl/worksheets/')}
 wb=E.fromstring(z.read('xl/workbook.xml')); rel=E.fromstring(z.read('xl/_rels/workbook.xml.rels')); rid=next(x.get(RNS+'id') for x in wb.find(ns+'sheets') if x.get('name')=='PCAP dictionary'); target=next(x.get('Target') for x in rel if x.get('Id')==rid); part='xl/'+target.lstrip('/') if not target.startswith('/xl/') else target.lstrip('/')
 sheet=E.fromstring(z.read(part)); styles=E.fromstring(z.read('xl/styles.xml')); xfs=styles.find(ns+'cellXfs'); top_id=str(len(xfs)); base=E.fromstring(E.tostring(xfs[6])); align=base.find(ns+'alignment'); align.set('vertical','top'); base.set('applyAlignment','1'); xfs.append(base); xfs.set('count',str(len(xfs)))
 for row in sheet.find(ns+'sheetData'):
  if row.get('r')=='1': continue
  vals=[''.join(c.itertext()) for c in row]
  row.set('ht','135' if vals and vals[0] in ('MessageType','Source') else '90'); row.set('customHeight','1')
  for c in row: c.set('s',top_id)
 with zipfile.ZipFile(T,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as out:
  for i in z.infolist():
   if i.filename==part: out.writestr(i,E.tostring(sheet,encoding='utf-8',xml_declaration=True))
   elif i.filename=='xl/styles.xml': out.writestr(i,E.tostring(styles,encoding='utf-8',xml_declaration=True))
   else: out.writestr(i,z.read(i.filename))
with zipfile.ZipFile(T) as z:
 assert z.testzip() is None
 after={n:h(z.read(n)) for n in z.namelist() if n.startswith('xl/worksheets/')}
 assert all(before[n]==after[n] for n in before if n!=part)
 assert after[part]!=before[part]
shutil.move(T,P)
out={'workbook_sha256':h(P.read_bytes()),'modified_parts':[part,'xl/styles.xml'],'unchanged_worksheet_parts':len(before)-1,'dictionary_top_alignment_style':top_id,'message_type_height':135,'source_height':135,'zip_integrity':True}
(B/'FINAL_PCAP_GUIDE_PATCH_VERIFICATION.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); print(json.dumps(out))
