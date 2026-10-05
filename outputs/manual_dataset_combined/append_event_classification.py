"""Append deterministic, capture-local Announce advertisement classifications."""
from __future__ import annotations
import hashlib,json,re,sys,zipfile,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from xml.sax.saxutils import escape
B=Path(__file__).resolve().parent; ROOT=B.parents[1]; APP=ROOT/'01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing'; sys.path.insert(0,str(APP))
from ingest.ptp_wire import read_pcap,parse_eth_frame,decode_ptp_payload,MSG_NAME
IN=B/'ORAN_All_Current_Datasets_FINAL_PCAP.xlsx'; OUT=B/'ORAN_All_Current_Datasets_FINAL_PCAP_v2_CLASSIFIED.xlsx'; AUDIT=B/'source_traceability_audit.json'; NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'; REL='http://schemas.openxmlformats.org/package/2006/relationships'; OFF='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
H=['Canonical capture SHA256','Origin','Disposition / quarantine','Packet ordinal','Capture timestamp ns','PTP message type','transportSpecific','PTP version','PTP domain','sourcePortIdentity','Previous comparable Announce ordinal','Previous grandmasterIdentity','Current grandmasterIdentity','Previous attributes tuple','Current attributes tuple','Observable class','Classification status','Rule reference','Supplied label handling']
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def col(n):
 s=''
 while n:n,k=divmod(n-1,26);s=chr(65+k)+s
 return s
def cell(ref,v,s='0'):
 v='' if v is None else str(v); return f'<c r="{ref}" s="{s}" t="inlineStr"><is><t xml:space="preserve">{escape(v)}</t></is></c>'
def row(n,vs,s='0',ht=30):return f'<row r="{n}" ht="{ht}" customHeight="1">'+''.join(cell(f'{col(i)}{n}',v,s) for i,v in enumerate(vs,1))+'</row>'
def origin(digest,paths):
 t=' '.join(paths).lower()
 if digest.startswith('d2c91b3e'):return 'External TIMESAFE capture','QUARANTINED: conflicting derived annotations; not independent label truth'
 if 'netem' in t:return 'Project software-collected Netem/emulation','SOFTWARE_TESTBED: not physical experiment proof'
 if 'timesafe' in t or 's-plane_security_repo' in t:return 'Associated external TIMESAFE capture','Exact launch/collection linkage unavailable locally'
 return 'Unknown local provenance','Origin not established'
def attrs(m):return (m.grandmaster_priority1,m.grandmaster_clock_class,m.grandmaster_clock_accuracy,m.offset_scaled_log_variance,m.grandmaster_priority2,m.steps_removed,m.time_source)
def classify(previous,context,ordinal,m):
 cur=(m.grandmaster_identity.hex(),attrs(m)); old=previous.get(context)
 if old is None: previous[context]=(ordinal,cur);return 'NO_PREVIOUS_OBSERVATION','NO_PREVIOUS_OBSERVATION','NONE','','',None
 po,(pid,pa)=old; cid,ca=cur; previous[context]=(ordinal,cur)
 if pid==cid and pa==ca:c='C0'; rule='R-CLASS-C0: same advertised identity and attributes'
 elif pid!=cid and pa==ca:c='C1'; rule='R-CLASS-C1: identity changed only'
 elif pid==cid and pa!=ca:c='C2'; rule='R-CLASS-C2: attributes changed only'
 else:c='C3'; rule='R-CLASS-C3: identity and attributes changed'
 return c,'VALID_COMPARABLE_ANNOUNCE',rule,po,pid,pa
def captures():
 a=json.loads(AUDIT.read_text()); g=defaultdict(list)
 for x in a['external_inventory']:
  if x.get('suffix')=='.pcap':g[x['sha256']].append(x['path'])
 out=[]
 for d,paths in sorted(g.items()):
  p=ROOT/paths[0]
  if p.exists() and sha(p)==d:out.append((d,p,paths))
 assert len(out)==14
 return out
def values(digest,org,disp,ordinal,ts,frame,state):
 payload=parse_eth_frame(frame); blank=['']*6; tail=['No label transfer; supplied annotations remain in their source tabs.']
 if payload is None:return [digest,org,disp,ordinal,ts,'NON_PTP','','','','','','','','','','NOT_APPLICABLE','NOT_APPLICABLE','NONE']+tail
 if len(payload)<34:return [digest,org,disp,ordinal,ts,'UNKNOWN','','','','','','','','','','UNKNOWN','UNKNOWN_INSUFFICIENT_ANNOUNCE','R-CLASS-UNKNOWN']+tail
 typ=payload[0]&15; name=MSG_NAME.get(typ,'UNKNOWN'); ctx=(payload[0]>>4,payload[1]&15,payload[4],payload[20:30].hex()); common=[digest,org,disp,ordinal,ts,name,payload[0]>>4,payload[1]&15,payload[4],payload[20:30].hex()]
 if typ!=11:return common+['','','','','','NOT_APPLICABLE','NOT_APPLICABLE','NONE']+tail
 declared=int.from_bytes(payload[2:4],'big'); m=decode_ptp_payload(payload)
 if m is None or declared<64 or declared>len(payload):return common+['','','','','','UNKNOWN','UNKNOWN_INSUFFICIENT_ANNOUNCE','R-CLASS-UNKNOWN: invalid/truncated Announce; state not updated']+tail
 c,status,rule,po,pid,pa=classify(state,ctx,ordinal,m); cid=m.grandmaster_identity.hex(); ca=attrs(m)
 return common+[po,pid,cid,json.dumps(pa) if pa else '',json.dumps(ca),c,status,rule]+tail
