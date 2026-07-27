import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const artifactPath = require.resolve("@oai/artifact-tool");
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactPath).href);

const ROOT = process.cwd();
const THREAD_ID = process.env.CODEX_THREAD_ID || `manual-${Date.now()}`;
const WORKSPACE = path.join(os.tmpdir(), "codex-presentations", THREAD_ID, "oran-complete-workflow-dataset");
const TMP_DIR = path.join(WORKSPACE, "tmp");
const PREVIEW_DIR = path.join(TMP_DIR, "preview");
const LAYOUT_DIR = path.join(TMP_DIR, "layout");
const OUTPUT_DIR = path.join(ROOT, "outputs", "presentations");
const FINAL_PPTX = path.join(OUTPUT_DIR, "O-RAN_AI_Native_Complete_Workflow_and_Dataset_Requirements.pptx");
const SHOW_FIRST_DIR = path.join(ROOT, "outputs", "EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED", "01_show_first");
const SHOW_FIRST_PPTX = path.join(SHOW_FIRST_DIR, "11_COMPLETE_WORKFLOW_AND_DATASET_REQUIREMENTS.pptx");

const C = {
  bg: "slate-50",
  ink: "slate-950",
  muted: "slate-600",
  faint: "slate-100",
  line: "slate-200",
  dark: "slate-900",
  panel: "white",
  blue: "#2563eb",
  cyan: "#0891b2",
  green: "#059669",
  amber: "#d97706",
  red: "#dc2626",
  purple: "#7c3aed",
};

await fs.mkdir(PREVIEW_DIR, { recursive: true });
await fs.mkdir(LAYOUT_DIR, { recursive: true });
await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.mkdir(SHOW_FIRST_DIR, { recursive: true });

function csvPath(name) {
  return path.join(SHOW_FIRST_DIR, name);
}

async function readRows(file, limit = 8) {
  const text = await fs.readFile(file, "utf8");
  return text.trim().split(/\r?\n/).slice(0, limit).map((line) => line.split(","));
}

const flexric = JSON.parse(await fs.readFile(path.join(ROOT, "outputs", "reports", "flexric_kpm_30min.json"), "utf8"));
const reportSummary = await readRows(csvPath("03_FLEXRIC_30MIN_REPORT_SUMMARY.csv"), 8);
const modelMetrics = await readRows(csvPath("04_MODEL_BENCHMARK_METRICS.csv"), 7);
const controlledWindows = await readRows(csvPath("06_CONTROLLED_FAULT_WINDOW_RESULTS.csv"), 6);
const reconciliation = await readRows(csvPath("08_PIPELINE_ROW_COUNT_RECONCILIATION.csv"), 8);
const decisionSample = await readRows(csvPath("07_FULL_FLEXRIC_DECISION_ROWS.csv"), 4);
const datasetMain = await readRows(path.join(ROOT, "outputs", "dataset_template_precise", "01_main_kpi_telemetry_template.csv"), 3);
const datasetLabels = await readRows(path.join(ROOT, "outputs", "dataset_template_precise", "02_fault_event_label_template.csv"), 3);
const datasetHealing = await readRows(path.join(ROOT, "outputs", "dataset_template_precise", "03_healing_action_outcome_template.csv"), 3);
const datasetXapp = await readRows(path.join(ROOT, "outputs", "dataset_template_precise", "04_ric_xapp_log_template.csv"), 3);
const datasetInventory = await readRows(path.join(ROOT, "outputs", "dataset_template_precise", "05_network_inventory_context_template.csv"), 3);

await fs.writeFile(
  path.join(TMP_DIR, "source-notes.txt"),
  [
    "Sources used for deck:",
    "PROJECT_INDEX.md",
    "outputs/reports/flexric_kpm_30min.json",
    "outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/*.csv",
    "outputs/dataset_template_precise/*.csv",
    "No external web sources were used.",
  ].join("\n"),
  "utf8",
);

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function addText(s, text, left, top, width, height, style = {}) {
  const shape = s.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(text);
  shape.text.style = {
    fontSize: style.fontSize ?? 18,
    bold: style.bold ?? false,
    color: style.color ?? C.ink,
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "top",
    typeface: "Aptos",
    wrap: "square",
  };
  return shape;
}

