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
const WORKSPACE = path.join(os.tmpdir(), "codex-presentations", THREAD_ID, "oran-expert-final");
const TMP_DIR = path.join(WORKSPACE, "tmp");
const PREVIEW_DIR = path.join(TMP_DIR, "preview");
const LAYOUT_DIR = path.join(TMP_DIR, "layout");
const QA_DIR = path.join(TMP_DIR, "qa");
const OUTPUT_DIR = path.join(ROOT, "outputs", "presentations");
const FINAL_PPTX = process.env.FINAL_PPTX || path.join(OUTPUT_DIR, "O-RAN_AI_Native_Self_Healing_Final_Expert_Review.pptx");

const C = {
  bg: "slate-50",
  ink: "slate-950",
  muted: "slate-600",
  line: "slate-200",
  panel: "white",
  blue: "sky-600",
  cyan: "cyan-500",
  green: "emerald-600",
  amber: "amber-500",
  red: "rose-600",
  dark: "slate-900",
};

const evidence = JSON.parse(await fs.readFile(path.join(ROOT, "outputs", "evidence", "controlled_fault_evaluation.json"), "utf8"));
const flexric = JSON.parse(await fs.readFile(path.join(ROOT, "outputs", "reports", "flexric_kpm_30min.json"), "utf8"));
const balanced = JSON.parse(await fs.readFile(path.join(ROOT, "outputs", "benchmarks", "flexric_kpm_30min_ml_benchmark_balanced.json"), "utf8"));

const modelDisplayName = {
  online_self_learning_v1: "Online self-learning",
  full_guarded_decision_engine_sample: "Guarded engine sample",
  isolation_forest_unsupervised: "Isolation Forest",
  random_forest_supervised: "Random Forest",
  gradient_boosting_supervised: "Gradient Boosting",
};

await fs.mkdir(PREVIEW_DIR, { recursive: true });
await fs.mkdir(LAYOUT_DIR, { recursive: true });
await fs.mkdir(QA_DIR, { recursive: true });
await fs.mkdir(OUTPUT_DIR, { recursive: true });

await fs.writeFile(
  path.join(TMP_DIR, "source-notes.txt"),
  [
    "Source notes for O-RAN expert final updated deck",
    "",
    "Sources:",
    "- PROJECT_INDEX.md: expert entry path and honest claims.",
    "- docs/FINAL_EVIDENCE_REPORT.md: final evidence, FlexRIC 30-minute metrics, controlled fault injection metrics.",
    "- docs/PAPER_CITATION_INTEGRATION_MAP.md: paper/standard-to-module mapping.",
    "- outputs/reports/flexric_kpm_30min.json: 30-minute FlexRIC KPM decision summary.",
    "- outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced.json: balanced benchmark metrics.",
    "- outputs/evidence/controlled_fault_evaluation.json: timestamped controlled fault-injection evaluation.",
    "- assets/oran_reference_architecture_topology.png: architecture visual.",
    "- assets/final_system_architecture_block_diagram.png: project system architecture visual.",
    "",
    "No external assets were fetched. All images are local project assets.",
  ].join("\n"),
  "utf8",
);

await fs.writeFile(
  path.join(TMP_DIR, "slide-plan.txt"),
  [
    "Deck plan: 13 editable slides, 16:9 1280x720.",
    "Palette: slate base, sky/cyan for O-RAN control, emerald for proof, amber for caveats.",
    "Fonts: Aptos Display/Aptos fallback. Use 44-60 px titles, 18-22 px body, 36-60 px KPIs.",
    "Audience: PRISM/expert reviewers/interviewers.",
    "Purpose: present final prototype, evidence, AI/ML placement, citations, and boundaries.",
  ].join("\n"),
  "utf8",
);

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function slide(title, kicker = "") {
  const s = deck.slides.add();
  s.background.fill = C.bg;
  addText(s, kicker || "AI-Native Self-Healing O-RAN Digital Twin", 64, 34, 720, 24, {
    fontSize: 12,
    bold: true,
    color: C.blue,
  });
  addText(s, title, 64, 62, 1020, 58, {
    fontSize: 36,
    bold: true,
    color: C.ink,
  });
  addLine(s, 64, 124, 1152, C.line);
  footer(s);
  return s;
}

function footer(s) {
  addText(s, "Evidence-backed prototype | FlexRIC KPM + AI/ML + Digital Twin + xApp-style output", 64, 682, 760, 20, {
    fontSize: 10,
    color: "slate-500",
  });
}