def main():
 caps=captures(); counts=Counter(); total=0
 with zipfile.ZipFile(IN) as zin:
  wb=ET.fromstring(zin.read('xl/workbook.xml')); rel=ET.fromstring(zin.read('xl/_rels/workbook.xml.rels')); sheets=wb.find('{%s}sheets'%NS); maxsid=max(int(x.get('sheetId')) for x in sheets); nums=[int(re.search(r'sheet(\d+)\.xml',x.get('Target','')).group(1)) for x in rel if re.search(r'sheet(\d+)\.xml',x.get('Target',''))]; nextnum=max(nums)+1
  with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as zout:
   replaced={'xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml'}
   for i in zin.infolist():
    if i.filename not in replaced:zout.writestr(i,zin.read(i.filename))
   rid='rIdClass1'; part=f'xl/worksheets/sheet{nextnum}.xml'; ET.SubElement(sheets,'{%s}sheet'%NS,{'name':'Event classification','sheetId':str(maxsid+1),'{%s}id'%OFF:rid});ET.SubElement(rel,'{%s}Relationship'%REL,{'Id':rid,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet','Target':f'worksheets/sheet{nextnum}.xml'})
   with zout.open(part,'w') as f:
    widths=''.join(f'<col min="{i}" max="{i}" width="{62 if i in (1,2,3,14,15,18,19) else 28}" customWidth="1"/>' for i in range(1,len(H)+1));f.write(f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{widths}</cols><sheetData>{row(1,H,"5",42)}'.encode())
    for digest,p,paths in caps:
     org,disp=origin(digest,paths); state={}
     for ordinal,(ts,frame) in enumerate(read_pcap(str(p)),1):
      v=values(digest,org,disp,ordinal,ts,frame,state);assert len(v)==len(H); total+=1;counts[(digest,org,disp,v[15],v[16])]+=1;f.write(row(total+1,v).encode())
    f.write(f'</sheetData><autoFilter ref="A1:{col(len(H))}{total+1}"/></worksheet>'.encode())
   # compact guide/counts
   nextnum+=1;rid2='rIdClass2';ET.SubElement(sheets,'{%s}sheet'%NS,{'name':'Classification guide','sheetId':str(maxsid+2),'{%s}id'%OFF:rid2});ET.SubElement(rel,'{%s}Relationship'%REL,{'Id':rid2,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet','Target':f'worksheets/sheet{nextnum}.xml'})
   rows=[['Scope','One output row per packet from 14 canonical PCAP hashes; aliases are not expanded.'],['Class legend','C0 same identity/tuple; C1 identity only; C2 attribute tuple only; C3 both.'],['Attribute tuple','priority1, clockClass, clockAccuracy, offsetScaledLogVariance, priority2, stepsRemoved, timeSource.'],['State','Separate per capture + transportSpecific/version/domain/sourcePortIdentity. Invalid Announce never updates baseline.'],['Limits','Advertisement only. Not maliciousness, healthy/fault, receiver selection, GNSS state, recovery or performed action.'],['Capture SHA256','Origin','Disposition / quarantine','Class','Status','Count']]
   rows += [[d,o,di,c,s,n] for (d,o,di,c,s),n in sorted(counts.items())]
   body=''.join(row(i,r,'5' if i==6 else '10',42 if i==6 else 90) for i,r in enumerate(rows,1));widths='<cols><col min="1" max="1" width="72" customWidth="1"/><col min="2" max="2" width="44" customWidth="1"/><col min="3" max="3" width="68" customWidth="1"/><col min="4" max="4" width="34" customWidth="1"/><col min="5" max="5" width="42" customWidth="1"/><col min="6" max="6" width="18" customWidth="1"/></cols>';zout.writestr(f'xl/worksheets/sheet{nextnum}.xml',f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>{widths}<sheetData>{body}</sheetData><autoFilter ref="A6:F{len(rows)}"/></worksheet>')
   ET.register_namespace('',NS);ET.register_namespace('r',OFF);zout.writestr('xl/workbook.xml',ET.tostring(wb,encoding='utf-8',xml_declaration=True));ET.register_namespace('',REL);zout.writestr('xl/_rels/workbook.xml.rels',ET.tostring(rel,encoding='utf-8',xml_declaration=True));ct=ET.fromstring(zin.read('[Content_Types].xml'));cns='http://schemas.openxmlformats.org/package/2006/content-types';[ET.SubElement(ct,'{%s}Override'%cns,{'PartName':f'/xl/worksheets/sheet{n}.xml','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'}) for n in (nextnum-1,nextnum)];ET.register_namespace('',cns);zout.writestr('[Content_Types].xml',ET.tostring(ct,encoding='utf-8',xml_declaration=True))
 out={'input_sha256':sha(IN),'output_sha256':sha(OUT),'packets':total,'counts':[{'capture':d,'origin':o,'disposition':di,'class':c,'status':s,'count':n} for (d,o,di,c,s),n in sorted(counts.items())]};assert total==359233
 with zipfile.ZipFile(IN) as a,zipfile.ZipFile(OUT) as b:
  assert b.testzip() is None; names=b.namelist();assert len(names)==len(set(names)); old=[n for n in a.namelist() if n.startswith('xl/worksheets/')];assert all(a.read(n)==b.read(n) for n in old);out['prior_worksheet_parts_byte_identical']=len(old);out['zip_integrity']=True;out['zip_member_names_unique']=True
 (B/'EVENT_CLASSIFICATION_RECONCILIATION.json').write_text(json.dumps(out,indent=2));print(json.dumps({'hash':out['output_sha256'],'packets':total,'classes':dict(Counter((x['class'],x['status']) for x in out['counts']))}))
if __name__=='__main__':main()
