import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const base = path.resolve("outputs/manual_dataset_combined");
const manifest = JSON.parse(await fs.readFile(path.join(base, "manifest.json"), "utf8"));
const wb = Workbook.create();
const summary = wb.worksheets.add("Summary");
const status = wb.worksheets.add("Source status");
const examples = wb.worksheets.add("Evidence examples");
const notes = wb.worksheets.add("Read me");
const navy = "#17365D", light = "#DCE6F1", warn = "#FCE4D6", gray = "#F2F2F2";

function title(sheet, range, text) {
  sheet.getRange(range).merge();
  sheet.getRange(range).values = [[text]];
  sheet.getRange(range).format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 14 }, horizontalAlignment: "left", verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 26;
}
function header(sheet, range) {
  sheet.getRange(range).format = { fill: light, font: { bold: true, color: "#000000" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
}
for (const s of [summary, status, examples, notes]) { s.showGridLines = false; s.tabColor = navy; }

title(summary, "A1:F1", "Corrected O-RAN evidence analysis");
summary.getRange("A3:B10").values = [
  ["Deliverable status", "Corrected analysis view; original combined workbook remains preserved and superseded."],
  ["Scope", "Evidence provenance, source status, alignment, and limitations."],
  ["Do not infer", "Packet annotation = clock health, attack exposure, device authorization, or recovery outcome."],
  ["Quarantined", "Announce sessions 1 and 2: one identical PCAP with 5,312 conflicting labels."],
  ["Eligible evidence", "Simulator results for simulator claims; packet/PCAP data for descriptive capture-local observations."],
  ["Real evaluation", "Blocked unless every actual input has traceable, reviewed, hash-bound clock-health evidence."],
  ["Recovery", "Code contains candidates and modeled effects; no executed physical recovery is established."],
  ["Original source values", "Unchanged in their original CSV/PCAP files and the superseded ORAN_All_Current_Datasets.xlsx."],
];
summary.getRange("A3:A10").format = { fill: gray, font: { bold: true }, verticalAlignment: "center", wrapText: true };
summary.getRange("B3:B10").format.wrapText = true;
summary.getRange("A3:B10").format.borders = { preset: "outside", style: "thin", color: "#BFBFBF" };
summary.getRange("A12:F12").merge(); summary.getRange("A12").values = [["Use this workbook for the canonical, non-duplicated interpretation. Detailed raw records remain in original source files for traceability."]]; summary.getRange("A12").format = { fill: warn, wrapText: true, font: { bold: true } };
summary.getRange("A:A").format.columnWidth = 25; summary.getRange("B:B").format.columnWidth = 95; summary.getRange("A12:F12").format.rowHeight = 34;

title(status, "A1:H1", "Canonical source status and disposition");
const sourceRows = manifest.sources.map((row) => {
  const [id, sourcePath, type, rows, columns, provenance, duplicateOf, hash] = row;
  let canonical = "See canonical map"; let disposition = "Retained for provenance"; let eligible = "Source-specific descriptive review only";
  if (id === "S021" || id === "S022" || (id >= "S028" && id <= "S031")) { canonical = "Announce capture conflict"; disposition = "QUARANTINED"; eligible = "Provenance/audit only; no ground truth or independent count"; }
  else if (["S017", "S018", "S019", "S020"].includes(id)) { canonical = "Synthetic simulator"; disposition = duplicateOf !== "None" ? "Duplicate representation" : "Retained"; eligible = "Simulator-only claims"; }
  else if (type.includes("TIMESAFE telemetry")) { canonical = "Capture-derived session"; disposition = "Exploratory / gated"; eligible = "Transformation audit only unless independently validated"; }
  else if (type.includes("TIMESAFE")) { canonical = "TIMESAFE capture"; disposition = "Supplied annotation / raw"; eligible = "Capture-local descriptive review"; }
  else if (type.includes("Simulated")) { canonical = "Synthetic simulator"; disposition = "Retained"; eligible = "Simulator-only claims"; }
  else if (type.includes("Netem")) { canonical = "Netem software testbed"; disposition = "Retained"; eligible = "Software-testbed behavior only"; }
  return [id, canonical, sourcePath, type, rows, provenance, disposition, eligible, duplicateOf, hash];
});
status.getRange("A3:J3").values = [["ID", "Canonical experiment", "Original source path", "Representation", "Rows", "Provenance", "Disposition", "Eligible analysis", "Duplicate of", "SHA-256"]];
header(status, "A3:J3"); status.getRangeByIndexes(3, 0, sourceRows.length, 10).values = sourceRows;
status.getRange("A3:J" + (3 + sourceRows.length)).format.wrapText = true; status.freezePanes.freezeRows(3);
for (const col of ["A:A","B:B","C:C","D:D","E:E","F:F","G:G","H:H","I:I","J:J"]) status.getRange(col).format.columnWidth = 18;
status.getRange("C:C").format.columnWidth = 54; status.getRange("H:H").format.columnWidth = 45; status.getRange("J:J").format.columnWidth = 40;

title(examples, "A1:F1", "Worked evidence examples");
examples.getRange("A3:F6").values = [
  ["Example", "What changed", "Where / when", "What it supports", "Alternative explanations", "Recovery status"],
  ["Production telemetry start", "First 3 packets emit no telemetry until Sync state resolves.", "Production PCAP, packet indices 1–4; 0 to 0.008973 s.", "Stateful transformation explanation.", "Not packet loss or a health diagnosis.", "No action recorded."],
  ["Supplied positive packets", "200 supplied annotations are Announce packets in one capture-relative interval.", "Production labeled CSV, 78.506815–105.308242 s.", "Describes source annotations and packet fields.", "Authorization and launch evidence unavailable; not clock health.", "No action or measured outcome."],
  ["Conflicting Announce sessions", "Same PCAP content, 5,312 label conflicts.", "Four PCAP aliases; 46,998 PTP rows.", "Duplicate/conflict finding.", "Neither label set can be preferred without source records.", "Quarantined; no recommendation."],
];
header(examples, "A3:F3"); examples.getRange("A3:F6").format.wrapText = true; examples.getRange("A3:F6").format.borders = { preset: "outside", style: "thin", color: "#BFBFBF" }; for (const c of ["A:A","B:B","C:C","D:D","E:E","F:F"]) examples.getRange(c).format.columnWidth = 30;

title(notes, "A1:D1", "Read me and scientific limits");
notes.getRange("A3:B10").values = [
  ["Supersedes", "Interpretation/recovery columns in ORAN_All_Current_Datasets.xlsx. The original workbook is preserved, not overwritten."],
  ["Source register", "Every included source remains listed with original path, row count, hash, representation type, and a claim-specific disposition."],
  ["Labels", "Supplied labels remain supplied annotations unless capture-specific evidence independently validates their stated meaning."],
  ["Duplicates", "Aliases, derived sessions, and overlapping windows are one evidence lineage and must not cross train/test boundaries."],
  ["Physical claims", "Require timestamp provenance, receiver/M-plane state, calibration, and controlled observations."],
  ["Recovery claims", "Require recorded command, timing, before/after measurements, and an appropriate control."],
  ["Detailed audit", "See ACCEPTANCE_REGISTER.md, CANONICAL_EXPERIMENT_MAP.md, PACKET_TELEMETRY_ALIGNMENT.md, and PROFESSOR_EXPLANATION.md."],
  ["Mechanical gates", "Protect evaluation inputs; they do not establish scientific authenticity."],
];
notes.getRange("A3:A10").format = { fill: gray, font: { bold: true }, wrapText: true }; notes.getRange("B3:B10").format.wrapText = true; notes.getRange("A:A").format.columnWidth = 24; notes.getRange("B:B").format.columnWidth = 95;
for (const s of [summary, examples, notes]) s.getUsedRange().format.autofitRows();
wb.recalculate();
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(path.join(base, "ORAN_All_Current_Datasets_CORRECTED.xlsx"));
console.log("created corrected workbook");