function addLinkText(s, label, uri, left, top, width, height, style = {}) {
  const shape = addText(s, label, left, top, width, height, {
    fontSize: style.fontSize ?? 13,
    bold: style.bold ?? false,
    color: C.blue,
  });
  try {
    shape.text.get(label).link = { uri, isExternal: true };
    shape.text.get(label).underline = "sng";
  } catch {
    // Linking is best-effort; the visible file path remains on the slide.
  }
  return shape;
}

function line(s, left, top, width, fill = C.line) {
  s.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: 2 },
    fill,
    line: { style: "solid", fill, width: 0 },
  });
}

function panel(s, left, top, width, height, fill = C.panel, stroke = C.line) {
  return s.shapes.add({
    geometry: "roundRect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: stroke, width: 1 },
    borderRadius: "rounded-lg",
  });
}

function slide(title, kicker = "AI-Native Self-Healing O-RAN Digital Twin") {
  const s = deck.slides.add();
  s.background.fill = C.bg;
  addText(s, kicker, 56, 30, 780, 24, { fontSize: 12, bold: true, color: C.blue });
  addText(s, title, 56, 58, 1090, 58, { fontSize: 35, bold: true });
  line(s, 56, 122, 1168);
  addText(s, "Linked to current expert CSV pack and dataset template files", 56, 684, 620, 18, {
    fontSize: 10,
    color: "slate-500",
  });
  return s;
}

function bullets(s, items, left, top, width, gap = 34, style = {}) {
  items.forEach((item, i) => {
    const y = top + i * gap;
    s.shapes.add({
      geometry: "ellipse",
      position: { left, top: y + 9, width: 8, height: 8 },
      fill: style.accent ?? C.blue,
      line: { style: "solid", fill: style.accent ?? C.blue, width: 0 },
    });
    addText(s, item, left + 20, y, width - 20, gap - 2, {
      fontSize: style.fontSize ?? 18,
      color: style.color ?? C.ink,
      bold: style.bold ?? false,
    });
  });
}

function miniTable(s, rows, left, top, width, rowH, colWidths, opts = {}) {
  const font = opts.fontSize ?? 11;
  rows.forEach((row, r) => {
    let x = left;
    const fill = r === 0 ? C.dark : r % 2 ? C.panel : C.faint;
    const color = r === 0 ? "white" : C.ink;
    row.forEach((cell, c) => {
      const w = colWidths[c] ?? (width / row.length);
      s.shapes.add({
        geometry: "rect",
        position: { left: x, top: top + r * rowH, width: w, height: rowH },
        fill,
        line: { style: "solid", fill: C.line, width: 1 },
      });
      addText(s, String(cell ?? "").slice(0, opts.maxChars ?? 80), x + 6, top + r * rowH + 5, w - 12, rowH - 8, {
        fontSize: r === 0 ? Math.max(10, font - 1) : font,
        color,
        bold: r === 0,
      });
      x += w;
    });
  });
}

function selectColumns(rows, names) {
  const header = rows[0];
  const idx = names.map((name) => header.indexOf(name));
  return rows.map((row) => idx.map((i, col) => (i >= 0 ? row[i] : col === 0 ? names[col] : "")));
}

function setHeader(rows, labels) {
  return [labels, ...rows.slice(1)];
}

function pathNote(s, label, p, top) {
  const rel = path.relative(ROOT, p).replaceAll("\\", "/");
  addText(s, label, 56, top, 210, 22, { fontSize: 12, bold: true, color: C.muted });
  addLinkText(s, rel, `file:///${p.replaceAll("\\", "/")}`, 270, top, 860, 22, { fontSize: 12 });
}

function kpi(s, label, value, left, top, width, color = C.blue) {
  panel(s, left, top, width, 106);
  addText(s, value, left + 18, top + 18, width - 36, 42, { fontSize: 32, bold: true, color });
  addText(s, label, left + 18, top + 68, width - 36, 24, { fontSize: 13, color: C.muted });
}

