import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const w=Workbook.create(); const s=w.worksheets.add('Test');
s.getRange('A1:C2').values=[['Source','Number','Classification'],['hello',1,'healthy']];
s.getRange('A1:C2').format.font={name:'Arial',size:11};
s.getRange('A1:C1').format={fill:'#243746',font:{name:'Arial',bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:44};
s.freezePanes.freezeRows(1);
await (await SpreadsheetFile.exportXlsx(w)).save('probe.xlsx');
