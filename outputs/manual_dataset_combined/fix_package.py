import zipfile,sys,shutil,os,json,re
from xml.sax.saxutils import escape
from pathlib import Path
p=Path(sys.argv[1]); temp=p.with_suffix('.repack.tmp')
date_sheet='xl/worksheets/sheet8.xml'
date_rows=json.loads(Path('part_07_000.json').read_text(encoding='utf-8'))['rows']
with zipfile.ZipFile(p) as src,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
    for item in src.infolist():
        if item.filename=='[Content_Types].xml' or item.filename.endswith('.rels'):
            data=src.read(item.filename).replace(b'ns0:',b'').replace(b'xmlns:ns0=',b'xmlns=')
            dst.writestr(item.filename,data)
        elif item.filename==date_sheet:
            xml=src.read(item.filename).decode('utf-8')
            def restore(match):
                n=int(match[1]); original=date_rows[n-2][2]
                return f'<x:c r="C{n}" s="1" t="str"><x:v>{escape(original)}</x:v></x:c>'
            xml=re.sub(r'<x:c r="C([2-9]|[1-9][0-9]+)"[^>]*>.*?</x:c>',restore,xml)
            dst.writestr(item.filename,xml)
        else:
            with src.open(item.filename) as r,dst.open(item.filename,'w') as w:shutil.copyfileobj(r,w,1024*1024)
with zipfile.ZipFile(p) as a,zipfile.ZipFile(temp) as b:
    for item in a.infolist():
        if item.filename not in ['[Content_Types].xml',date_sheet] and not item.filename.endswith('.rels'):
            assert item.CRC==b.getinfo(item.filename).CRC
os.replace(temp,p)
print('Package namespaces fixed; exact source timestamps restored; other worksheet/style bytes unchanged:',p)