function addText(s, text, left, top, width, height, style = {}) {
  const box = s.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = String(text);
  box.text.style = {
    fontSize: style.fontSize ?? 18,
    bold: style.bold ?? false,
    color: style.color ?? C.ink,
    alignment: style.alignment ?? "left",
    typeface: style.typeface ?? "Aptos",
  };
  return box;
}

function addLine(s, left, top, width, fill = C.line) {
  s.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: 2 },
    fill,
    line: { style: "solid", fill, width: 0 },
  });
}

function panel(s, left, top, width, height, fill = C.panel, line = C.line) {
  return s.shapes.add({
    geometry: "roundRect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: "rounded-lg",
  });
}

function kpi(s, label, value, left, top, width, accent = C.blue) {
  panel(s, left, top, width, 112);
  addText(s, value, left + 18, top + 22, width - 36, 42, {
    fontSize: 34,
    bold: true,
    color: accent,
  });
  addText(s, label, left + 18, top + 70, width - 36, 26, {
    fontSize: 14,
    color: C.muted,
  });
}

function bulletList(s, items, left, top, width, lineHeight = 33, opts = {}) {
  items.forEach((item, index) => {
    const y = top + index * lineHeight;
    s.shapes.add({
      geometry: "ellipse",
      position: { left, top: y + 9, width: 8, height: 8 },
      fill: opts.accent ?? C.blue,
      line: { style: "solid", fill: opts.accent ?? C.blue, width: 0 },
    });
    addText(s, item, left + 20, y, width - 20, lineHeight - 3, {
      fontSize: opts.fontSize ?? 18,
      color: opts.color ?? C.ink,
    });
  });
}

async function addImage(s, imagePath, left, top, width, height, alt, fit = "contain") {
  const bytes = await fs.readFile(imagePath);
  const contentType = imagePath.toLowerCase().endsWith(".png") ? "image/png" : "image/jpeg";
  s.images.add({
    blob: bytes,
    contentType,
    alt,
    fit,
    position: { left, top, width, height },
  });
}

function addTable(s, values, left, top, width, height, headerFill = C.dark) {
  const table = s.tables.add({
    rows: values.length,
    columns: values[0].length,
    left,
    top,
    width,
    height,
    values,
  });
  table.styleOptions = { headerRow: true, bandedRows: true };
  for (let r = 0; r < values.length; r++) {
    for (let c = 0; c < values[0].length; c++) {
      const cell = table.getCell(r, c);
      cell.text.style = {
        fontSize: r === 0 ? 12 : 13,
        bold: r === 0,
        color: r === 0 ? "white" : C.ink,
      };
    }
  }
  for (let c = 0; c < values[0].length; c++) {
    const cell = table.getCell(0, c);
    cell.fill = headerFill;
    cell.text.style = { fontSize: 12, bold: true, color: "white" };
  }
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  return table;
}

function bar(s, label, value, max, left, top, width, color) {
  addText(s, label, left, top, 240, 24, { fontSize: 14, color: C.ink, bold: true });
  panel(s, left + 250, top + 2, width, 20, "slate-100", "slate-200");
  s.shapes.add({
    geometry: "roundRect",
    position: { left: left + 250, top: top + 2, width: Math.max(3, (value / max) * width), height: 20 },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
    borderRadius: "rounded-md",
  });
  addText(s, String(value), left + 260 + width, top - 1, 90, 24, { fontSize: 13, color: C.muted });
}

// 1. Cover
{
  const s = deck.slides.add();
  s.background.fill = C.dark;
  addText(s, "AI-Native Self-Healing O-RAN Network", 68, 72, 940, 64, {
    fontSize: 44,
    bold: true,
    color: "white",
    typeface: "Aptos Display",
  });
  addText(s, "Digital Twin + FlexRIC KPM + AI/ML + Guarded xApp-style Healing", 72, 142, 930, 40, {
    fontSize: 24,
    color: "slate-200",
  });
  addText(s, "Expert final deck", 72, 45, 260, 22, { fontSize: 13, bold: true, color: C.cyan });
  kpi(s, "30-min FlexRIC decisions", "71.9K", 72, 278, 250, C.cyan);
  kpi(s, "Controlled fault F1", "1.00", 354, 278, 250, C.green);
  kpi(s, "False-positive rate", "0.00", 636, 278, 250, C.green);
  kpi(s, "RCA/healing accuracy", "0.876", 918, 278, 250, C.amber);
  addText(s, "Claim: AI/ML-assisted RAN assurance sandbox, not production operator RAN actuation.", 72, 608, 1020, 32, {
    fontSize: 18,
    color: "slate-300",
  });
}