// 1
{
  const s = deck.slides.add();
  s.background.fill = C.dark;
  addText(s, "AI-Native Self-Healing O-RAN", 64, 70, 980, 70, { fontSize: 46, bold: true, color: "white" });
  addText(s, "Complete Workflow, Evidence Pack, and Dataset Requirements", 64, 148, 980, 38, {
    fontSize: 24,
    color: "slate-200",
  });
  line(s, 64, 218, 1080, C.cyan);
  addText(s, "What we built", 64, 270, 260, 28, { fontSize: 18, bold: true, color: C.cyan });
  bullets(
    s,
    [
      "Digital twin + AI/ML anomaly detection for O-RAN KPI streams",
      "RCA + guarded healing recommendations with xApp-style output",
      "FlexRIC/KPM-style evidence, controlled fault replay, and CSV artifacts",
      "Clear next data requirement for production-grade validation",
    ],
    68,
    314,
    780,
    40,
    { fontSize: 20, color: "white", accent: C.cyan },
  );
  panel(s, 890, 286, 270, 170, "#0f172a", "#334155");
  addText(s, "Open first", 914, 312, 220, 24, { fontSize: 16, bold: true, color: "white" });
  addText(s, "01_FINAL_PRESENTATION.pptx\nthen this workflow deck\nthen linked CSV evidence", 914, 350, 220, 82, {
    fontSize: 16,
    color: "slate-200",
  });
  addText(s, "Prepared from local project evidence only", 64, 668, 520, 20, { fontSize: 11, color: "slate-400" });
}

// 2
{
  const s = slide("Project In One View");
  kpi(s, "Final decision rows", "71,900", 70, 158, 245, C.blue);
  kpi(s, "Training rows", "431,400", 335, 158, 245, C.green);
  kpi(s, "Benchmark test rows", "6,250", 600, 158, 245, C.purple);
  kpi(s, "Data quality events", "0", 865, 158, 245, C.green);
  bullets(
    s,
    [
      "Input: FlexRIC/Open RAN KPM-style telemetry, replay CSVs, controlled fault windows",
      "Core: normalizer, digital twin state engine, AI anomaly scoring, RCA, healing policy",
      "Output: auditable xApp-style decision rows, reports, expert CSVs, model benchmarks",
      "Honest boundary: demo/research prototype, not a production live operator RAN controller",
    ],
    76,
    318,
    1030,
    43,
    { fontSize: 20 },
  );
  pathNote(s, "Evidence index", csvPath("02_EXPERT_CSV_INDEX.csv"), 626);
}

// 3
{
  const s = slide("Where This Fits In O-RAN");
  const blocks = [
    ["O-RU / Low-PHY", "RF, antenna, fronthaul\nKPIs: RSRP, RSRQ, timing, beam indicators"],
    ["O-DU / MAC / RLC", "Scheduling, PRBs, retransmission\nKPIs: PRB util, CQI, HARQ, RLC buffer"],
    ["O-CU / RRC / PDCP", "Mobility, sessions, user-plane\nKPIs: handover, drops, PDCP delay"],
    ["5G Core / UPF", "AMF/SMF/UPF and transport\nKPIs: N3/N6 RTT, packet drop, sessions"],
    ["Near-RT RIC", "xApp loop and E2/KPM interface\nOur output: xApp-style decisions"],
    ["SMO / Non-RT RIC", "Policies, model lifecycle, reports\nOur output: model registry and evidence"],
  ];
  let x = 58;
  blocks.forEach((b, i) => {
    const y = i < 3 ? 165 : 405;
    if (i === 3) x = 58;
    panel(s, x, y, 360, 172, "white", i === 4 ? C.blue : C.line);
    addText(s, b[0], x + 18, y + 18, 316, 28, { fontSize: 19, bold: true, color: i === 4 ? C.blue : C.ink });
    addText(s, b[1], x + 18, y + 58, 316, 92, { fontSize: 15, color: C.muted });
    x += 390;
  });
}

