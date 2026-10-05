import zipfile,re,json,os
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'ORAN_All_Current_Datasets.xlsx'; temp=p.with_suffix('.layout.tmp')
m=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(p) as src,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
    for item in src.infolist():
        raw=src.read(item.filename)
        if item.filename=='xl/styles.xml':
            raw=raw.replace(b'formatCode="0.###############"',b'formatCode="General"')
        elif item.filename.startswith('xl/worksheets/'):
            i=int(re.search(r'sheet(\d+)',item.filename)[1])-1
            txt=raw.decode('utf-8');pre,rest=txt.split('<x:sheetData>',1)
            for j,h in enumerate(m['sheets'][i]['headers'],1):
                width={'wall_time':42,'scenario':36,'model':46,'reason':100,'error':100,'detail':50}.get(h)
                if width:pre=re.sub(fr'(<x:col min="{j}" max="{j}" width=")[^"]+',lambda x:x[1]+str(width),pre)
            raw=(pre+'<x:sheetData>'+rest).encode()
            assert raw.split(b'<x:sheetData>',1)[1]==src.read(item.filename).split(b'<x:sheetData>',1)[1]
        dst.writestr(item.filename,raw)
os.replace(temp,p)
print('Column widths and numeric display adjusted; every worksheet cell byte unchanged.')
