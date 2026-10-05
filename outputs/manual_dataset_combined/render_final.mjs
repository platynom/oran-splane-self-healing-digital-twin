import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const m=JSON.parse(await fs.readFile('manifest.json','utf8'));
const w=await SpreadsheetFile.importXlsx(await FileBlob.load('preview_sample.xlsx'));
const col=n=>{let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;};
for(let i=0;i<m.sheets.length;i++){
  const s=m.sheets[i];
  const p=await w.render({sheetName:s.name,range:`A1:${col(Math.min(s.columns,5))}${Math.min(s.rows+1,5)}`,scale:1,format:'png'});
  await fs.writeFile(`final_${i.toString().padStart(2,'0')}.png`,new Uint8Array(await p.arrayBuffer()));
  if(s.columns>8){
    const q=await w.render({sheetName:s.name,range:`${col(s.columns-3)}1:${col(s.columns)}5`,scale:1,format:'png'});
    await fs.writeFile(`final_${i.toString().padStart(2,'0')}_class.png`,new Uint8Array(await q.arrayBuffer()));
  }
  console.log('RENDERED',s.name);
}