// 4
{
  const s = slide("Complete Workflow");
  const steps = [
    ["1", "Telemetry", "FlexRIC/KPM, replay CSV, OAI-style logs"],
    ["2", "Normalize", "Common KPI schema"],
    ["3", "Twin state", "Cell, slice, service health"],
    ["4", "AI detect", "Anomaly + risk score"],
    ["5", "RCA", "Likely root cause"],
    ["6", "Heal", "Action + guardrail"],
    ["7", "Evidence", "CSV, JSON, PPT, SQLite"],
  ];
  steps.forEach((st, i) => {
    const left = 62 + i * 168;
    panel(s, left, 210, 136, 190, i === 3 ? "#dbeafe" : "white", i === 3 ? C.blue : C.line);
    addText(s, st[0], left + 15, 226, 34, 32, { fontSize: 24, bold: true, color: C.blue });
    addText(s, st[1], left + 15, 270, 108, 28, { fontSize: 17, bold: true });
    addText(s, st[2], left + 15, 314, 106, 60, { fontSize: 13, color: C.muted });
    if (i < steps.length - 1) addText(s, "→", left + 142, 282, 30, 30, { fontSize: 30, bold: true, color: C.cyan });
  });
  addText(s, "The important idea: every raw source becomes the same KPI vector before AI/RCA logic sees it.", 88, 470, 1040, 40, {
    fontSize: 22,
    bold: true,
    color: C.ink,
  });
  pathNote(s, "Decision CSV", csvPath("07_FULL_FLEXRIC_DECISION_ROWS.csv"), 626);
}

// 5
{
  const s = slide("Actual Example: Backhaul Degradation");
  panel(s, 64, 156, 510, 440);
  addText(s, "Input KPI row symptoms", 90, 184, 420, 26, { fontSize: 22, bold: true });
  bullets(
    s,
    [
      "Radio signal acceptable: RSRP/RSRQ/RSSI not the main issue",
      "PRB utilization not extreme, so congestion is not dominant",
      "N3/N6 RTT and transport jitter are high",
      "Throughput drops while transport delay rises",
      "Expected root cause: backhaul_degradation",
    ],
    94,
    235,
    430,
    49,
    { fontSize: 18 },
  );
  panel(s, 626, 156, 520, 440, "#ecfeff", "#bae6fd");
  addText(s, "Decision produced by the pipeline", 652, 184, 430, 26, { fontSize: 22, bold: true, color: C.cyan });
  miniTable(
    s,
    [
      ["Field", "Example value"],
      ["anomaly_detected", "TRUE"],
      ["risk_score", "high, e.g. 0.82"],
      ["root_cause", "backhaul_degradation"],
      ["healing_action", "reroute_transport_path"],
      ["automation_decision", "allow_with_monitoring"],
      ["ric_control_type", "a1_policy / xApp-style output"],
    ],
    652,
    238,
    450,
    38,
    [180, 270],
    { fontSize: 13, maxChars: 42 },
  );
}

// 6
{
  const s = slide("Why The RCA Says Backhaul, Not Radio");
  const rows = [
    ["Observed KPI pattern", "Interpretation"],
    ["Bad RSRP/RSRQ/SINR", "Radio link degradation"],
    ["Very high PRB use + queue delay", "Cell congestion"],
    ["High handover failure / ping-pong", "Mobility instability"],
    ["High packet loss with drops", "Packet-loss degradation"],
    ["High N3/N6 RTT + jitter while radio is okay", "Backhaul degradation"],
  ];
  miniTable(s, rows, 92, 166, 1040, 54, [430, 610], { fontSize: 17, maxChars: 80 });
  addText(
    s,
    "Detection answers: is something wrong? RCA answers: what is most likely wrong? Healing answers: what should the system recommend next?",
    108,
    520,
    1000,
    58,
    { fontSize: 23, bold: true, color: C.ink },
  );
}

// 7
{
  const s = slide("Controlled Fault Replay Results");
  const rows = selectColumns(controlledWindows, [
    "window_id",
    "fault_type",
    "start_s",
    "end_s",
    "detected_rows",
    "detection_coverage",
    "detection_latency_s",
    "rca_accuracy_when_detected",
    "healing_accuracy_when_detected",
  ]);
  const displayRows = setHeader(rows, ["window", "fault", "start", "end", "detected", "coverage", "latency", "RCA acc.", "healing acc."]);
  miniTable(s, displayRows, 74, 158, 1080, 48, [85, 190, 70, 70, 95, 130, 130, 155, 155], {
    fontSize: 11,
    maxChars: 34,
  });
  addText(
    s,
    "Interpretation: detection coverage is perfect in the clean replay windows; RCA/healing is lower for overlapping symptom families such as backhaul vs packet-loss transport problems.",
    78,
    530,
    1060,
    58,
    { fontSize: 20, bold: true },
  );
  pathNote(s, "Fault CSV", csvPath("06_CONTROLLED_FAULT_WINDOW_RESULTS.csv"), 626);
}

