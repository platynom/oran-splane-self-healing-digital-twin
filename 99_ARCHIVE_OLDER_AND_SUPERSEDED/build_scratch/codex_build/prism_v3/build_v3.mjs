import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin";
const sourcePath = path.join(workspaceDir, "ORAN_SPlane_PRISM_Review_1.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v3.pptx");
const skillDir = "C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.923.10815/skills/presentations";
const runtimePython = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
process.env.RUNTIME_NODE_MODULES = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({
  kind: "textbox,notes",
  include: "id,slide,bbox,text",
  maxChars: 400000,
});
const records = snapshot.ndjson.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));

function recordFor(slideIndex, needle, kind = "textbox") {
  const hits = records.filter((r) => r.kind === kind && r.slideIndex === slideIndex && (r.text ?? "").includes(needle));
  if (hits.length !== 1) throw new Error(`Expected one ${kind} on slide ${slideIndex + 1} containing ${JSON.stringify(needle)}, found ${hits.length}`);
  return hits[0];
}

function edit(slideIndex, needle, replacement, style = {}) {
  const r = recordFor(slideIndex, needle);
  const target = presentation.resolve(r.id);
  target.text.replace(r.text, replacement);
  if (style.fontSize !== undefined) target.text.fontSize = style.fontSize;
  if (style.color !== undefined) target.text.color = style.color;
  if (style.bold !== undefined) target.text.bold = style.bold;
  if (style.typeface !== undefined) target.text.typeface = style.typeface;
  if (style.autoFit !== undefined) target.text.autoFit = style.autoFit;
  return target;
}

function editById(id, replacement, style = {}) {
  const r = records.find((x) => x.id === id);
  if (!r) throw new Error(`Missing record ${id}`);
  const target = presentation.resolve(id);
  target.text.replace(r.text, replacement);
  if (style.fontSize !== undefined) target.text.fontSize = style.fontSize;
  if (style.color !== undefined) target.text.color = style.color;
  if (style.bold !== undefined) target.text.bold = style.bold;
  if (style.autoFit !== undefined) target.text.autoFit = style.autoFit;
  return target;
}

function setNotes(slideIndex, text) {
  presentation.slides.getItem(slideIndex).speakerNotes.textFrame.setText(text);
}

function setShapeFill(id, fill, lineFill = fill) {
  const shape = presentation.resolve(id);
  shape.fill = fill;
  shape.line = { fill: lineFill, width: 1 };
}

function addText(slide, text, position, style) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = { autoFit: "shrinkText", wrap: "square", ...style };
  return box;
}

function setKicker(slideIndex, text) {
  const hits = records.filter((r) => r.kind === "textbox" && r.slideIndex === slideIndex && r.position?.top <= 26 && r.position?.width >= 700);
  if (hits.length !== 1) throw new Error(`Expected one kicker on slide ${slideIndex + 1}, found ${hits.length}`);
  const target = presentation.resolve(hits[0].id);
  target.text = text;
  target.text.style = { typeface: "Calibri", fontSize: 13.33, bold: true, color: "#1C7293", alignment: "left", autoFit: "shrinkText", wrap: "square" };
}

function addNode(slide, title, detail, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    position,
    fill: options.fill ?? "#FFFFFF",
    line: { fill: options.line ?? "#9FB3C8", width: options.lineWidth ?? 1.4 },
  });
  shape.text = detail ? `${title}\n${detail}` : title;
  shape.text.style = {
    typeface: "Calibri",
    fontSize: options.fontSize ?? 16,
    bold: options.bold ?? true,
    color: options.color ?? "#12263A",
    alignment: "center",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    wrap: "square",
  };
  return shape;
}

function addArrow(slide, position, options = {}) {
  return slide.shapes.add({
    geometry: "line",
    position,
    line: { style: options.style ?? "solid", fill: options.color ?? "#5B6B7C", width: options.width ?? 2 },
    head: options.head === false ? { type: "none" } : { type: "arrow", width: "sm", length: "sm" },
    tail: options.tail ? { type: options.tail, width: "sm", length: "sm" } : { type: "none" },
  });
}

