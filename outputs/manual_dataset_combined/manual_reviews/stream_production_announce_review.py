"""Stream exact CSV cells into the bounded review workbook and verify it."""
from __future__ import annotations
import csv, hashlib, json, re, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

B=Path(__file__).resolve().parent; ROOT=B.parents[2]
P=json.loads((B/'01_production_announce_plan.json').read_text())
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
RAW=ROOT/P['raw']; LAB=ROOT/P['labels']
CODE={'Sync':'0','Delay_Req':'1','PDelay_Req':'2','PDelay_Resp':'3','Follow_Up':'8','Delay_Resp':'9','PDelay_Resp_Follow_Up':'10','Announce':'11','Signaling':'12','Management':'13'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def col(n):
 s=''
 while n: n,k=divmod(n-1,26);s=chr(65+k)+s
 return s
def cell(ref,v,style): return f'<x:c r="{ref}" s="{style}" t="inlineStr"><x:is><x:t xml:space="preserve">{escape(v)}</x:t></x:is></x:c>'
def endpoint_map():
 endpoints={}
 with RAW.open(encoding='utf-8-sig',newline='') as f:
  rows=csv.reader(f);next(rows)
  cached=list(rows)
 for pos in (1,2):
  for raw in cached:
   if raw[pos] not in endpoints: endpoints[raw[pos]]=str(len(endpoints))
 return endpoints
def projection_ok(raw,labeled,previous_time,endpoints):
 expected=0.0 if previous_time is None else float(raw[0])-float(previous_time)
 return (labeled[0]==endpoints[raw[1]] and labeled[1]==endpoints[raw[2]] and labeled[2]==raw[4] and labeled[3]==raw[5] and labeled[4]==CODE.get(raw[6],raw[6]) and abs(float(labeled[5])-expected)<1e-12)
def assemble():
 with zipfile.ZipFile(B/'01_PRODUCTION_ANNOUNCE_TEMPLATE.xlsx') as src,zipfile.ZipFile(B/'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW.xlsx','w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for item in src.infolist():
   if item.filename!='xl/worksheets/sheet3.xml': out.writestr(item,src.read(item.filename));continue
   xml=src.read(item.filename).decode();before,rest=xml.split('<x:sheetData>',1);body,after=rest.split('</x:sheetData>',1);rows=re.findall(r'<x:row\b.*?</x:row>',body,re.S);header=rows[0];sample=ET.fromstring('<x:r xmlns:x="'+NS+'">'+rows[1]+'</x:r>')[0];styles={re.sub(r'\d','',c.get('r')):c.get('s','0') for c in sample};end=f'{col(len(P["raw_headers"])+len(P["label_headers"])+7)}{P["rows"]+1}';before=re.sub(r'<x:dimension[^>]*/>','',before);i=before.index('>',before.index('<x:worksheet'))+1;before=before[:i]+f'<x:dimension ref="A1:{end}"/>'+before[i:];after=re.sub(r'<x:autoFilter[^>]*/>|<x:autoFilter.*?</x:autoFilter>','',after,flags=re.S)
   with out.open(item.filename,'w') as dest,RAW.open(encoding='utf-8-sig',newline='') as rf,LAB.open(encoding='utf-8-sig',newline='') as lf:
    dest.write((before+'<x:sheetData>'+header).encode());rr=csv.reader(rf);lr=csv.reader(lf);next(rr);next(lr)
    endpoints=endpoint_map();previous=None
    for record,(raw,labeled) in enumerate(zip(rr,lr),1):
     assert projection_ok(raw,labeled,previous,endpoints);previous=raw[0];vals=raw+labeled+[P['raw_sha256'],P['label_sha256'],str(record),'EXACT_DECODER_PROJECTION_LINKED','Supplied packet annotation; semantics unvalidated','Unknown from this row alone','Not established; no verified physical action'];idx=record+1;dest.write((f'<x:row r="{idx}" ht="30" customHeight="1">'+''.join(cell(f'{col(j)}{idx}',v,styles.get(col(j),'0')) for j,v in enumerate(vals,1))+'</x:row>').encode())
    dest.write((f'</x:sheetData><x:autoFilter ref="A1:{end}"/>'+after).encode())
def verify():
 result={'raw_sha256':sha(RAW),'label_sha256':sha(LAB),'rows':0,'raw_source_cells_verified':0,'label_source_cells_verified':0,'original_cells_verified':0,'label_alignment_verified':True,'zip_integrity':False}
 with zipfile.ZipFile(B/'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW.xlsx') as z,RAW.open(encoding='utf-8-sig',newline='') as rf,LAB.open(encoding='utf-8-sig',newline='') as lf:
  result['zip_integrity']=z.testzip() is None;rr=csv.reader(rf);lr=csv.reader(lf);headers=next(rr);next(lr)
  endpoints=endpoint_map();previous=None
  for _,node in ET.iterparse(z.open('xl/worksheets/sheet3.xml'),events=('end',)):
   if node.tag!='{'+NS+'}row': continue
   got=[''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('{'+NS+'}v','') for c in node]
   if result['rows']==0: assert got[:len(headers)]==headers and got[len(headers):len(headers)+len(P['label_headers'])]==[f'S026 {x}' for x in P['label_headers']]
   else:
    raw=next(rr);lab=next(lr);assert projection_ok(raw,lab,previous,endpoints) and got[:len(headers)]==raw and got[len(headers):len(headers)+len(lab)]==lab;previous=raw[0];result['raw_source_cells_verified']+=len(headers);result['label_source_cells_verified']+=len(lab);result['original_cells_verified']+=len(headers)+len(lab)
   result['rows']+=1;node.clear()
  assert result['rows']-1==P['rows'] and next(rr,None) is None and next(lr,None) is None
 result['rows']-=1;result['workbook_sha256']=sha(B/'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW.xlsx')
 with zipfile.ZipFile(B/'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW.xlsx') as z:
  sheet=z.read('xl/worksheets/sheet3.xml').decode();book=ET.fromstring(z.read('xl/workbook.xml'))
  result.update({'sheet_count':len(book.findall('{'+NS+'}sheets/{'+NS+'}sheet')),'all_records_dimension':re.search(r'<x:dimension ref="([^"]+)',sheet).group(1),'all_records_filter':re.search(r'<x:autoFilter ref="([^"]+)',sheet).group(1),'all_records_frozen_top_row':'ySplit="1"' in sheet,'bounded_render_check':'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW_render_check.json'})
 (B/'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__': {'assemble':assemble,'verify':verify}[__import__('sys').argv[1]]()
