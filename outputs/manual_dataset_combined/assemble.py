import concurrent.futures, subprocess, json, zipfile, re, copy, time
import xml.etree.ElementTree as E
from pathlib import Path

B=Path(__file__).resolve().parent
NODE=Path('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
M=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
E.register_namespace('x',NS); E.register_namespace('r',REL)
def tag(n): return '{'+NS+'}'+n
def build(fn):
    out=B/(fn+'.xlsx')
    if out.exists(): return fn
    p=subprocess.run([str(NODE),'--max-old-space-size=2048','build_part.mjs',fn],cwd=B,capture_output=True,text=True)
    (B/(fn+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode: raise RuntimeError(fn+' '+(p.stdout+p.stderr)[-3000:])
    return fn
parts=[fn for s in M['sheets'] for fn in s['parts']]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for i,f in enumerate(pool.map(build,parts),1):
        print(f'EXPORTED {i}/{len(parts)} {f}',flush=True)

# Combine artifact-authored parts without keeping hundreds of thousands of rows in RAM.
first=B/(parts[0]+'.xlsx')
with zipfile.ZipFile(first) as z:
    styles=E.fromstring(z.read('xl/styles.xml'))
    theme=z.read('xl/theme/theme1.xml')
stylecache={}; maps={}
def register_style(raw):
    if raw in stylecache:return stylecache[raw]
    src=E.fromstring(raw); remaps={}
    for coll in ['numFmts','fonts','fills','borders','cellStyleXfs','cellXfs']:
        old=src.find(tag(coll)); dest=styles.find(tag(coll))
        if old is None:continue
        if dest is None:
            dest=E.Element(tag(coll),{'count':'0'});styles.insert(0,dest)
        idxmap={}
        for idx,e in enumerate(old):
            e=copy.deepcopy(e)
            if coll in ['cellStyleXfs','cellXfs']:
                for attr,collection in [('fontId','fonts'),('fillId','fills'),('borderId','borders'),('xfId','cellStyleXfs')]:
                    if attr in e.attrib:e.set(attr,str(remaps.get(collection,{}).get(int(e.get(attr)),int(e.get(attr)))))
                if 'numFmtId' in e.attrib:e.set('numFmtId',str(remaps.get('numFmts',{}).get(int(e.get('numFmtId')),int(e.get('numFmtId')))))
            if coll=='numFmts':
                found=next((x for x in dest if x.get('formatCode')==e.get('formatCode')),None)
                original=int(e.get('numFmtId'))
                if found is None:
                    n=max([163]+[int(x.get('numFmtId')) for x in dest])+1;e.set('numFmtId',str(n));dest.append(e)
                else:n=int(found.get('numFmtId'))
                idxmap[original]=n
            else:
                encoded=E.tostring(e)
                matches=[j for j,x in enumerate(dest) if E.tostring(x)==encoded]
                if matches:n=matches[0]
                else:n=len(dest);dest.append(e)
                idxmap[idx]=n
        dest.set('count',str(len(dest)));remaps[coll]=idxmap
    stylecache[raw]=remaps['cellXfs'];return remaps['cellXfs']

def col(n):
    out=''
    while n:n,k=divmod(n-1,26);out=chr(65+k)+out
    return out

outfile=B/'ORAN_All_Current_Datasets.xlsx'
audit=[]
with zipfile.ZipFile(outfile,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for si,s in enumerate(M['sheets'],1):
        path=f'xl/worksheets/sheet{si}.xml'; offset=0; lastcol=col(s['columns'])
        with out.open(path,'w') as dest:
            for pi,fn in enumerate(s['parts']):
                with zipfile.ZipFile(B/(fn+'.xlsx')) as z:
                    stylemap=register_style(z.read('xl/styles.xml'))
                    xml=z.read('xl/worksheets/sheet1.xml').decode()
                assert ' t="s"' not in xml,'Unexpected shared-string reference'
                assert '<x:f' not in xml,'Unexpected formula'
                # Remap styles once globally; artifact exports literal values as t=str.
                xml=re.sub(r'\bs="(\d+)"',lambda m:'s="'+str(stylemap[int(m[1])])+'"',xml)
                pre,tail=xml.split('<x:sheetData>',1);body,suffix=tail.split('</x:sheetData>',1)
                if pi==0:
                    pre=re.sub(r'<x:dimension[^>]*/>','',pre)
                    pos=pre.index('> ',pre.index('<x:worksheet')) if '> ' in pre[pre.index('<x:worksheet'):] else -1
                    insert=pre.index('>',pre.index('<x:worksheet'))+1
                    pre=pre[:insert]+f'<x:dimension ref="A1:{lastcol}{s["rows"]+1}"/>'+pre[insert:]
                    dest.write((pre+'<x:sheetData>').encode())
                rows=re.findall(r'<x:row\b.*?</x:row>',body,re.S)
                if pi:rows=rows[1:]
                for row in rows:
                    if pi:
                        row=re.sub(r'(<x:row\b[^>]*\br=")(\d+)(")',lambda m:m[1]+str(int(m[2])+offset)+m[3],row,count=1)
                        row=re.sub(r'(<x:c\b[^>]*\br="[A-Z]+)(\d+)(")',lambda m:m[1]+str(int(m[2])+offset)+m[3],row)
                    dest.write(row.encode())
                offset+=len(rows)-(1 if pi==0 else 0)
            assert offset==s['rows'],(s['name'],offset,s['rows'])
            suffix=re.sub(r'<x:autoFilter.*?</x:autoFilter>|<x:autoFilter[^>]*/>','',suffix,flags=re.S)
            dest.write((f'</x:sheetData><x:autoFilter ref="A1:{lastcol}{offset+1}"/>'+suffix).encode())
        audit.append([s['name'],offset,s['columns']]);print('ASSEMBLED',s['name'],offset,flush=True)
    out.writestr('xl/styles.xml',E.tostring(styles,encoding='utf-8',xml_declaration=True))
    out.writestr('xl/theme/theme1.xml',theme)
    wb=E.Element(tag('workbook'));views=E.SubElement(wb,tag('bookViews'));E.SubElement(views,tag('workbookView'),{'activeTab':'3'})
    sheets=E.SubElement(wb,tag('sheets'))
    rels=E.Element('{'+PKG+'}Relationships')
    content=E.Element('{'+CT+'}Types')
    for ext,typ in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml')]:E.SubElement(content,'{'+CT+'}Default',{'Extension':ext,'ContentType':typ})
    def override(part,kind):E.SubElement(content,'{'+CT+'}Override',{'PartName':'/'+part,'ContentType':kind})
    override('xl/workbook.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
    override('xl/styles.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml')
    override('xl/theme/theme1.xml','application/vnd.openxmlformats-officedocument.theme+xml')
    for i,s in enumerate(M['sheets'],1):
        E.SubElement(sheets,tag('sheet'),{'name':s['name'],'sheetId':str(i),'{'+REL+'}id':f'rId{i}'})
        E.SubElement(rels,'{'+PKG+'}Relationship',{'Id':f'rId{i}','Type':REL+'/worksheet','Target':f'worksheets/sheet{i}.xml'})
        override(f'xl/worksheets/sheet{i}.xml','application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
    for j,typ,target in [(1,'styles','styles.xml'),(2,'theme','theme/theme1.xml')]:
        E.SubElement(rels,'{'+PKG+'}Relationship',{'Id':f'rId{len(M["sheets"])+j}','Type':REL+'/'+typ,'Target':target})
    rootrels=E.Element('{'+PKG+'}Relationships');E.SubElement(rootrels,'{'+PKG+'}Relationship',{'Id':'rId1','Type':REL+'/officeDocument','Target':'xl/workbook.xml'})
    for path,node in [('xl/workbook.xml',wb),('xl/_rels/workbook.xml.rels',rels),('_rels/.rels',rootrels),('[Content_Types].xml',content)]:out.writestr(path,E.tostring(node,encoding='utf-8',xml_declaration=True))
(B/'assembly_audit.json').write_text(json.dumps(audit,indent=2))
print('SAVED',outfile,outfile.stat().st_size,flush=True)
