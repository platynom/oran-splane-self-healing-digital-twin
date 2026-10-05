"""Preserve CSV lexical values in artifact-authored sheet templates, using bounded memory.

Raw cells intentionally remain text: Excel's 15-digit precision must not silently
round scientific values. Convert copies of selected columns for calculations.
No source file is modified. Run prepare, build template JS, assemble, verify.
"""
from pathlib import Path
import csv, hashlib, json, re, sys, zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

B = Path(__file__).resolve().parent
ROOT = B.parents[1]
M = json.loads((B/'manifest.json').read_text(encoding='utf-8'))
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
EXTRA = ['Audit source ID','Audit source file','Audit source SHA256','Audit source record',
         'Audit capture group','Audit provenance','Audit label meaning','Audit status',
         'Audit eligibility','Audit duplicate relationship','Audit reasoning',
         'Situation interpretation','Proposed recovery action']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def col(n):
    s=''
    while n: n,k=divmod(n-1,26); s=chr(65+k)+s
    return s

def info(s):
    sid,file,typ,n,nc,prov,dup,digest=s
    num=int(sid[1:])
    groups={21:'announce_conflict',22:'announce_conflict',28:'announce_conflict',29:'announce_conflict',30:'announce_conflict',31:'announce_conflict',41:'announce_conflict',42:'announce_conflict',23:'announce_3',32:'announce_3',33:'announce_3',43:'announce_3',24:'sync_followup',34:'sync_followup',35:'sync_followup',44:'sync_followup',25:'sync_singlestep',36:'sync_singlestep',37:'sync_singlestep',45:'sync_singlestep',26:'production_announce',27:'production_announce',38:'production_announce',39:'production_announce',40:'production_announce'}
    group=groups.get(num,'simulator_collection' if 17<=num<=20 else 'run_linkage_unresolved_'+sid)
    if 'Simulated' in typ: kind,sem,eligible='SIMULATION','Scenario/label generated in simulation','SIMULATION_ONLY'
    elif typ=='Model metrics': kind,sem,eligible='MODEL_OUTPUT','Reported metric; training provenance not independently verified','SOFTWARE_REPORT_ONLY'
    elif 'Netem' in typ: kind,sem,eligible='SOFTWARE_TESTBED','Recorded scenario/prediction; physical fault meaning unverified','SOFTWARE_ONLY'
    elif typ=='TIMESAFE telemetry': kind,sem,eligible='CAPTURE_DERIVED','Projected label; not measured clock health','EXPLORATORY_DERIVED_ONLY'
    else: kind,sem,eligible='CAPTURE_EXPORT','Supplied packet annotation, if present; authenticity unverified','CAPTURE_DESCRIPTION_ONLY'
    status='UNVALIDATED_PHYSICAL_CLAIM'
    if kind=='SIMULATION':status='SIMULATION_ONLY'
    if group=='announce_conflict':status,eligible='QUARANTINED','PROVENANCE_ONLY'
    relation=('Exact file duplicate of '+dup) if dup!='None' else ('Related capture representations: '+group if num>=21 else 'Run overlap not established; do not assume independence')
    if dup!='None':status='DUPLICATE_REPRESENTATION'
    reason='LABEL_TAXONOMY.md; PARAMETER_PROVENANCE.md; CANONICAL_EXPERIMENT_MAP.md'
    if group=='announce_conflict':reason='ISSUE_02_FINDINGS.md; conflicting annotations on one capture'
    situation='Unknown from this row alone'
    if kind=='SIMULATION':situation='Simulation scenario only; see original label/scenario'
    elif kind=='SOFTWARE_TESTBED':situation='Software record only; see original scenario/prediction'
    elif kind=='MODEL_OUTPUT':situation='Model summary; not a situation observation'
    action='Not established; no verified physical action'
    return dict(id=sid,file=file,type=typ,rows=n,columns=nc,hash=digest,group=group,kind=kind,semantics=sem,status=status,eligibility=eligible,relationship=relation,reason=reason,situation=situation,action=action,sheet=(sid+' '+typ)[:31])

def extras(d,record):
    return [d['id'],d['file'],d['hash'],record,d['group'],d['kind'],d['semantics'],d['status'],d['eligibility'],d['relationship'],d['reason'],d['situation'],d['action']]

def prepare():
    plan=[]
    for s in M['sources']:
        d=info(s); p=ROOT/d['file']; assert sha(p)==d['hash'],d['id']
        with p.open(encoding='utf-8-sig',newline='') as f:
            it=csv.reader(f); headers=next(it); samples=[]; count=0
            for count,row in enumerate(it,1):
                assert len(row)==len(headers),(d['id'],count,'ragged CSV')
                assert all(len(v)<=32767 for v in row),(d['id'],count,'Excel cell limit')
                if count<=3:samples.append(row+extras(d,count))
        assert count==d['rows'] and len(headers)==d['columns'],d['id']
        d.update(headers=headers+EXTRA,samples=samples)
        plan.append(d)
    (B/'detailed_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PREPARED',len(plan),'sources',sum(d['rows'] for d in plan),'rows',flush=True)

