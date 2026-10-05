import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
const f=await FileBlob.load("outputs/manual_dataset_combined/ORAN_All_Current_Datasets.xlsx");
const wb=await SpreadsheetFile.importXlsx(f);
console.log((await wb.inspect({kind:"sheet",include:"id,name"})).ndjson);