// 2. What changed
{
  const s = slide("What This Final Version Proves", "Executive summary");
  bulletList(
    s,
    [
      "A digital twin mirrors O-RAN KPI state and evaluates risk before healing.",
      "FlexRIC KPM telemetry is ingested, normalized, processed, and audited.",
      "AI/ML models support anomaly detection, self-learning, and benchmark comparison.",
      "RCA and healing recommendations are guarded by drift, AML, policy, and safety gates.",
      "Controlled timestamped fault labels now test detection, RCA, and healing correctness.",
      "The folder has expert-facing index, evidence CSVs, and paper-to-module citation map.",
    ],
    92,
    178,
    1020,
    50,
    { accent: C.green, fontSize: 21 },
  );
}

// 3. Architecture AI placement
{
  const s = slide("Where AI/ML Sits In The O-RAN Architecture", "Architecture mapping");
  await addImage(s, path.join(ROOT, "assets", "oran_reference_architecture_topology.png"), 58, 158, 564, 430, "O-RAN reference architecture", "contain");
  panel(s, 660, 156, 520, 430);
  addText(s, "Correct expert statement", 690, 184, 440, 28, { fontSize: 22, bold: true, color: C.blue });
  addText(
    s,
    "AI is not embedded inside every protocol block. Instead, the AI-assisted digital twin consumes KPIs from RIC, CU, DU, RU, PHY, core, transport, and SMO domains, then performs anomaly detection, RCA, drift monitoring, and guarded healing recommendations.",
    690,
    230,
    440,
    156,
    { fontSize: 19, color: C.ink },
  );
  bulletList(
    s,
    ["Near-RT RIC: xApp-style decisions", "SMO/Non-RT RIC: governance and lifecycle", "CU/DU/RU/PHY/Core: KPI-driven fault signals"],
    690,
    420,
    420,
    38,
    { accent: C.cyan, fontSize: 18 },
  );
}

// 4. Closed loop
{
  const s = slide("Closed-Loop Self-Healing Flow", "Implementation flow");
  const steps = [
    ["Telemetry", "FlexRIC/Open RAN/simulated KPIs"],
    ["Digital Twin", "risk, SLA, slice and timing state"],
    ["AI/ML", "anomaly, self-learning, drift"],
    ["RCA", "root cause classification"],
    ["Healing", "safe action recommendation"],
    ["Audit", "CSV/JSONL/SQLite evidence"],
  ];
  steps.forEach(([a, b], i) => {
    const x = 70 + (i % 3) * 390;
    const y = 178 + Math.floor(i / 3) * 190;
    panel(s, x, y, 320, 116);
    addText(s, a, x + 24, y + 22, 260, 28, { fontSize: 24, bold: true, color: i === 2 ? C.green : C.blue });
    addText(s, b, x + 24, y + 62, 270, 38, { fontSize: 16, color: C.muted });
  });
  addText(s, "Shared engine: oran_twin/engine.py", 72, 610, 600, 32, { fontSize: 20, bold: true, color: C.ink });
}

// 5. AIML models
{
  const s = slide("AI/ML Models Actually Used", "Model transparency");
  addTable(
    s,
    [
      ["Model / method", "Role in project", "Status"],
      ["Online self-learning", "Learns KPI baselines and RCA centroids", "Implemented"],
      ["Isolation Forest", "Unsupervised anomaly benchmark", "Implemented"],
      ["Random Forest", "Supervised benchmark", "Implemented"],
      ["Gradient Boosting", "Supervised benchmark", "Implemented"],
      ["Drift monitor", "Detects distribution shift and lifecycle state", "Implemented"],
      ["Deep neural model", "Future sequence/deep model path", "Deferred"],
    ],
    72,
    164,
    1136,
    360,
  );
  panel(s, 72, 560, 1136, 62, "amber-50", "amber-200");
  addText(s, "Use this wording: AI/ML-based anomaly detection, online self-learning, and benchmarked classical ML models. Do not claim deep learning.", 96, 580, 1080, 28, {
    fontSize: 18,
    bold: true,
    color: "amber-900",
  });
}