def cell(ref,value,style):
    if isinstance(value,int):return f'<x:c r="{ref}" s="{style}" t="n"><x:v>{value}</x:v></x:c>'
    assert not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',value),'Invalid XML control'
    return f'<x:c r="{ref}" s="{style}" t="inlineStr"><x:is><x:t xml:space="preserve">{escape(value)}</x:t></x:is></x:c>'

def assemble():
    plan=json.loads((B/'detailed_plan.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(B/'detailed_template.xlsx') as src, zipfile.ZipFile(B/'detailed_pending.xlsx','w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        paths={f'xl/worksheets/sheet{i+4}.xml':d for i,d in enumerate(plan)}
        for item in src.infolist():
            if item.filename not in paths:out.writestr(item,src.read(item.filename));continue
            d=paths[item.filename]; xml=src.read(item.filename).decode('utf-8')
            before,rest=xml.split('<x:sheetData>',1); body,after=rest.split('</x:sheetData>',1)
            rows=re.findall(r'<x:row\b.*?</x:row>',body,re.S)
            assert len(rows)>=2 and ' t="s"' not in body
            header=rows[0]; sample=ET.fromstring('<x:root xmlns:x="'+NS+'">'+rows[1]+'</x:root>')[0]
            styles={re.sub(r'\d','',c.get('r')):c.get('s','0') for c in sample}
            end=f'{col(len(d["headers"]))}{d["rows"]+1}'
            before=re.sub(r'<x:dimension[^>]*/>','',before)
            i=before.index('>',before.index('<x:worksheet'))+1
            before=before[:i]+f'<x:dimension ref="A1:{end}"/>'+before[i:]
            after=re.sub(r'<x:autoFilter[^>]*/>|<x:autoFilter.*?</x:autoFilter>','',after,flags=re.S)
            with out.open(item.filename,'w') as dest, (ROOT/d['file']).open(encoding='utf-8-sig',newline='') as f:
                dest.write((before+'<x:sheetData>'+header).encode('utf-8')); it=csv.reader(f);next(it)
                for record,values in enumerate(it,1):
                    idx=record+1
                    row=f'<x:row r="{idx}" ht="30" customHeight="1">'+''.join(cell(f'{col(j)}{idx}',v,styles.get(col(j),'0')) for j,v in enumerate(values+extras(d,record),1))+'</x:row>'
                    dest.write(row.encode('utf-8'))
                dest.write((f'</x:sheetData><x:autoFilter ref="A1:{end}"/>'+after).encode('utf-8'))
            print('STREAMED',d['id'],d['rows'],flush=True)
    print('ASSEMBLED',flush=True)

def verify():
    plan=json.loads((B/'detailed_plan.json').read_text(encoding='utf-8')); results=[]
    workbook = B/'detailed_pending.xlsx'
    if not workbook.exists(): workbook = B/'ORAN_All_Current_Datasets_CORRECTED.xlsx'
    with zipfile.ZipFile(workbook) as z:
        assert z.testzip() is None
        for i,d in enumerate(plan,4):
            assert sha(ROOT/d['file'])==d['hash'],d['id']
            with z.open(f'xl/worksheets/sheet{i}.xml') as stream, (ROOT/d['file']).open(encoding='utf-8-sig',newline='') as f:
                it=csv.reader(f); headers=next(it); row_count=0; cells=0
                for event,node in ET.iterparse(stream,events=('end',)):
                    if node.tag!='{'+NS+'}row':continue
                    got=[]
                    for c in node:
                        assert c.find('{'+NS+'}f') is None,'Unexpected formula'
                        assert c.get('t')!='e','Excel error cell'
                        if c.get('t')=='inlineStr':v=''.join(c.itertext())
                        else:v=c.findtext('{'+NS+'}v',default='')
                        got.append(v)
                    if row_count==0:expected=d['headers']
                    else:expected=next(it)+[str(v) for v in extras(d,row_count)];cells+=len(headers)
                    assert got==expected,(d['id'],row_count,'value mismatch')
                    row_count+=1;node.clear()
                assert row_count-1==d['rows'] and next(it,None) is None
            results.append({'id':d['id'],'rows':row_count-1,'original_cells_verified':cells,'source_hash_match':True,'all_appended_values_verified':True})
            print('VERIFIED',d['id'],flush=True)
    report={'method':'Independent CSV reader versus exported XLSX XML; exact lexical source cell comparison, all rows and metadata, source hashes, ZIP integrity, no formulas/error cells in detail sheets','sources':len(results),'rows':sum(r['rows'] for r in results),'original_cells_verified':sum(r['original_cells_verified'] for r in results),'workbook_sha256':sha(workbook),'results':results}
    (B/'detailed_reconciliation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)

if __name__=='__main__':{'prepare':prepare,'assemble':assemble,'verify':verify}[sys.argv[1]]()
