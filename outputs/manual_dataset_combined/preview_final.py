import zipfile,json,re
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(B/'ORAN_All_Current_Datasets.xlsx') as z,zipfile.ZipFile(B/'preview_sample.xlsx','w',zipfile.ZIP_DEFLATED) as out:
    for info in z.infolist():
        if info.filename.startswith('xl/worksheets/'):
            with z.open(info.filename) as f:
                raw=b''
                while raw.count(b'</x:row>')<6:
                    b=f.read(65536)
                    if not b:break
                    raw+=b
            txt=raw.decode('utf-8',errors='ignore');pre,body=txt.split('<x:sheetData>',1)
            rows=re.findall(r'<x:row\b.*?</x:row>',body,re.S)[:6]
            pre=re.sub(r'<x:dimension[^>]*/>','',pre)
            out.writestr(info.filename,pre+'<x:sheetData>'+''.join(rows)+'</x:sheetData></x:worksheet>')
        else:out.writestr(info.filename,z.read(info.filename))
print('Final workbook sample prepared')
