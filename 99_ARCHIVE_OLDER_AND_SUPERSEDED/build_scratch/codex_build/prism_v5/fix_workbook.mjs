import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin";
const sourcePath = path.join(root, "ORAN_SPlane_Parameter_Fault_Matrix.xlsx");
const outputPath = path.join(root, "ORAN_SPlane_Parameter_Fault_Matrix_CORRECTED_2026-09-28.xlsx");
const previewPath = path.join(root, ".codex_build", "prism_v5", "fault_key_corrected.png");

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));
const sheet = workbook.worksheets.getItem("FAULT KEY");

sheet.getRange("E8").values = [["This kernel lacks sch_netem. Software detection logic can be exercised with packet-timestamp fixtures or an asymmetric proxy, but credible time-error impact requires an independent clock and hardware timestamping."]];
sheet.getRange("F8").values = [["T-SPLANE-05 (delay manipulation)"]];
sheet.getRange("E15").values = [["sch_netem is unavailable in this kernel. The corrected B3 campaign used a tbf bottleneck plus competing non-PTP traffic; packet-delay variation remains packet-observable."]];
sheet.getRange("E17").values = [["sch_netem is unavailable in this kernel. Constant-asymmetry detection logic can be tested with retained or constructed packet timing, but credible physical asymmetry and nanosecond cTE measurement require hardware timestamping."]];

for (const address of ["E8", "F8", "E15", "E17"]) {
  sheet.getRange(address).format.wrapText = true;
}

const changed = await workbook.inspect({
  kind: "table",
  range: "FAULT KEY!A4:F20",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 8,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
const stale = await workbook.inspect({
  kind: "match",
  searchTerm: "netem can inject asymmetric delay|netem delay/jitter is purpose-built|fixed asymmetry can be emulated with netem|T-SPLANE-04 \\(selective delay\\)",
  options: { useRegex: true, maxResults: 50 },
  summary: "stale fault-key claim scan",
});

const preview = await workbook.render({ sheetName: "FAULT KEY", range: "A1:F20", scale: 1.5, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await (await SpreadsheetFile.exportXlsx(workbook)).save(outputPath);

process.stdout.write(JSON.stringify({
  outputPath,
  previewPath,
  changed: changed.ndjson,
  formulaErrors: errors.ndjson,
  staleMatches: stale.ndjson,
}, null, 2));