// Slides 3-4: larger, professional problem framing and evidence-accurate wording.
edit(2, "THE PROBLEM", "PROBLEM STATEMENT", { fontSize: 20 });
const problemTitle = edit(2, "Radios must agree", "Tightly bounded time alignment underpins Open Fronthaul", { fontSize: 46.67, autoFit: "shrinkText" });
problemTitle.position = { ...problemTitle.position, top: 55, height: 96 };
edit(2, "Relative time alignment", "Category-A relative alignment target between radio units\nO-RAN Open Fronthaul CUS-plane specification", { fontSize: 14.67 });
edit(2, "End-to-end network", "Application-level time-error limit from O-RU to PRTC\nITU-T G.8271.1", { fontSize: 14.67 });
edit(2, "Fastest publicly", "Observed service failure after a timing attack in one study\nTIMESAFE", { fontSize: 14.67 });
edit(2, "That is what makes", "Because timing is distributed as network traffic, it is attackable. Loss of a shared time reference can degrade radio coordination, making the S-plane a security surface as well as an engineering constraint.", { fontSize: 16.67 });
setNotes(2, "The 130 ns value is category-specific, the ±1.5 µs value is an application-level O-RU-to-PRTC limit, and the roughly 2 s result is an observation from TIMESAFE, not a standardised bound or a fastest-known claim.");

edit(3, "THE CORE QUESTION", "RESEARCH QUESTION", { fontSize: 20 });
edit(3, "Same symptom", "Can timing attacks be distinguished from benign faults?", { fontSize: 50.67, autoFit: "shrinkText" });
edit(3, "From the packets alone", "Where ambiguity appears: a planned grandmaster or boundary-clock change can resemble a rogue clock, while link loss or congestion can resemble packet removal or delay manipulation.\nDecision parameters: allow-listed clock identity, maintenance window, clockClass, priority, stepsRemoved, sequence continuity, observed packet rate, offset, path delay and packet-delay variation.", { fontSize: 14.67, autoFit: "shrinkText" });
setNotes(3, "The overlap is scenario-specific. Decisions use operator allow-lists and maintenance context together with protocol fields, packet-rate evidence and servo telemetry.");

// Slide 5: scope language.
edit(4, "A timing failure becomes", "Published attacks show that a timing failure can become a service failure in seconds, leaving little time for a safe decision.");
edit(4, "Benign faults and attacks", "Selected benign faults and attacks can produce overlapping symptoms. The decision combines protocol evidence with provisioned context.");
edit(4, "Fully specified by standards", "Constrained by standards");
edit(4, "IEEE 1588-2019", "IEEE 1588-2019 and ITU-T G.8275.1 constrain wire-level legality. Operator intent still requires provisioned context, and some thresholds are measured.");

// Slide 6: milestone status and parameter count.
editById("sh/zep4byhs", "A1-A8 / B1-B8 catalogue; 144-parameter × 16-fault matrix", { fontSize: 14.67 });
editById("sh/4f2pgr2h", "Six-node testbed and injection validated; digital twin not in this campaign", { fontSize: 14.67 });
editById("sh/u907axkf", "PARTIAL", { fontSize: 11.33 });
setShapeFill("sh/va98j210", "#C08401");
editById("sh/fq9cfqxc", "Decision engine evaluated; closed-loop healing not validated", { fontSize: 14.67 });
editById("sh/1sbuh0fi", "PARTIAL", { fontSize: 11.33 });
setShapeFill("sh/0r2t8vyx", "#C08401");

// Slide 7: accurate rule-arm provenance.
edit(6, "Decides from standards", "Combines standards legality with provisioned operator context\nNo model training; a small number of measured thresholds remain\nBase rule was SHA-256 frozen before the campaign\nv3 is a disclosed post-campaign defect-fix revision", { fontSize: 16 });
setNotes(6, "The comparison is required by worklet objective 5. Distinguish the pre-frozen base rule from v3, which was written after v2 false positives were observed and then re-frozen before V4 scoring.");