// 6. FlexRIC KPM evidence
{
  const s = slide("FlexRIC KPM 30-Minute Evidence", "Live/lab telemetry evidence");
  const summary = flexric.jsonl_decision_summary;
  kpi(s, "Decision rows", String(summary.records.toLocaleString()), 72, 168, 250, C.blue);
  kpi(s, "Anomalies", String(summary.anomaly_records), 354, 168, 250, C.amber);
  kpi(s, "Data quality events", "0", 636, 168, 250, C.green);
  kpi(s, "SQLite feature rows", String(flexric.sqlite_summary.feature_rows.toLocaleString()), 918, 168, 250, C.cyan);
  addTable(
    s,
    [
      ["Root cause", "Rows"],
      ["normal", String(summary.root_cause_counts.normal ?? 0)],
      ["backhaul_degradation", String(summary.root_cause_counts.backhaul_degradation ?? 0)],
      ["Healing action", "reroute_transport_path for anomalies"],
      ["RIC output", "a1_policy for anomaly decisions"],
    ],
    144,
    340,
    990,
    224,
  );
}

// 7. Balanced ML benchmark
{
  const s = slide("Balanced Model Benchmark", "Normal + held-out fault rows");
  const profile = balanced.dataset_profile;
  addTable(
    s,
    [
      ["Split", "Records", "Fault rows", "Normal rows"],
      ["Train", String(profile.train.records), String(profile.train.fault_records), String(profile.train.normal_records)],
      ["Test", String(profile.test.records), String(profile.test.fault_records), String(profile.test.normal_records)],
    ],
    88,
    164,
    520,
    150,
  );
  const models = balanced.benchmarks.filter((m) => m.precision !== undefined).slice(0, 5);
  addTable(
    s,
    [
      ["Model", "Precision", "Recall", "F1", "FPR"],
      ...models.map((m) => [modelDisplayName[m.name] ?? m.name, String(m.precision), String(m.recall), String(m.f1_score), String(m.false_positive_rate)]),
    ],
    88,
    350,
    1100,
    250,
  );
}

// 8. Controlled fault injection
{
  const s = slide("Controlled Fault-Injection Validation", "Timestamped answer-key evaluation");
  const windows = evidence.window_results;
  addText(s, "The evaluator injects known faults into normalized FlexRIC KPM rows, logs start/end timestamps, and checks whether the engine detects the expected fault and healing action.", 72, 154, 1060, 54, {
    fontSize: 20,
    color: C.ink,
  });
  windows.forEach((w, i) => {
    const x = 110 + i * 210;
    panel(s, x, 264, 168, 126, i % 2 === 0 ? "white" : "slate-100");
    addText(s, w.fault_type.replaceAll("_", " "), x + 12, 286, 144, 48, { fontSize: 15, bold: true, color: C.ink });
    addText(s, `${w.start_s}s - ${w.end_s}s`, x + 12, 344, 130, 22, { fontSize: 14, color: C.muted });
  });
  kpi(s, "Precision", String(evidence.precision), 150, 474, 210, C.green);
  kpi(s, "Recall", String(evidence.recall), 390, 474, 210, C.green);
  kpi(s, "F1-score", String(evidence.f1_score), 630, 474, 210, C.green);
  kpi(s, "False-positive rate", String(evidence.false_positive_rate), 870, 474, 260, C.green);
}

// 9. RCA/healing outcome by window
{
  const s = slide("RCA And Healing Correctness", "Controlled fault results");
  addTable(
    s,
    [
      ["Fault", "Detection coverage", "Latency", "RCA accuracy", "Healing accuracy"],
      ...evidence.window_results.map((w) => [
        w.fault_type,
        String(w.detection_coverage),
        String(w.detection_latency_s ?? "not detected"),
        String(w.rca_accuracy_when_detected),
        String(w.healing_accuracy_when_detected),
      ]),
    ],
    72,
    158,
    1136,
    300,
  );
  addText(s, "Aggregate RCA/healing accuracy is 0.8761. Backhaul and handover have partial root-cause ambiguity under replayed KPM conditions; this is disclosed rather than hidden.", 92, 500, 1040, 60, {
    fontSize: 20,
    color: C.ink,
  });
}

// 10. Paper integration
{
  const s = slide("Literature Was Implemented, Not Just Cited", "Paper-to-module traceability");
  addTable(
    s,
    [
      ["Paper/theme", "Implemented module"],
      ["O-RAN architecture / RIC", "xapp_runner.py, oran_twin/engine.py"],
      ["Digital twin networks / ZSM", "digital_twin.py, dtn_orchestrator.py, policy_orchestrator.py"],
      ["xApp conflict / distillation", "conflict_manager.py, xapp_distillation_policy.json"],
      ["Drift handling", "drift_monitor.py"],
      ["AML threat analysis", "security_guard.py, automation_safety.py"],
      ["SpotLight spectrum anomaly", "spectrum_monitor.py"],
      ["E2E network slicing DT", "slice_impact.py"],
      ["TSN/STRIDE timing twin", "timing_security.py"],
    ],
    72,
    152,
    1136,
    416,
  );
  addText(s, "Full citation map: docs/PAPER_CITATION_INTEGRATION_MAP.md", 72, 602, 840, 28, {
    fontSize: 18,
    bold: true,
    color: C.blue,
  });
}