// 8
{
  const s = slide("Model Benchmark: What Each Result Means");
  const rows = selectColumns(modelMetrics, [
    "model",
    "tp",
    "fp",
    "fn",
    "tn",
    "precision",
    "recall",
    "f1_score",
    "false_positive_rate",
    "false_negative_rate",
  ]);
  miniTable(s, rows, 74, 154, 1080, 50, [270, 70, 70, 70, 70, 110, 100, 105, 125, 140], {
    fontSize: 10,
    maxChars: 34,
  });
  bullets(
    s,
    [
      "Online self-learning performs strongly in the controlled setup because the replay fault shape is structured.",
      "Isolation Forest catches unseen anomalies better because it does not need exact fault-class labels.",
      "Random Forest/Gradient Boosting can fail on held-out fault families because supervised models learn known labels.",
    ],
    76,
    520,
    1050,
    35,
    { fontSize: 17 },
  );
  pathNote(s, "Model CSV", csvPath("04_MODEL_BENCHMARK_METRICS.csv"), 646);
}

// 9
{
  const s = slide("Row Counts Are Synced, But They Mean Different Things");
  miniTable(s, reconciliation, 58, 152, 1164, 48, [190, 250, 100, 280, 344], { fontSize: 11, maxChars: 64 });
  addText(
    s,
    "Use this slide if someone asks why they see 71,900, 431,400, or 6,250 in different sheets.",
    84,
    558,
    1010,
    30,
    { fontSize: 22, bold: true, color: C.amber },
  );
  pathNote(s, "Count CSV", csvPath("08_PIPELINE_ROW_COUNT_RECONCILIATION.csv"), 626);
}

// 10
{
  const s = slide("CSV Evidence Pack: What Is Linked");
  miniTable(s, reportSummary, 70, 152, 470, 40, [235, 235], { fontSize: 12, maxChars: 46 });
  panel(s, 594, 152, 560, 314);
  addText(s, "Show-first CSV order", 620, 178, 410, 26, { fontSize: 21, bold: true });
  bullets(
    s,
    [
      "03 report summary: headline run metrics",
      "04 benchmark metrics: model-by-model performance",
      "05/06 controlled faults: answer-key validation",
      "07 decision rows: full xApp-style output stream",
      "08 reconciliation: explains row counts",
      "09 column guide: explains every expert CSV column",
    ],
    624,
    224,
    480,
    34,
    { fontSize: 16 },
  );
  pathNote(s, "CSV index", csvPath("02_EXPERT_CSV_INDEX.csv"), 546);
  pathNote(s, "Column guide", csvPath("09_CSV_COLUMN_GUIDE.csv"), 574);
}

// 11
{
  const s = slide("Decision Rows: Column Snippet");
  const rows = selectColumns(decisionSample, [
    "row_id",
    "cell_id",
    "service_class",
    "anomaly_detected",
    "risk_score",
    "root_cause",
    "healing_action",
    "automation_decision",
    "approved",
    "ric_control_type",
  ]);
  const displayRows = setHeader(rows, ["row", "cell", "service", "anomaly", "risk", "root cause", "healing", "decision", "approved", "RIC"]);
  miniTable(s, displayRows, 70, 160, 1088, 56, [60, 88, 110, 128, 90, 150, 160, 170, 72, 60], {
    fontSize: 10,
    maxChars: 30,
  });
  bullets(
    s,
    [
      "Each row is one engine decision for one normalized KPI record.",
      "The columns carry detection, risk, root cause, healing action, automation safety, and RIC/xApp intent.",
      "This is the main spreadsheet to show when asked: what did your system output?",
    ],
    76,
    430,
    1030,
    40,
    { fontSize: 20 },
  );
  pathNote(s, "Full decision rows", csvPath("07_FULL_FLEXRIC_DECISION_ROWS.csv"), 626);
}