// Slide 8: real protocol execution, without claiming independent clock-error measurement.
edit(7, "The clocks genuinely", "Real linuxptp daemons execute BMCA and servo logic on isolated network namespaces\nFaults use live packet-path mechanisms, not synthetic packet rows\nNo independent clock-error instrument was used; synchronisation impact is inferred from protocol and servo telemetry\nITU-T G.8275.1 profile settings: domain 24, priority1 128, Sync 16/s, Announce 8/s", { fontSize: 15.33 });
setNotes(7, "Emphasise that protocol execution is real. Do not claim independently measured loss of synchronisation: the campaign uses packet captures and daemon telemetry, not an external timing instrument.");

// Slide 12: multiple grandmasters are not inherently illegal.
edit(11, "Produce protocol-inconsistent", "Produce illegal or unauthorised evidence, such as forged Announce fields, non-monotonic sequence IDs, or a superior grandmaster that is outside the provisioned allow-list.");

// Slide 14: three-way software / detection-only / hardware taxonomy.
edit(13, "SOFTWARE — produced", "SW FULL · SW* DETECTION");
edit(13, "HARDWARE REQUIRED", "HW PHYSICAL");
for (const id of ["sh/fqdg3q98", "sh/pwvy90rq", "sh/5o32d8r2", "sh/s3q1oj2l"]) editById(id, records.find((r) => r.id === id).text === "HW" ? "SW*" : records.find((r) => r.id === id).text, { color: "#C58B18", bold: true });
for (const id of ["sh/n6to3qdk", "sh/98b65gvq"]) editById(id, records.find((r) => r.id === id).text === "HW" ? "SW" : records.find((r) => r.id === id).text, { color: "#1E8E5A", bold: true });
editById("sh/fi5432t4", "SW*", { color: "#C58B18", bold: true });
for (const id of ["sh/grmxwvqt", "sh/lkrmhsju", "sh/knu1k3ah"]) setShapeFill(id, "#FFF6DD", "#E9C46A");
setShapeFill("sh/m507alwz", "#EAF5EF", "#CBE6D8");
edit(13, "Mapped to O-RAN", "Attack classes align where applicable with ETSI TR 104 106. Benign classes are test conditions, not threat identifiers. SW* means software detection logic only; physical impact needs hardware.", { fontSize: 11.33 });
setNotes(13, "Taxonomy from the latest parameter matrix: 8 fully software classes, 3 software detection-only classes (A4, A8, B5), and 5 hardware-required classes (A6, A7, B1, B4, B6).");

// Slide 16: campaign provenance and randomisation caveat.
edit(15, "Designed so", "The base rule was pre-frozen; v3 is a disclosed post-campaign defect-fix revision.", { fontSize: 17.33 });
edit(15, "Hash-freeze before running", "Freeze history disclosed");
edit(15, "The decision rule is", "The base rule was hashed before the campaign. v3 was created after v2 false positives were observed, then re-frozen before V4 scoring on the same captures.", { fontSize: 14.67 });
edit(15, "Attacker identity", "Parameters are reproducible from random.Random(rep). The C-series designs contain only 4-5 distinct parameter values, so the randomised space remains narrow.", { fontSize: 14.67 });
setNotes(15, "Do not describe v3 as independent pre-registered validation. The base rule was pre-frozen; v3 is a transparent post-observation defect fix evaluated on the same campaign captures.");

// Slide 17: label the base-vs-revision comparison accurately.
edit(16, "Per-scenario detection", "Per-scenario detection: frozen base vs v3 defect-fix", { fontSize: 42.67 });
edit(16, "Frozen rule", "Frozen base");
edit(16, "With v3 detectors", "v3 defect-fix");

// Slide 19: measured interpolation boundary.
edit(18, "Detects sustained interception", "Observed: 65% blackhole was caught and 60% was missed. The ~62% evasion boundary is an interpolation, not a directly tested point. Short or bursty interception may average out.", { fontSize: 16 });

// Slide 20: direct trivial-baseline control and the requested B_bc_replacement conclusion.
edit(19, "The ML arm is not distinguishable", "ARM B is not distinguishable from always-BENIGN", { fontSize: 18.67 });
edit(19, "It outputs BENIGN", "ARM B outputs BENIGN on 47/56 and has ROC-AUC 0.604. It scores 24/56 versus 20/56 for always-BENIGN (paired exact McNemar p = 0.219). Both score 4/4 on B_bc_replacement, so that result is not unique.", { fontSize: 14.67 });
setNotes(19, "The always-BENIGN control scores attack 0/32, benign 20/20, abstention 0/4, and exact accuracy 20/56. ARM B improves by only four runs and is not statistically distinguishable at this sample size (paired exact McNemar p = 0.21875). Its B_bc_replacement result is shared by the constant predictor and is not a unique learned capability.");

