import fs from 'node:fs/promises';
import path from 'node:path';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const base=path.resolve('outputs/manual_dataset_combined/manual_reviews');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(base,'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW.xlsx')));
const checks=[];
for(const [sheet,range,file] of [
 ['Read me','A1:B7','01_review_readme.png'],
 ['Parameter guide','A1:H22','01_review_parameter_guide.png'],
 ['All records','A1:U5','01_review_all_records.png'],
 ['Descriptive findings','A1:D5','01_review_findings.png'],
 ['Conditional recovery reasoning','A1:D4','01_review_recovery_reasoning.png'],
]){
 const preview=await wb.render({sheetName:sheet,range,scale:1.4,autoCrop:'all'});
 await fs.writeFile(path.join(base,file),new Uint8Array(await preview.arrayBuffer()));
 const inspection=await wb.inspect({kind:'table',range:`${sheet}!${range}`,include:'values,formulas',tableMaxRows:7,tableMaxCols:15,tableMaxCellChars:120});
 checks.push({sheet,range,render:file,inspection:inspection.ndjson});
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'bounded final formula error scan'});
await fs.writeFile(path.join(base,'01_PRODUCTION_ANNOUNCE_MANUAL_REVIEW_render_check.json'),JSON.stringify({checks,formula_error_scan:errors.ndjson},null,2));
