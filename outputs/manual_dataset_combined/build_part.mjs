import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const file=process.argv[2];
const p=JSON.parse(await fs.readFile(file,'utf8'));
const w=Workbook.create(); const s=w.worksheets.add(p.name);
const nr=p.rows.length+1,nc=p.headers.length;
s.getRangeByIndexes(0,0,nr,nc).values=[p.headers,...p.rows];
s.getRangeByIndexes(0,0,nr,nc).format.font={name:'Arial',size:11};
s.getRangeByIndexes(0,0,nr,nc).setNumberFormat('0.###############');
s.getRangeByIndexes(0,0,nr,nc).format.columnWidth=22;
s.getRangeByIndexes(0,0,1,nc).format={fill:'#243746',font:{name:'Arial',bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:48};
// Apply identical style operations to every part so exported styles are reusable.
s.freezePanes.freezeRows(1);
if(p.name==='Read me') {s.getRange('A1:A16').format.columnWidth=24;s.getRange('B1:B16').format.columnWidth=120;s.getRange('B2:B16').format.wrapText=true;s.getRange('A2:B16').format.rowHeight=58;}
else if(p.name==='Sources') {s.getRangeByIndexes(0,1,nr,1).format.columnWidth=85;s.getRangeByIndexes(0,5,nr,1).format.columnWidth=64;s.getRangeByIndexes(0,7,nr,1).format.columnWidth=70;}
else if(p.name==='Recovery rules') {s.getRangeByIndexes(0,1,nr,1).format.columnWidth=47;s.getRangeByIndexes(0,2,nr,1).format.columnWidth=27;s.getRangeByIndexes(0,3,nr,1).format.columnWidth=110;s.getRangeByIndexes(1,1,nr-1,3).format.wrapText=true;s.getRangeByIndexes(1,0,nr-1,nc).format.rowHeight=45;}
else if(p.name==='Parameter roles') {s.getRangeByIndexes(0,0,nr,nc).format.columnWidth=44;s.getRangeByIndexes(0,2,nr,1).format.columnWidth=90;s.getRangeByIndexes(1,0,nr-1,nc).format.wrapText=true;s.getRangeByIndexes(1,0,nr-1,nc).format.rowHeight=42;}
else {s.getRangeByIndexes(0,0,nr,2).format.columnWidth=14;s.getRangeByIndexes(0,nc-3,nr,3).format.columnWidth=48;}
if(file.endsWith('_000.json')) {
  const first=await w.render({sheetName:p.name,range:`A1:${String.fromCharCode(64+Math.min(nc,5))}${Math.min(nr,5)}`,scale:1,format:'png'});
  await fs.writeFile(file+'.png',new Uint8Array(await first.arrayBuffer()));
  if(nc>8) {
    const col=(n)=>{let x='';while(n){n--;x=String.fromCharCode(65+n%26)+x;n=Math.floor(n/26);}return x;};
    const last=await w.render({sheetName:p.name,range:`${col(nc-3)}1:${col(nc)}5`,scale:1,format:'png'});
    await fs.writeFile(file+'.last.png',new Uint8Array(await last.arrayBuffer()));
  }
  const check=await w.inspect({kind:'table',range:'A1:D3',sheetId:p.name,tableMaxRows:3,tableMaxCols:4,maxChars:1200});
  await fs.writeFile(file+'.check.json',check.ndjson);
}
await (await SpreadsheetFile.exportXlsx(w)).save(file+'.xlsx');
console.log('BUILT',p.name,p.rows.length,file);