// Slide 21: interpretation constrained to this telemetry and testbed.
edit(20, "C1 blackholes", "C1 blackholes the timing path and C3 disrupts BMCA. Servo samples fall from 88 per baseline run to 44 and 28. The ML arm loses evidence; the rule arm can still use packet-rate deficit plus legality and context evidence.", { fontSize: 14.67 });
edit(20, "It learned testbed", "Feature importances indicate testbed-servo artefact risk", { fontSize: 19.33 });
edit(20, "Top importances", "Top importances are offset_abs_max 0.268, path_delay_mean 0.262, and offset_std 0.208. With one testbed, domain shift cannot be separated from intrinsic class overlap.", { fontSize: 14.67 });

// Slide 22: surface the held-out sample and metadata constraints.
edit(21, "Standards values partly", "Held-out evidence is small and partially missing");
editById("sh/udonux8v", "4/scenario", { fontSize: 11.33 });
edit(21, "ITU-T G.827x", "Only four held-out replicates exist per scenario, and 48/168 runs lack pmc.jsonl. Intervals are wide and ARM B sees only 6 of 28 designed features.", { fontSize: 14.67 });
edit(21, "Software timestamping", "Replicate metadata is inconsistent");
editById("sh/yp0zipk7", "36 C runs", { fontSize: 11.33 });
edit(21, "The platform resolves", "Thirty-six C-series contexts record rep=901; the split uses the replicate encoded in the directory name. Correct this before any fresh validation claim.", { fontSize: 14.67 });

// Slide 23: disclosure of the rerun and post-observation revision.
edit(22, "All four fixed", "All fabricated-data runs were re-executed. Evaluator defects were corrected, and the post-observation v3 decision revision is explicitly disclosed.", { fontSize: 15.33 });

// Slide 24: corrected action plan and hardware boundary.
edit(23, "Widen the interception", "Boundary-clock allow-list to close the B_bc_replacement false positive, then re-freeze and re-run\nTest additional interception levels around the interpolated ~62% boundary\nExtend the randomised design space for the three new scenarios\nRe-run ARM B with richer management-plane telemetry for a fairer comparison\nM6 deliverable: paper and IP disclosure draft");
edit(23, "unlocks A4 delay", "improves A4/B5 physical-impact credibility and timestamp precision");
edit(23, "7 of 16 fault classes", "5 of 16 classes require hardware. Three more support software detection logic but need hardware for credible physical-impact measurement.", { fontSize: 16 });
setNotes(23, "Hardware priorities: GNSS receiver for A6/A7/B1, a second oscillator for B6, SyncE hardware for B4, and a hardware-timestamping NIC to improve A4/B5 physical-impact measurement.");

// Slide 25: conclusion constrained to the evidence.
edit(24, "A real testbed", "Real protocol execution, scoped evidence");
edit(24, "Six genuine PTP", "Six linuxptp daemons and live packet-path injection; no independent clock-error instrument");
edit(24, "168 live runs", "168 live runs; base rule pre-frozen");
edit(24, "The rule could not", "v3 was created after v2 false positives and its revision history is disclosed");
edit(24, "Three coverage gaps", "Three coverage gaps closed; benign specificity remains 0.783");
edit(24, "Rule-based decisively", "On this fixed split, ARM A beats ARM B; ARM B is not distinguishable from always-BENIGN", { fontSize: 14.67 });
edit(24, "The 62 % evasion", "~62% is interpolated; BC replacement remains open; 5 HW plus 3 detection-only classes", { fontSize: 14.67 });
setNotes(24, "Close on the evidence boundary. ARM B is not statistically distinguishable from always-BENIGN at n=56, and its B_bc_replacement performance is not a unique capability.");

