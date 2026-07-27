import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "file:///C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), "..", "..");
const PROJECT = path.join(ROOT, "oran_splane_selfhealing");
const OUT = path.join(ROOT, "Project_FullReview_Presentation.pptx");
const QA = path.join(PROJECT, "results", "full_review_deck_qa");

const C = {
  navy: "0B1324",
  navy2: "111C32",
  ink: "172033",
  muted: "526070",
  light: "F7F9FC",
  panel: "FFFFFF",
  line: "D6DEE8",
  danger: "E45757",
  good: "16A36D",
  accent: "2F80ED",
  amber: "F2A541",
  violet: "6F5BD7",
};

const W = 1280;
const H = 720;
const M = 58;

function csvRows(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const cells = [];
    let cur = "";
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') quoted = !quoted;
      else if (ch === "," && !quoted) {
        cells.push(cur);
        cur = "";
      } else cur += ch;
    }
    cells.push(cur);
    return Object.fromEntries(headers.map((h, i) => [h, cells[i]]));
  });
}

async function readFacts() {
  const disc = csvRows(await fs.readFile(path.join(PROJECT, "results", "discriminator_metrics.csv"), "utf8"));
  const bench = csvRows(await fs.readFile(path.join(PROJECT, "results", "benchmark_results.csv"), "utf8"));
  const windows = csvRows(await fs.readFile(path.join(PROJECT, "dataset", "splane_windows.csv"), "utf8"));
  const counts = {};
  for (const r of windows) counts[r.label] = (counts[r.label] || 0) + 1;
  const summary = await fs.readFile(path.join(PROJECT, "results", "SUMMARY.md"), "utf8");
  const realismPath = path.join(PROJECT, "results", "REALISM_NOTES.md");
  let realism = "";
  try {
    realism = await fs.readFile(realismPath, "utf8");
  } catch {
    realism = "REALISM_NOTES.md was not present when this deck was generated.";
  }
  return {
    disc: disc.find((r) => r.model === "random_forest_h0_h1"),
    baseline: disc.find((r) => r.model.includes("detection_only")),
    bench,
    governed: bench.find((r) => r.method === "governed_loop"),
    counts,
    total: windows.length,
    summary,
    realism,
  };
}

function addText(slide, text, x, y, w, h, opts = {}) {
  const s = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  s.text = text;
  s.text.style = {
    fontFace: "Aptos",
    fontSize: opts.size ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? "left",
  };
  return s;
}

function addBox(slide, x, y, w, h, fill = C.panel, line = C.line, radius = "rounded-lg") {
  return slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: radius,
  });
}

function chip(slide, text, x, y, w, fill = C.navy2, color = "FFFFFF") {
  addBox(slide, x, y, w, 32, fill, fill, "rounded-full");
  addText(slide, text, x + 13, y + 7, w - 26, 18, { size: 13, bold: true, color, align: "center" });
}

function title(slide, t, subtitle = "", dark = false) {
  addText(slide, t, M, 36, 900, 48, { size: 36, bold: true, color: dark ? "FFFFFF" : C.ink });
  if (subtitle) addText(slide, subtitle, M, 88, 930, 28, { size: 17, color: dark ? "B8C4D6" : C.muted });
}

function footer(slide, n) {
  addText(slide, "AI-Native Self-Healing O-RAN S-plane Digital Twin", M, 681, 620, 18, { size: 10, color: "8491A3" });
  addText(slide, String(n).padStart(2, "0"), 1178, 681, 42, 18, { size: 10, color: "8491A3", align: "right" });
}

function notes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
}

function stat(slide, value, label, x, y, w, color = C.accent) {
  addBox(slide, x, y, w, 104, "FFFFFF", "DDE5F0");
  addText(slide, value, x + 18, y + 18, w - 36, 34, { size: 30, bold: true, color });
  addText(slide, label, x + 18, y + 57, w - 36, 30, { size: 15, color: C.muted });
}

function bullets(slide, items, x, y, w, size = 18, gap = 34, color = C.ink) {
  items.forEach((item, i) => {
    slide.shapes.add({ geometry: "ellipse", position: { left: x, top: y + i * gap + 8, width: 7, height: 7 }, fill: C.accent, line: { style: "solid", fill: C.accent, width: 0 } });
    addText(slide, item, x + 20, y + i * gap, w - 20, gap, { size, color });
  });
}