// 12
{
  const s = slide("Training Data We Used");
  kpi(s, "Corrected base rows", "71,900", 86, 164, 250, C.blue);
  kpi(s, "Scenario expansion", "× 6", 366, 164, 250, C.purple);
  kpi(s, "Final training rows", "431,400", 646, 164, 250, C.green);
  bullets(
    s,
    [
      "Training pack sits inside the show-first folder so reviewers can inspect it directly.",
      "Rows include multi-scenario augmentation for normal, congestion, radio, packet-loss, backhaul, and handover behavior.",
      "This supports prototype learning and benchmarking, but production claims need real lab/operator truth labels.",
    ],
    92,
    330,
    980,
    42,
    { fontSize: 20 },
  );
  pathNote(s, "Training folder", path.join(SHOW_FIRST_DIR, "10_training_data_what_models_trained_on"), 626);
}

// 13
{
  const s = slide("Dataset Required For Production-Grade Claims");
  const reqs = [
    ["Data family", "Why required"],
    ["O-RAN testbed / OAI / srsRAN", "Real RAN stack behavior, not only emulator-shaped values"],
    ["FlexRIC / Near-RT RIC KPM", "Actual RIC/E2/KPM integration evidence"],
    ["O-CU / O-DU / O-RU KPIs", "Localize whether issue is radio, scheduler, mobility, fronthaul, or user plane"],
    ["5G Core + UPF + transport", "Separate RAN faults from core/backhaul faults"],
    ["Controlled fault labels", "Research-grade answer key with start/end times"],
    ["Healing outcomes", "Measure whether actions improved recovery, not just detection"],
  ];
  miniTable(s, reqs, 74, 154, 1060, 58, [340, 720], { fontSize: 15, maxChars: 95 });
}

// 14
{
  const s = slide("Dataset Template Pack To Send");
  const files = [
    ["Template CSV", "Purpose"],
    ["01_main_kpi_telemetry_template.csv", "Primary row-wise KPI training table"],
    ["02_fault_event_label_template.csv", "Answer-key fault labels with start/end time"],
    ["03_healing_action_outcome_template.csv", "Action and recovery result table"],
    ["04_ric_xapp_log_template.csv", "RIC/xApp/control-loop evidence table"],
    ["05_network_inventory_context_template.csv", "Topology/context table"],
    ["06_data_dictionary_minimum.csv", "Minimum meaning of critical columns"],
  ];
  miniTable(s, files, 86, 156, 1030, 58, [420, 610], { fontSize: 16, maxChars: 78 });
  pathNote(s, "Dataset ZIP", path.join(ROOT, "outputs", "email_dataset_update", "dataset_template_precise.zip"), 626);
}

// 15
{
  const s = slide("Main KPI Telemetry Template: Column Groups");
  const groups = [
    ["Identity/time", "timestamp, window_sec, site_id, cell_id, gnb_id, du_id, cu_id, ru_id, ue_id_hash"],
    ["Service context", "slice_id, qci_or_5qi, service_class, scenario_id, experiment_id, traffic_profile"],
    ["Radio/PHY", "rsrp_dbm, rsrq_db, rssi_dbm, sinr_db, cqi, mcs, bler_pct, harq_retx_pct"],
    ["Beam/RF", "beam_id, beam_index, beam_switch_count, beam_failure_count, precoder_id, rank_indicator"],
    ["DU/MAC/RLC", "dl_prb_util_pct, ul_prb_util_pct, mac_scheduler_delay_ms, rlc_buffer_kbytes"],
    ["CU/Core/Transport", "handover_fail_pct, n3_rtt_ms, n6_rtt_ms, packet_loss_pct, upf_packet_drop_pct"],
    ["Labels", "fault_event_id, fault_active, fault_type, label_source"],
  ];
  miniTable(s, [["Group", "Representative columns"], ...groups], 46, 150, 1188, 64, [245, 943], {
    fontSize: 13,
    maxChars: 130,
  });
  pathNote(s, "Main template", path.join(ROOT, "outputs", "dataset_template_precise", "01_main_kpi_telemetry_template.csv"), 628);
}