// Link every analytical slide to the corresponding worklet objective or milestone.
const kickers = new Map([
  [2, "WORKLET M1: PROBLEM STUDY (COMPLETED)"],
  [3, "WORKLET M1: DECISION REQUIREMENTS (COMPLETED)"],
  [4, "WORKLET M1: S-PLANE SUB-SCOPE (COMPLETED)"],
  [5, "WORKLET DELIVERY MAP: CURRENT STATUS"],
  [6, "OBJECTIVE 5: AI VS RULE COMPARISON (COMPLETED)"],
  [7, "WORKLET M3: FAULT-INJECTION TESTBED (PARTIAL)"],
  [8, "WORKLET M2: KPI CONFIGURATION (COMPLETED)"],
  [9, "WORKLET M2: PLATFORM CONSTRAINTS (COMPLETED)"],
  [10, "WORKLET M1: SYSTEM DATA FLOW (COMPLETED)"],
  [11, "WORKLET M5: DECISION ENGINE (COMPLETED)"],
  [12, "WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)"],
  [13, "WORKLET M2: FAULT TAXONOMY (COMPLETED)"],
  [14, "WORKLET M3: FAULT INJECTION (COMPLETED)"],
  [15, "WORKLET M6: CAMPAIGN DESIGN (COMPLETED)"],
  [16, "WORKLET M6: PER-SCENARIO EVALUATION (COMPLETED)"],
  [17, "WORKLET M6: PRIMARY RESULTS (COMPLETED)"],
  [18, "WORKLET M6: DETECTION BOUNDARY (COMPLETED)"],
  [19, "OBJECTIVE 5: AI VS RULE COMPARISON (COMPLETED)"],
  [20, "OBJECTIVE 5: RESULT INTERPRETATION (COMPLETED)"],
  [21, "WORKLET M6: LIMITATIONS DOCUMENTED (COMPLETED)"],
  [22, "WORKLET M6: PIPELINE AUDIT (COMPLETED)"],
  [23, "WORKLET M3, M5 AND M6: REMAINING WORK"],
]);
for (const [slideIndex, text] of kickers) setKicker(slideIndex, text);

// The original worklet/booklet remains unchanged as slide 1. Add scope labels only to slides without kickers.
addText(presentation.slides.getItem(1), "WORKLET SUB-SCOPE: OPEN FRONTHAUL S-PLANE TIMING SECURITY", { left: 59.52, top: 39, width: 900, height: 26 }, { typeface: "Calibri", fontSize: 13.33, bold: true, color: "#18B89A" });
addText(presentation.slides.getItem(24), "WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE", { left: 59.52, top: 19.2, width: 780, height: 24.96 }, { typeface: "Calibri", fontSize: 13.33, bold: true, color: "#1C7293" });

