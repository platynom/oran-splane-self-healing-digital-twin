import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
// Artifact authors bounded source samples and styles. The companion streamer
// replaces sample rows with full CSV records without retaining all rows in RAM.
const base=path.resolve('outputs/manual_dataset_combined');
const plan=JSON.parse(await fs.readFile(path.join(base,'detailed_plan.json'),'utf8'));
const wb=Workbook.create();
function table(name,headers,rows,widths){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 s.getRangeByIndexes(0,0,rows.length+1,headers.length).values=[headers,...rows];
 s.getUsedRange().format.font={name:'Arial',size:10};
 s.getUsedRange().format.verticalAlignment='center';
 s.getRangeByIndexes(0,0,1,headers.length).format={fill:'#17365D',font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},wrapText:true,rowHeight:42};
 widths.forEach((width,i)=>s.getRangeByIndexes(0,i,rows.length+1,1).format.columnWidth=width);
 s.freezePanes.freezeRows(1);return s;
}
const summary=table('Summary',['Topic','What this workbook contains'],[
 ['Scope',`${plan.length} sources; ${plan.reduce((n,s)=>n+s.rows,0).toLocaleString('en-US')} source records, including duplicate representations for audit.`],
 ['Dataset detail','One source per tab. All original columns come first; Audit columns and interpretations are appended.'],
 ['Real data first','CAPTURE_EXPORT supports capture-local description. CAPTURE_DERIVED includes defaults and inferred fields.'],
 ['Simulation and emulation','SIMULATION, SOFTWARE_TESTBED and MODEL_OUTPUT are explicitly separated from physical evidence.'],
 ['Labels','Original labels are supplied annotations or generated labels. No physical fault, maliciousness or recovery is inferred from a filename.'],
 ['Quarantine','Announce sessions 1/2 and their raw/derived aliases share one capture and conflicting labels. Retained for provenance only.'],
 ['Independent counts','Source-row totals are not independent experiments. Use capture groups; Netem run relationships remain unresolved.'],
 ['Precision','Original CSV fields are stored as exact text to preserve precision, timestamps and identifiers. Convert copies for numerical analysis.'],
 ['Recovery','The final column states whether an action is justified. Unknown remains unknown; see the conditional action discussion in the guide.'],
 ['External evidence','Launch logs, authorization records, receiver measurements and physical action outcomes are still needed for stronger claims.']
],[25,105]);
summary.getRange('B2:B11').format.wrapText=true;summary.getUsedRange().format.autofitRows();
const status=table('Source status',['ID','Detail tab','Original source file','Rows','Original columns','Capture group','Provenance','Status','Eligibility','Duplicate relationship','SHA256'],plan.map(d=>[d.id,d.sheet,d.file,d.rows,d.columns,d.group,d.kind,d.status,d.eligibility,d.relationship,d.hash]),[12,34,80,14,18,34,26,32,32,65,72]);
status.getRange('A2:K46').format.rowHeight=30;
const examples=table('Evidence examples',['What','Which','What it supports','Limit'],[
 ['Initial three packets','Production packets 1–3','No resolved Sync state yet; telemetry begins later','Does not establish packet loss or fault'],
 ['200 positive labels','Production supplied Label=1','Description of annotations and packet fields','No independent launch or clock-health validation'],
 ['One capture, conflicting labels','Announce session 1/2','Duplicate quarantine and provenance review','No selecting the label set with better scores']
],[27,32,60,64]);examples.getUsedRange().format.wrapText=true;examples.getUsedRange().format.autofitRows();
for(const d of plan){
 const sourceWidths={'wall_time':36,'Time':30,'t_s':24,'Time Interval':24,'scenario':34,'model':34,'attack_family':28,'action':30,'reason':55};
 const widths=d.headers.map((h,i)=>i<d.columns?(sourceWidths[h]||Math.min(56,Math.max(20,h.length+3))):({'Audit source file':80,'Audit source SHA256':72,'Audit label meaning':65,'Audit duplicate relationship':68,'Audit reasoning':80,'Situation interpretation':60,'Proposed recovery action':55}[h]||30));
 const s=table(d.sheet,d.headers,d.samples,widths);
 s.getRangeByIndexes(1,0,d.samples.length,d.headers.length).setNumberFormat('@');
 s.getRangeByIndexes(1,d.columns+3,d.samples.length,1).setNumberFormat('0');
 s.getRangeByIndexes(1,0,d.samples.length,d.headers.length).format.rowHeight=30;
 s.getRangeByIndexes(1,d.headers.length-2,d.samples.length,2).format.wrapText=true;
}
const guide=table('Read me',['Topic','How to use it'],[
 ['Start','Open S027 TIMESAFE raw captures. Select one packet parameter; read PARAMETER_BY_PARAMETER_GUIDE.md beside this workbook.'],
 ['Source record','Audit source record is the 1-based CSV data-record ordinal, excluding the header. It is not a physical line number for multiline CSV.'],
 ['Exact source values','All original cells, including numeric strings and empty fields, are copied exactly. Excel cannot retain more than 15 numeric significant digits.'],
 ['Calculations','Copy a selected numeric column into an analysis sheet and convert explicitly. Keep raw text unchanged; use Python Decimal if exact precision matters.'],
 ['Filters','Every detail sheet has a header filter and frozen header. Audit status identifies quarantine; eligibility separates source types.'],
 ['Joining','Use a validated capture-specific key, never elapsed time alone. Packet, telemetry and window tables have different meanings.'],
 ['Duplicates','All original representations remain inspectable. Raw and derived forms are not extra experiments; duplicate records must not inflate statistics.'],
 ['Situation and action','An unknown situation is not healthy. An action needs evidence of the issue and an available reference/path; physical success needs execution and receiver records.'],
 ['Teaching evidence','See PARAMETER_PROVENANCE.md, LABEL_TAXONOMY.md, THRESHOLD_AND_RECOVERY_AUDIT.md and PARAMETER_BY_PARAMETER_GUIDE.md.'],
 ['Historical files','The 45-source scope includes selected historical representations. SOURCE_DEPENDENCY_FINDINGS.md records wider inventory and unresolved dynamic use.'],
 ['Verification','detailed_reconciliation.json records exact cell reconciliation and source hashes. Mechanical correctness is separate from scientific authenticity.']
],[25,115]);guide.getRange('B2:B12').format.wrapText=true;guide.getUsedRange().format.autofitRows();
wb.recalculate();
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(base,'detailed_template.xlsx'));
await fs.mkdir(path.join(base,'detailed_previews'),{recursive:true});
for(const s of wb.worksheets.items){
 const isDetail=s.name.startsWith('S0');
 const range=isDetail?'A1:D4':s.name==='Source status'?'A1:E5':s.name==='Evidence examples'?'A1:D4':'A1:B12';
 const blob=await wb.render({sheetName:s.name,range,scale:1,format:'png'});
 await fs.writeFile(path.join(base,'detailed_previews',s.name.replace(/[^a-zA-Z0-9]/g,'_')+'.png'),new Uint8Array(await blob.arrayBuffer()));
 console.log('RENDERED',s.name);
}
const check=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:20}});
await fs.writeFile(path.join(base,'detailed_template_check.json'),check.ndjson);
console.log('TEMPLATE READY',wb.worksheets.items.length);