function componentSlide(pres, n, cfg) {
  const slide = pres.slides.add();
  slide.background.fill = C.light;
  title(slide, cfg.title, cfg.subtitle);
  addBox(slide, 66, 150, 360, 390, "FFFFFF", "DDE5F0");
  addText(slide, cfg.num, 92, 178, 80, 58, { size: 52, bold: true, color: cfg.color });
  addText(slide, cfg.plain, 92, 252, 282, 92, { size: 24, bold: true, color: C.ink });
  addText(slide, cfg.file, 92, 365, 280, 34, { size: 15, color: C.muted });
  chip(slide, cfg.tag, 92, 432, 180, cfg.color);
  addBox(slide, 470, 150, 338, 390, "FFFFFF", "DDE5F0");
  addText(slide, "Key technical terms", 500, 180, 260, 30, { size: 22, bold: true });
  bullets(slide, cfg.terms, 502, 230, 270, 18, 43);
  addBox(slide, 850, 150, 360, 390, "FFFFFF", "DDE5F0");
  addText(slide, "What it does", 880, 180, 260, 30, { size: 22, bold: true });
  bullets(slide, cfg.does, 882, 230, 282, 17, 48, C.ink);
  footer(slide, n);
  notes(slide, cfg.notes);
}

function flow(slide, stages, active, x = 85, y = 210) {
  const width = 245;
  stages.forEach((s, i) => {
    const on = i <= active;
    addBox(slide, x + i * 285, y, width, 122, on ? s.color : "FFFFFF", on ? s.color : "DDE5F0");
    addText(slide, s.name, x + i * 285 + 22, y + 24, width - 44, 28, { size: 22, bold: true, color: on ? "FFFFFF" : C.ink, align: "center" });
    addText(slide, s.detail, x + i * 285 + 22, y + 62, width - 44, 40, { size: 14, color: on ? "EAF2FF" : C.muted, align: "center" });
    if (i < stages.length - 1) addText(slide, "→", x + i * 285 + width + 18, y + 37, 42, 42, { size: 34, bold: true, color: on ? C.accent : "BBC6D4", align: "center" });
  });
}

function tableLike(slide, rows, x, y, widths, rowH, headerFill = C.navy2) {
  rows.forEach((row, r) => {
    let cx = x;
    row.forEach((cell, c) => {
      addBox(slide, cx, y + r * rowH, widths[c], rowH, r === 0 ? headerFill : "FFFFFF", r === 0 ? headerFill : "DDE5F0", "rounded-sm");
      addText(slide, cell, cx + 10, y + r * rowH + 9, widths[c] - 20, rowH - 15, {
        size: r === 0 ? 13 : 12,
        bold: r === 0,
        color: r === 0 ? "FFFFFF" : C.ink,
      });
      cx += widths[c] + 2;
    });
  });
}