// Insert an editable, evidence-grounded architecture map after the sub-scope title slide.
{
  const slide = presentation.slides.insert({ after: presentation.slides.getItem(1) }).slide;
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 1280, height: 720 }, fill: "#F8FAFC", line: { fill: "none", width: 0 } });
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 1280, height: 12 }, fill: "#18B89A", line: { fill: "none", width: 0 } });
  addText(slide, "WORKLET M1: SYSTEM ARCHITECTURE DESIGN (COMPLETED)", { left: 59.52, top: 19.2, width: 900, height: 24.96 }, { typeface: "Calibri", fontSize: 13.33, bold: true, color: "#1C7293" });
  addText(slide, "Where the project acts in the 5G O-RAN stack", { left: 59.52, top: 43, width: 1155, height: 58 }, { typeface: "Cambria", fontSize: 38, bold: true, color: "#12263A" });
  addText(slide, "Completed: mapped the service path and isolated the Open Fronthaul S-plane timing boundary.", { left: 59.52, top: 105, width: 1155, height: 30 }, { typeface: "Calibri", fontSize: 17.33, color: "#5B6B7C" });

  const smo = addNode(slide, "SMO / Non-RT RIC", "policy and lifecycle", { left: 520, top: 153, width: 190, height: 60 }, { fill: "#EAF2F8", line: "#1C7293", fontSize: 15 });
  const nearRic = addNode(slide, "Near-RT RIC", "xApps and E2 control", { left: 760, top: 153, width: 180, height: 60 }, { fill: "#EAF2F8", line: "#1C7293", fontSize: 15 });
  const cloud = addNode(slide, "O-Cloud", "hosts RIC, CU and DU functions", { left: 990, top: 153, width: 220, height: 60 }, { fill: "#EEF1F5", line: "#8796A5", fontSize: 14.67 });

  const ue = addNode(slide, "User equipment", "UE", { left: 40, top: 262, width: 120, height: 66 }, { fill: "#FFFFFF" });
  const oru = addNode(slide, "O-RU", "radio unit", { left: 205, top: 262, width: 130, height: 66 }, { fill: "#FFFFFF" });
  const odu = addNode(slide, "O-DU", "distributed unit", { left: 395, top: 262, width: 140, height: 66 }, { fill: "#FFFFFF" });
  const ocu = addNode(slide, "O-CU-CP / O-CU-UP", "central unit", { left: 595, top: 262, width: 165, height: 66 }, { fill: "#FFFFFF", fontSize: 14.67 });
  const core = addNode(slide, "5G Core", "control and user plane", { left: 820, top: 262, width: 145, height: 66 }, { fill: "#FFFFFF", fontSize: 14.67 });
  const dataNetwork = addNode(slide, "Data network", "applications and services", { left: 1025, top: 262, width: 185, height: 66 }, { fill: "#FFFFFF", fontSize: 14.67 });

  const mainNodes = [ue, oru, odu, ocu, core, dataNetwork];
  for (let i = 0; i < mainNodes.length - 1; i++) {
    slide.shapes.connect(mainNodes[i], mainNodes[i + 1], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#5B6B7C", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });
  }
  addText(slide, "Open Fronthaul C/U/S/M planes", { left: 292, top: 232, width: 250, height: 24 }, { typeface: "Calibri", fontSize: 12.67, bold: true, color: "#B3402F", alignment: "center" });
  slide.shapes.connect(smo, nearRic, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "dashed", fill: "#1C7293", width: 1.5 }, head: { type: "arrow", width: "sm", length: "sm" } });
  addText(slide, "A1", { left: 722, top: 168, width: 30, height: 20 }, { typeface: "Calibri", fontSize: 12, bold: true, color: "#1C7293", alignment: "center" });
  slide.shapes.connect(nearRic, odu, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "dashed", fill: "#1C7293", width: 1.5 }, head: { type: "arrow", width: "sm", length: "sm" } });
  slide.shapes.connect(nearRic, ocu, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "dashed", fill: "#1C7293", width: 1.5 }, head: { type: "arrow", width: "sm", length: "sm" } });
  addText(slide, "E2", { left: 745, top: 222, width: 32, height: 20 }, { typeface: "Calibri", fontSize: 12, bold: true, color: "#1C7293", alignment: "center" });
  slide.shapes.connect(cloud, nearRic, { kind: "straight", fromSide: "left", toSide: "right", line: { style: "dotted", fill: "#8796A5", width: 1.2 } });

  const prtc = addNode(slide, "PRTC / grandmaster", "reference time", { left: 40, top: 405, width: 155, height: 66 }, { fill: "#FFF8E8", line: "#C58B18", fontSize: 14.67 });
  const boundary = addNode(slide, "Boundary clock", "timing relay", { left: 230, top: 405, width: 145, height: 66 }, { fill: "#FFF8E8", line: "#C58B18", fontSize: 14.67 });
  const hit = addNode(slide, "PROJECT HIT: OPEN FRONTHAUL S-PLANE", "PTP / SyncE timing evidence captured on brUP and brDN", { left: 410, top: 390, width: 365, height: 92 }, { fill: "#DDF5EF", line: "#18B89A", lineWidth: 2.5, color: "#0B5547", fontSize: 16 });
  slide.shapes.connect(prtc, boundary, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#C58B18", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });
  slide.shapes.connect(boundary, hit, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#C58B18", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });
  slide.shapes.connect(hit, oru, { kind: "elbow", fromSide: "top", toSide: "bottom", line: { style: "dashed", fill: "#18B89A", width: 2 } });
  slide.shapes.connect(hit, odu, { kind: "elbow", fromSide: "top", toSide: "bottom", line: { style: "dashed", fill: "#18B89A", width: 2 } });

  const features = addNode(slide, "Feature extraction", "packet plus daemon telemetry", { left: 410, top: 530, width: 215, height: 72 }, { fill: "#FFFFFF", line: "#18B89A", fontSize: 14.67 });
  const compare = addNode(slide, "Rule and ML comparison", "ARM A versus ARM B", { left: 690, top: 530, width: 215, height: 72 }, { fill: "#FFFFFF", line: "#18B89A", fontSize: 14.67 });
  const response = addNode(slide, "Safe response decision", "isolate, holdover or escalate", { left: 970, top: 530, width: 240, height: 72 }, { fill: "#FFFFFF", line: "#18B89A", fontSize: 14.67 });
  slide.shapes.connect(hit, features, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: "#18B89A", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });
  slide.shapes.connect(features, compare, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#18B89A", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });
  slide.shapes.connect(compare, response, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: "#18B89A", width: 2 }, head: { type: "arrow", width: "sm", length: "sm" } });

  // Explicit line arrows keep the data-flow legible in portable renderers.
  for (const [left, width] of [[165, 35], [340, 50], [540, 50], [765, 50], [970, 50]]) addArrow(slide, { left, top: 295, width, height: 0 });
  addArrow(slide, { left: 200, top: 438, width: 25, height: 0 }, { color: "#C58B18" });
  addArrow(slide, { left: 380, top: 438, width: 25, height: 0 }, { color: "#C58B18" });
  addArrow(slide, { left: 518, top: 484, width: 0, height: 42 }, { color: "#18B89A" });
  addArrow(slide, { left: 630, top: 566, width: 55, height: 0 }, { color: "#18B89A" });
  addArrow(slide, { left: 910, top: 566, width: 55, height: 0 }, { color: "#18B89A" });
  addArrow(slide, { left: 714, top: 183, width: 41, height: 0 }, { color: "#1C7293", style: "dashed" });
  addArrow(slide, { left: 942, top: 183, width: 43, height: 0 }, { color: "#8796A5", style: "dotted", head: false });
  addArrow(slide, { left: 465, top: 213, width: 385, height: 49 }, { color: "#1C7293", style: "dashed", head: false });
  addArrow(slide, { left: 677, top: 213, width: 173, height: 49 }, { color: "#1C7293", style: "dashed", head: false });
  addArrow(slide, { left: 278, top: 329, width: 0, height: 58 }, { color: "#18B89A", style: "dashed", head: false });
  addArrow(slide, { left: 465, top: 329, width: 0, height: 58 }, { color: "#18B89A", style: "dashed", head: false });

  slide.shapes.add({ geometry: "line", position: { left: 59.52, top: 638, width: 1155, height: 0 }, line: { fill: "#D7E1EA", width: 1 } });
  addText(slide, "Validated here: packet capture, feature extraction and classification. Remaining scope: digital-twin orchestration and automated recovery.", { left: 59.52, top: 650, width: 1155, height: 34 }, { typeface: "Calibri", fontSize: 14, color: "#5B6B7C", alignment: "center" });
  slide.speakerNotes.textFrame.setText("Architecture context follows the O-RAN reference architecture: SMO with Non-RT RIC, Near-RT RIC, O-CU-CP/O-CU-UP, O-DU, O-RU and O-Cloud. Open Fronthaul between O-DU and O-RU carries C/U/S/M planes. Official sources: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf ; https://mediastorage.o-ran.org/ecosystem-resources/O-RAN-2025.04.02.WP.O-RAN_NTN_Deployments-v08.4.pdf ; https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3219 . The highlighted project boundary is based on this repository's six-daemon S-plane testbed.");
}

const requirements = {
  explicitTotalSlideCount: 26,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  sourceTemplatePath: sourcePath,
};
const fontPolicy = {
  basis: "reference",
  families: ["Cambria", "Calibri", "Courier New"],
  referencePath: sourcePath,
  referenceSha256: "54a5f8006e4eeff2ee65326ab220a20ca5840327104d58a8674f59411a7e246e",
};

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const candidatePath = path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v3_candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"],
  requiredNativeTableOwnerSlides: [],
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v3.validation.json"),
});
process.stdout.write(JSON.stringify({ finalPath, result }, null, 2));