// 16
{
  const s = slide("Template Snippets: Labels, Healing, xApp, Inventory");
  const cards = [
    [
      "Fault labels",
      C.blue,
      "Answer key for detection/RCA.",
      datasetLabels[0].slice(0, 10).join(", "),
    ],
    [
      "Healing outcomes",
      C.green,
      "Shows whether recovery action worked.",
      datasetHealing[0].join(", "),
    ],
    [
      "RIC / xApp logs",
      C.purple,
      "Connects model decision to control-loop evidence.",
      datasetXapp[0].join(", "),
    ],
    [
      "Network inventory",
      C.amber,
      "Topology and deployment context.",
      datasetInventory[0].slice(0, 13).join(", "),
    ],
  ];
  cards.forEach((card, i) => {
    const left = i % 2 === 0 ? 78 : 660;
    const top = i < 2 ? 158 : 392;
    panel(s, left, top, 500, 172, "white", card[1]);
    addText(s, card[0], left + 22, top + 18, 420, 26, { fontSize: 22, bold: true, color: card[1] });
    addText(s, card[2], left + 22, top + 54, 420, 24, { fontSize: 15, bold: true });
    addText(s, card[3], left + 22, top + 90, 440, 58, { fontSize: 12, color: C.muted });
  });
  addText(
    s,
    "These four files prevent guesswork: they say what happened, what action was taken, whether recovery worked, and where in the topology it happened.",
    88,
    588,
    1040,
    34,
    { fontSize: 18, bold: true },
  );
}

// 17
{
  const s = slide("Current Claims vs Next Improvements");
  panel(s, 80, 158, 500, 390, "#ecfdf5", "#bbf7d0");
  addText(s, "Can claim now", 110, 188, 350, 28, { fontSize: 24, bold: true, color: C.green });
  bullets(
    s,
    [
      "AI/ML prototype for O-RAN KPI anomaly detection",
      "Digital twin state tracking and RCA/healing logic",
      "FlexRIC/KPM-style ingestion and xApp-style decisions",
      "Controlled timestamped fault replay evidence",
      "Expert-ready CSV and PPT evidence pack",
    ],
    116,
    244,
    400,
    44,
    { fontSize: 18, accent: C.green },
  );
  panel(s, 700, 158, 500, 390, "#fff7ed", "#fed7aa");
  addText(s, "Still needed for production claims", 730, 188, 420, 28, { fontSize: 24, bold: true, color: C.amber });
  bullets(
    s,
    [
      "2-hour or longer sustained run",
      "Live OAI/srsRAN gNB/nrUE + FlexRIC integration",
      "Real RF simulator or SDR-backed telemetry",
      "Operator/lab fault labels and recovery outcomes",
      "Real E2 actuation and physical beamforming control",
    ],
    736,
    244,
    400,
    44,
    { fontSize: 18, accent: C.amber },
  );
}

// 18
{
  const s = slide("How To Present This Deck");
  const order = [
    ["Step", "What to open", "Why"],
    ["1", "01_FINAL_PRESENTATION.pptx", "Main story"],
    ["2", "11_COMPLETE_WORKFLOW_AND_DATASET_REQUIREMENTS.pptx", "Detailed workflow and dataset proof"],
    ["3", "07_FULL_FLEXRIC_DECISION_ROWS.csv", "Actual system output rows"],
    ["4", "06_CONTROLLED_FAULT_WINDOW_RESULTS.csv", "Fault-injection validation"],
    ["5", "10_training_data_what_models_trained_on/", "Training data proof"],
    ["6", "dataset_template_precise.zip", "What we need next"],
  ];
  miniTable(s, order, 98, 158, 1010, 62, [100, 470, 440], { fontSize: 16, maxChars: 78 });
  addText(
    s,
    "Recommended closing line: the project is demo-ready and research-prototype ready; the next jump is lab/operator-grade data and live OAI/FlexRIC validation.",
    108,
    586,
    980,
    46,
    { fontSize: 20, bold: true, color: C.ink },
  );
}

for (const [index, s] of deck.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await deck.export({ slide: s, format: "png", scale: 1 });
  await fs.writeFile(path.join(PREVIEW_DIR, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await s.export({ format: "layout" });
  await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
}

const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(TMP_DIR, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(FINAL_PPTX);
await fs.copyFile(FINAL_PPTX, SHOW_FIRST_PPTX);

console.log(JSON.stringify({ FINAL_PPTX, SHOW_FIRST_PPTX, slides: deck.slides.items.length, PREVIEW_DIR, LAYOUT_DIR }, null, 2));