// 11. Expert evidence files
{
  const s = slide("Evidence Files To Show Experts", "Presentation-ready artifact map");
  addTable(
    s,
    [
      ["Artifact", "Purpose"],
      ["PROJECT_INDEX.md", "Start here; explains what to open first"],
      ["docs/FINAL_EVIDENCE_REPORT.md", "Main technical evidence and limitations"],
      ["outputs/evidence/flexric_kpm_30min_decisions.csv", "71,900-row decision CSV"],
      ["outputs/evidence/controlled_fault_decisions.csv", "2,400-row labelled fault evaluation CSV"],
      ["outputs/reports/flexric_kpm_30min.json", "30-minute FlexRIC KPM report"],
      ["outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced.json", "Balanced ML benchmark"],
    ],
    72,
    154,
    1136,
    386,
  );
}

// 12. Honest claim boundary
{
  const s = slide("What To Claim And What Not To Claim", "Defensible expert framing");
  panel(s, 72, 164, 520, 360, "emerald-50", "emerald-200");
  addText(s, "Safe claims", 104, 196, 420, 32, { fontSize: 26, bold: true, color: "emerald-800" });
  bulletList(
    s,
    [
      "AI/ML-assisted O-RAN digital twin prototype",
      "FlexRIC KPM ingestion and decision evidence",
      "RCA and guarded healing recommendations",
      "Controlled fault-injection validation",
      "CSV/JSON/SQLite audit trail",
    ],
    108,
    250,
    420,
    42,
    { accent: C.green, fontSize: 18 },
  );
  panel(s, 688, 164, 520, 360, "amber-50", "amber-200");
  addText(s, "Avoid overclaims", 720, 196, 420, 32, { fontSize: 26, bold: true, color: "amber-900" });
  bulletList(
    s,
    [
      "Not production operator-RAN actuation",
      "Not deep learning in active path yet",
      "Not independent operator fault truth",
      "2-hour run still recommended for final showcase",
      "Real E2 control is future work",
    ],
    724,
    250,
    420,
    42,
    { accent: C.amber, fontSize: 18 },
  );
}

// 13. Next step
{
  const s = slide("Final Status", "Ready except optional 2-hour run");
  addText(s, "Done for demo, resume, and expert-review level.", 92, 178, 960, 48, {
    fontSize: 34,
    bold: true,
    color: C.green,
  });
  bulletList(
    s,
    [
      "Project goals satisfied at prototype level.",
      "Presentation folder cleaned and indexed.",
      "AI/ML usage is documented and defensible.",
      "Controlled fault-injection evaluation is implemented.",
      "Only major optional upgrade: 2-hour FlexRIC KPM stability run.",
    ],
    104,
    280,
    980,
    48,
    { accent: C.green, fontSize: 22 },
  );
  panel(s, 92, 582, 1020, 54, "slate-100", "slate-300");
  addText(s, ".\\scripts\\run_kpm_evidence_pipeline.ps1 -DurationSeconds 7200 -RunName flexric_kpm_2hr -SkipPatch", 116, 600, 960, 24, {
    fontSize: 17,
    bold: true,
    color: C.dark,
  });
}

for (const [index, s] of deck.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  const png = await deck.export({ slide: s, format: "png", scale: 1 });
  await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), png);
  const layout = await s.export({ format: "layout" });
  await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.layout.json`), await layout.text(), "utf8");
}

const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await writeBlob(path.join(PREVIEW_DIR, "deck-montage.webp"), montage);

await fs.writeFile(
  path.join(QA_DIR, "visual-qa.txt"),
  [
    "Visual QA checklist",
    "- Rendered all slides to PNG.",
    "- Rendered deck montage.",
    "- Slides use editable text, tables, shapes, charts/visual shapes, and local image bytes.",
    "- No external images fetched.",
    "- Main factual claims trace to source-notes.txt.",
    "- Caveats are included explicitly.",
  ].join("\n"),
  "utf8",
);

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(FINAL_PPTX);
console.log(JSON.stringify({ finalPptx: FINAL_PPTX, slides: deck.slides.items.length, workspace: WORKSPACE }, null, 2));

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}