async function main() {
  const facts = await readFacts();
  await fs.mkdir(QA, { recursive: true });
  const pres = Presentation.create({ slideSize: { width: W, height: H } });

  let n = 1;
  let slide = pres.slides.add();
  slide.background.fill = C.navy;
  addText(slide, "AI-Native Self-Healing O-RAN Network", 74, 96, 860, 70, { size: 48, bold: true, color: "FFFFFF" });
  addText(slide, "Using a Digital Twin for Open-Fronthaul S-plane Recovery", 78, 180, 820, 42, { size: 25, color: "C8D6EA" });
  addText(slide, "From passive timing telemetry to governed recovery before the ~2 s failure window", 78, 252, 760, 36, { size: 19, color: "E5ECF8" });
  chip(slide, "CPU-only emulation", 78, 332, 168, C.accent);
  chip(slide, "Labelled dataset", 264, 332, 150, C.good);
  chip(slide, "Hardware-ready path", 432, 332, 180, C.amber, C.navy);
  addBox(slide, 860, 98, 305, 390, "14223B", "29415F");
  stat(slide, "100 ns", "S-plane time-error budget", 900, 132, 225, C.danger);
  stat(slide, "~2 s", "attack-to-failure window", 900, 258, 225, C.amber);
  stat(slide, "0.547 s", "measured governed-loop MTTR", 900, 384, 225, C.good);
  addText(slide, "Author: Jaswanth | Status: reproducible simulator + benchmark", 78, 610, 720, 24, { size: 15, color: "B9C7D9" });
  footer(slide, n++);
  notes(slide, "Open by framing this as the main project made concrete: O-RAN fronthaul, AI-native discrimination, self-healing response, and a digital twin that verifies candidate actions.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "The main topic becomes one governed loop", "Each word maps to a concrete software responsibility, not a slogan.");
  ["O-RAN\nOpen fronthaul\nO-DU ↔ O-RU", "AI-native\nlearned H0/H1\nclassification", "Self-healing\naction selection\nand rollback", "Digital twin\ncounterfactual\nverification"].forEach((t, i) => {
    addBox(slide, 82 + i * 290, 180, 245, 205, ["FFFFFF","FFFFFF","FFFFFF","FFFFFF"][i], "DDE5F0");
    addText(slide, t, 110 + i * 290, 222, 190, 112, { size: 23, bold: true, align: "center", color: [C.accent,C.violet,C.good,C.amber][i] });
    if (i < 3) addText(slide, "→", 338 + i * 290, 245, 48, 60, { size: 42, bold: true, color: C.muted });
  });
  addText(slide, "Concrete thesis: detect a sync anomaly, separate benign timing faults from malicious attacks, verify recovery actions in a twin, then commit the safest action before the base station fails.", 126, 456, 1030, 78, { size: 24, color: C.ink, align: "center" });
  footer(slide, n++); notes(slide, "This slide connects the broad title to the narrow research problem. Emphasize that the deck is about the S-plane timing slice of O-RAN.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "Timing is a control-plane dependency, not background plumbing", "PTP + SyncE keep the O-DU and O-RU aligned tightly enough for radio operation.");
  stat(slide, "PTP + SyncE", "Open-fronthaul synchronization stack", 80, 160, 290, C.accent);
  stat(slide, "~100 ns", "target time-error class", 400, 160, 230, C.danger);
  stat(slide, "~2 s", "reported crash window under spoofing", 660, 160, 230, C.amber);
  stat(slide, "O-DU ↔ O-RU", "timing domain, not Internet routing", 920, 160, 250, C.good);
  bullets(slide, ["PTP distributes time; SyncE helps frequency stability.", "A forged or replayed master can move the slave clock outside budget.", "Recovery must be selected before the failure window, not after outage evidence arrives."], 122, 340, 980, 22, 48);
  footer(slide, n++); notes(slide, "Use this slide to make the stakes concrete: this is fronthaul timing security, where nanosecond-scale error can become a base-station outage.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "The project sits in the fronthaul S-plane", "It is not a routing problem and it is not the radio air interface.");
  const layers = [["Application / SMO", "management and orchestration"], ["Near-RT RIC", "xApps and policy"], ["O-DU / O-RU fronthaul", "C/U/M/S planes"], ["L1/L2 timing", "PTP, SyncE, PHC, ESMC"], ["RF air interface", "UE and spectrum"]];
  layers.forEach((l, i) => {
    const y = 140 + i * 82; const active = i === 2 || i === 3;
    addBox(slide, 145, y, 960, 56, active ? (i === 3 ? C.danger : C.accent) : "FFFFFF", active ? (i === 3 ? C.danger : C.accent) : "DDE5F0");
    addText(slide, l[0], 172, y + 12, 300, 24, { size: 20, bold: true, color: active ? "FFFFFF" : C.ink });
    addText(slide, l[1], 520, y + 14, 500, 20, { size: 16, color: active ? "EEF6FF" : C.muted });
  });
  chip(slide, "Highlighted scope: Open-Fronthaul S-plane", 430, 580, 410, C.danger);
  footer(slide, n++); notes(slide, "Clarify boundaries: the monitor reads S-plane timing telemetry; later hardware still mostly means timing/networking gear, not SDRs.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "Prior work proves the threat; response is the gap", "The gap is action selection and fault-vs-attack separation.");
  tableLike(slide, [
    ["Work", "What it does", "What remains open"],
    ["TIMESAFE, ACM ToPS 2025", "Shows fronthaul timing attacks and reports a 97.5% detector", "Stops at detection; no recovery action; no H0/H1 split"],
    ["OpenTwin / DTN work", "Uses twins for network optimization and data/energy studies", "Not focused on S-plane attack recovery"],
    ["xApp conflict mitigation", "Manages conflicting RIC control actions", "Different layer; not PTP/SyncE timing"],
    ["This project", "Discriminate H0/H1, verify actions in a twin, commit before failure", "Emulated today; hardware validation is next"],
  ], 78, 150, [250, 430, 430], 74);
  footer(slide, n++); notes(slide, "State the provenance nuance: O-RAN WG11 lists PTP master-clock spoofing as a threat; the 'no comprehensive standard yet' statement comes from research literature assessment, not an official O-RAN quote.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "The formal problem is response under uncertainty", "Contribution: the missing response step plus fault/attack split and a released dataset.");
  addBox(slide, 90, 150, 500, 368, "FFFFFF", "DDE5F0");
  addText(slide, "Input", 126, 180, 130, 30, { size: 24, bold: true, color: C.accent });
  bullets(slide, ["offset, mean path delay, PDV", "PTP sequence/message regularity", "SyncE QL, GNSS and holdover flags"], 130, 235, 390, 18, 48);
  addBox(slide, 682, 150, 500, 368, "FFFFFF", "DDE5F0");
  addText(slide, "Decision", 718, 180, 150, 30, { size: 24, bold: true, color: C.good });
  bullets(slide, ["detect anomaly", "classify H0 benign fault vs H1 attack", "forecast each action in the twin", "commit only if it beats safe default"], 722, 235, 388, 18, 44);
  addText(slide, "Main-topic mapping: O-RAN = fronthaul; AI-native = learned discrimination; self-healing = autonomous action; digital twin = governed verification.", 112, 558, 1040, 28, { size: 20, bold: true, color: C.ink, align: "center" });
  addText(slide, `Honest scope: integration + experimental validation + ${facts.total.toLocaleString()}-window released dataset; not a new fundamental algorithm.`, 138, 594, 980, 28, { size: 18, bold: true, color: C.danger, align: "center" });
  footer(slide, n++); notes(slide, "Make the optimization target clear: minimize wrong-action rate and recovery time while staying inside the 100 ns budget and the two-second failure window. This also covers the contribution and honest scope.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "System architecture turns telemetry into an auditable action", "No arch.png was present, so this diagram was generated from the implemented modules.");
  const blocks = [
    ["PTP/SyncE\ntelemetry", 74, 200, C.accent], ["Injectors +\ndataset", 290, 200, C.violet], ["Feature\nwindows", 506, 200, C.amber], ["H0/H1\nclassifier", 722, 200, C.danger], ["Digital twin\nforecasts", 938, 200, C.good],
    ["Governed\nhealing loop", 398, 420, C.navy2], ["Action space\n+ audit reason", 682, 420, C.good],
  ];
  blocks.forEach((b) => { addBox(slide, b[1], b[2], 172, 100, b[3], b[3]); addText(slide, b[0], b[1]+16, b[2]+23, 140, 48, { size: 20, bold: true, color: "FFFFFF", align: "center" }); });
  [232,448,664,880].forEach((x) => addText(slide, "→", x, 225, 42, 42, { size: 30, bold: true, color: C.muted }));
  addText(slide, "↓", 783, 315, 42, 42, { size: 30, bold: true, color: C.muted });
  addText(slide, "→", 590, 445, 50, 42, { size: 30, bold: true, color: C.muted });
  footer(slide, n++); notes(slide, "Walk left to right: the simulator or future hardware feeds telemetry; windows become features; classifier and twin feed the governed action logic.");

  const comps = [
    { num: "01", title: "The simulator gives a repeatable S-plane world", subtitle: "fronthaul_sim/simulator.py", file: "fronthaul_sim/simulator.py", tag: "P1 simulator", color: C.accent, plain: "A clock-servo model produces PTP/SyncE telemetry on a laptop.", terms: ["PTP offset", "mean path delay", "PDV", "frequency error", "SyncE QL"], does: ["Disciplines a slave clock", "Supports GNSS reference and holdover", "Keeps healthy traces within budget"], notes: "Explain that this is the default realism tier: deterministic pure-Python physics, no PTP NIC required." },
    { num: "02", title: "Injectors create labelled benign faults and attacks", subtitle: "faults/injectors.py", file: "faults/injectors.py", tag: "P2 labels", color: C.violet, plain: "Scenario injectors produce timestamped H0, H1, and healthy labels.", terms: ["GNSS loss", "PDV burst", "SyncE degrade", "PTP spoof", "replay"], does: ["Covers three H0 fault modes", "Covers two H1 attack modes", "Hardening adds overlap and mimicry"], notes: "Mention realism notes: giveaway labels were removed and attack/fault magnitudes overlap." },
    { num: "03", title: "Feature extraction turns raw telemetry into 0.4 s decisions", subtitle: "telemetry/features.py", file: "telemetry/features.py", tag: "10 features", color: C.amber, plain: "Sliding windows summarize timing behavior for classification.", terms: ["0.4 s window", "0.2 s step", "offset stats", "sequence regressions", "majority label"], does: ["Builds ten model inputs", "Preserves scenario/run identity", "Outputs anomaly labels per window"], notes: "The feature slide bridges raw simulator traces and the classifier; it explains why decisions can be made inside the two-second window." },
    { num: "04", title: "The dataset builder makes the experiment reproducible", subtitle: "dataset/build.py", file: "dataset/build.py", tag: `${facts.total} windows`, color: C.good, plain: "One script assembles telemetry, labelled windows, and the datasheet.", terms: ["CSV dataset", "datasheet", "fixed seed", "label counts", "CPU-only"], does: [`${facts.counts.healthy} healthy windows`, `${facts.counts.H0} H0 benign-fault windows`, `${facts.counts.H1} H1 attack windows`], notes: "Read the exact label counts from splane_windows.csv. Emphasize dataset release value for resume and applied research positioning." },
    { num: "05", title: "The discriminator separates fault response from attack response", subtitle: "discriminator/model.py", file: "discriminator/model.py", tag: "Random Forest", color: C.danger, plain: "A stratified Random Forest classifies anomalous windows as H0 or H1.", terms: ["90 trees", "depth 6", "65/35 split", "ROC-AUC", "confusion matrix"], does: [`Accuracy ${facts.disc.accuracy}`, `ROC-AUC ${facts.disc.roc_auc_h1}`, `Baseline accuracy ${facts.baseline.accuracy}`], notes: "Do not round numbers verbally beyond what the audience can absorb, but the slide uses the measured CSV values." },
    { num: "06", title: "The twin forecasts action outcomes before touching the system", subtitle: "twin/model.py", file: "twin/model.py", tag: "P4 twin", color: C.accent, plain: "Each candidate action gets a counterfactual time-error trajectory.", terms: ["decay/floor forecast", "fidelity score", "peak error", "steady error", "discounted advice"], does: ["Ranks candidate recoveries", "Reduces trust when telemetry is messy", "Keeps safe-default as a comparator"], notes: "The twin is compact by design. It is a decision support model, not a full hardware emulator." },
    { num: "07", title: "The healing loop commits only with evidence", subtitle: "healing/loop.py", file: "healing/loop.py", tag: "P5 loop", color: C.good, plain: "Detect, classify, verify, and commit with an auditable reason.", terms: ["safe default", "action shortlist", "decision budget", "audit reason", "fallback"], does: ["Chooses different actions for H0 vs H1", "Checks twin fidelity", "Records decision time and reason"], notes: "Emphasize governance: when fidelity is low, the system falls back rather than blindly automating." },
    { num: "08", title: "The benchmark compares recovery policies, not just accuracy", subtitle: "benchmark/run.py", file: "benchmark/run.py", tag: "P6 benchmark", color: C.violet, plain: "The loop is judged against detection-only, holdover, and failover baselines.", terms: ["success rate", "wrong action", "MTTR", "peak time error", "2 s window"], does: [`Governed success ${facts.governed.recovery_success_rate}`, `Wrong-action rate ${facts.governed.wrong_action_rate}`, `Peak error ${facts.governed.peak_time_error_ns} ns`], notes: "This connects the project contribution to operational value: not detecting attacks, but recovering correctly and quickly." },
  ];
  comps.forEach((c) => componentSlide(pres, n++, c));

  const stages = [
    { name: "Detect", detail: "offset/PDV over budget", color: C.danger },
    { name: "Discriminate", detail: "H0 fault vs H1 attack", color: C.violet },
    { name: "Twin-verify", detail: "forecast action outcomes", color: C.accent },
    { name: "Commit / fallback", detail: "best action or safe default", color: C.good },
  ];
  [0, 1, 3].forEach((active, idx) => {
    slide = pres.slides.add(); slide.background.fill = idx === 0 ? C.navy : C.light;
    title(slide, idx === 0 ? "Loop walkthrough: first detect the sync anomaly" : idx === 1 ? "Loop walkthrough: then separate H0 from H1" : "Loop walkthrough: verify, commit, and audit", idx === 2 ? "The progressive reveal simulates the motion of the governed control loop." : "Each advance adds another stage of evidence.", idx === 0);
    flow(slide, stages, active);
    addBox(slide, 146, 435, 988, 94, idx === 0 ? "16233B" : "FFFFFF", idx === 0 ? "314766" : "DDE5F0");
    addText(slide, idx === 0 ? "The controller does nothing until timing telemetry crosses an anomaly threshold." : idx === 1 ? "The response path diverges: benign faults should not be treated like active attackers." : "The twin compares candidate actions against the conservative safe default; low fidelity triggers fallback.", 190, 462, 900, 34, { size: 22, bold: true, color: idx === 0 ? "FFFFFF" : C.ink, align: "center" });
    footer(slide, n++); notes(slide, "Use this as a step-through animation substitute. It is deliberately split across three slides because scripted PowerPoint animations are unreliable.");
  });

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "Discrimination is strong after realism hardening", "The classifier beats detection-only while still making real errors.");
  stat(slide, facts.disc.accuracy, "H0/H1 accuracy", 74, 150, 230, C.good);
  stat(slide, facts.disc.roc_auc_h1, "ROC-AUC for H1", 326, 150, 230, C.accent);
  stat(slide, facts.disc.f1_macro, "macro F1", 578, 150, 230, C.violet);
  stat(slide, facts.baseline.accuracy, "detection-only baseline accuracy", 830, 150, 300, C.danger);
  tableLike(slide, [["", "Pred H0", "Pred H1"], ["True H0", "186", "2"], ["True H1", "2", "123"]], 150, 335, [170, 170, 170], 58, C.navy2);
  bullets(slide, ["REALISM_NOTES.md: removed message-type giveaways.", "Attack and benign-fault magnitudes overlap.", "Evasive attacks mimic fault signatures and can occur during congestion."], 730, 340, 380, 16, 38);
  footer(slide, n++); notes(slide, "The prompt asked not to fabricate numbers. These values come directly from discriminator_metrics.csv and REALISM_NOTES.md.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "The governed loop beats simple baselines", "The measured loop stays inside the 100 ns timing budget and the 2 s failure window.");
  tableLike(slide, [
    ["Method", "Recovery", "Wrong action", "MTTR", "Peak error"],
    ...facts.bench.map((r) => [r.method.replaceAll("_", " "), r.recovery_success_rate, r.wrong_action_rate, `${r.mean_mttr_s} s`, `${Number(r.peak_time_error_ns).toFixed(3)} ns`]),
  ], 64, 145, [285, 160, 160, 150, 185], 54);
  addBox(slide, 820, 470, 360, 100, "FFFFFF", "DDE5F0");
  addText(slide, "Takeaway", 850, 492, 120, 24, { size: 22, bold: true, color: C.good });
  addText(slide, `Governed peak error is ${facts.governed.peak_time_error_ns} ns, below the 100 ns budget.`, 850, 528, 282, 30, { size: 17, color: C.ink });
  footer(slide, n++); notes(slide, "Benchmark values come from benchmark_results.csv. The governed loop is imperfect but materially better than no response and wrong-action-prone simple policies.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "Hardware next phase: timing lab first, radio later", "Indicative costs only; verify with vendors before procurement.");
  tableLike(slide, [
    ["Tier A timing lab item", "Purpose", "Indicative cost"],
    ["2-3 PCs + PTP NICs", "O-DU slave, attacker, load generator", "NIC $30-$300 each; reuse PCs"],
    ["PTP/SyncE-aware switch", "Boundary/transparent clock, G.8275.1", "$500 budget; $1.5k-$8k telecom"],
    ["PTP Grandmaster or PC GM + GPSDO", "Trusted reference clock", "$150-$400 DIY; $2k-$10k appliance"],
    ["GNSS receiver, antenna, PPS", "GNSS-loss and holdover faults", "$50-$300"],
    ["SFPs, cabling, TAP/mirror", "Passive PTP capture", "$100-$400"],
    ["Time-error tester", "ns-true validation reference", "borrow/rent; buy $5k+"],
  ], 52, 125, [330, 420, 360], 48);
  addText(slide, "Tier A total: DIY/budget ~$800-$3,000 reusing PCs; professional ~$6,000-$18,000.", 88, 602, 1060, 28, { size: 22, bold: true, color: C.ink, align: "center" });
  footer(slide, n++); notes(slide, "Key message: because this is S-plane timing, the real testbed is mostly timing Ethernet equipment. A radio is not required to validate the proposed loop.");

  slide = pres.slides.add(); slide.background.fill = C.light; title(slide, "Hardware path closes the loop", "Same software, real telemetry: linuxptp replaces the simulator input.");
  [["PTP GM\nGNSS/PPS", 80, 220, C.amber], ["Timing-aware\nswitch", 310, 220, C.accent], ["O-DU PC\nmonitor + loop", 540, 220, C.good], ["Attacker PC\nspoof/replay", 770, 220, C.danger], ["Optional O-RU\ncrash demo", 1000, 220, C.violet]].forEach((b) => { addBox(slide, b[1], b[2], 170, 104, b[3], b[3]); addText(slide, b[0], b[1]+14, b[2]+27, 142, 42, { size: 18, bold: true, color: "FFFFFF", align: "center" }); });
  [242,472,702,932].forEach((x) => addText(slide, "↔", x, 246, 46, 42, { size: 30, bold: true, color: C.muted }));
  addBox(slide, 70, 382, 350, 160, "FFFFFF", "DDE5F0"); addText(slide, "Done now", 96, 408, 150, 24, { size: 22, bold: true, color: C.good }); bullets(slide, ["run_all.py reproduction", "dataset + benchmark", "tests pass 3/3"], 100, 452, 270, 14, 28);
  addBox(slide, 460, 382, 350, 160, "FFFFFF", "DDE5F0"); addText(slide, "Next commands", 486, 408, 190, 24, { size: 22, bold: true, color: C.amber }); bullets(slide, ["ptp4l / phc2sys / ts2phc", "tc netem and packet capture", "BMCA allow-list actions"], 490, 452, 270, 14, 28);
  addBox(slide, 850, 382, 360, 160, "FFFFFF", "DDE5F0"); addText(slide, "Do not miss", 876, 408, 160, 24, { size: 22, bold: true, color: C.danger }); bullets(slide, ["G.8275.1 profile", "OCXO vs TCXO holdover", "GNSS sky view, PPS skew, UPS", "Tier A needs no radio licence"], 880, 448, 290, 13, 25);
  addText(slide, "Close: the project is a reproducible response loop today; hardware timestamping is the next validation step.", 142, 596, 980, 26, { size: 20, bold: true, color: C.ink, align: "center" });
  footer(slide, n++); notes(slide, "This final slide combines the connection diagram, practical considerations, done-vs-next status, and closing limitation.");

  for (const [i, s] of pres.slides.items.entries()) {
    const png = await pres.export({ slide: s, format: "png", scale: 1 });
    await fs.writeFile(path.join(QA, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await s.export({ format: "layout" });
    await fs.writeFile(path.join(QA, `slide-${String(i + 1).padStart(2, "0")}.layout.json`), await layout.text());
  }
  const montage = await pres.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(QA, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const pptx = await PresentationFile.exportPptx(pres);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
