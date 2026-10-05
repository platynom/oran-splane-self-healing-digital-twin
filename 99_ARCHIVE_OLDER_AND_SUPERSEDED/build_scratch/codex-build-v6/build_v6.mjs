import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const sourcePath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v5.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v6.pptx");
const skillDir = "C:\\Users\\Admin\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.927.11222\\skills\\presentations";
const pythonExecutable = "C:\\Users\\Admin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
const buildDir = path.join(workspaceDir, ".codex-build-v6");
const stagingDir = path.join(workspaceDir, ".codex-finalizer-v6");
await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));

const C = {
  bg: "#F8FAFC", navy: "#12263A", blue: "#1C7293", teal: "#18B89A",
  gray: "#5B6B7C", pale: "#EAF2F8", rule: "#D7E1EA", dark: "#0E2440",
  green: "#1E8E5A", red: "#B3402F", amber: "#C58B18", white: "#FFFFFF",
};

function rect(slide, x, y, w, h, fill, line = "none", radius = false) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { fill: line, width: line === "none" ? 0 : 1 },
  });
}

function textBox(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: opts.font ?? "Calibri",
    fontSize: opts.size ?? 16,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    color: opts.color ?? C.navy,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: "shrinkText",
  };
  return shape;
}

function baseSlide(slide, kicker, title, citations) {
  rect(slide, 0, 0, 1280, 720, C.bg);
  rect(slide, 0, 0, 1280, 12, C.teal);
  textBox(slide, kicker, 60, 22, 1160, 24, { size: 12.8, color: C.blue, bold: true });
  textBox(slide, title, 60, 49, 1160, 53, { size: 35, color: C.navy, bold: true, font: "Cambria" });
  rect(slide, 60, 111, 1160, 46, C.pale, C.rule, true);
  textBox(slide, citations, 76, 120, 1128, 30, { size: 11.2, color: C.gray });
}

function rowRule(slide, y) {
  rect(slide, 60, y, 1160, 1.2, C.rule);
}

let insertionIndex = 5;
function insertNextSlide() {
  const slide = presentation.slides.add();
  slide.moveTo(insertionIndex);
  insertionIndex += 1;
  return slide;
}

// Slide 6: literature foundation
{
  const slide = insertNextSlide();
  baseSlide(
    slide,
    "WORKLET M1: LITERATURE REVIEW (COMPLETED)",
    "Research Foundation for S-Plane Timing Assurance",
    "Groen et al., TIMESAFE, ACM ToPS 28(5), 2025, doi:10.1145/3775060  |  Bonati et al., Colosseum, IEEE OJ-COMS, 2024, doi:10.1109/OJCOMS.2024.3447472\nDigital Twin for O-RAN, IEEE Communications Magazine, 2024, doi:10.1109/MCOM.003.2400016  |  OpenRAN Gym, Computer Networks, 2023  |  TSN Digital Twin, EURASIP JIS, 2025"
  );
  textBox(slide, "SOURCE", 70, 173, 300, 24, { size: 12, color: C.blue, bold: true });
  textBox(slide, "WHAT THE LITERATURE ESTABLISHES", 390, 173, 400, 24, { size: 12, color: C.blue, bold: true });
  textBox(slide, "BOUNDARY LEFT OPEN", 820, 173, 370, 24, { size: 12, color: C.blue, bold: true });
  rowRule(slide, 201);
  const rows = [
    ["TIMESAFE · ACM 2025", "PTP attacks can disrupt O-RAN fronthaul and can be detected from packet evidence.", "Attack detection was not tested against a matched set of benign timing faults."],
    ["Digital Twin for O-RAN · IEEE 2024", "A RAN twin can support testing, optimization and safer control decisions.", "The architecture does not validate S-plane attack-versus-fault discrimination."],
    ["Colosseum · IEEE 2024", "Repeatable Open RAN twins can reproduce realistic experimental conditions.", "The platform does not focus on telecom PTP legality or recovery choice."],
    ["OpenRAN Gym · Elsevier 2023", "O-RAN AI/ML requires controlled data collection and reproducible evaluation.", "It does not ask whether an S-plane model beats rules or a constant predictor."],
    ["TSN Digital Twin · Springer 2025", "A timing-aware twin can support structured security testing.", "The study does not combine O-RAN PTP, benign lookalikes and held-out controls."],
  ];
  let y = 214;
  for (const [source, established, gap] of rows) {
    textBox(slide, source, 70, y + 8, 295, 56, { size: 15.5, color: C.navy, bold: true, font: "Cambria" });
    textBox(slide, established, 390, y + 7, 395, 60, { size: 14.3, color: C.gray });
    textBox(slide, gap, 820, y + 7, 370, 60, { size: 14.3, color: C.navy });
    rowRule(slide, y + 72);
    y += 79;
  }
  rect(slide, 60, 620, 1160, 54, C.dark, C.dark, true);
  textBox(slide, "Literature conclusion: prior work validates the threat, AI testbeds and digital-twin direction. It does not resolve the operational decision between malicious timing and a similar benign fault.", 82, 634, 1116, 30, { size: 14.5, color: C.white, bold: true, font: "Cambria" });
  slide.speakerNotes.textFrame.setText([
    "Sources:",
    "J. Groen et al., TIMESAFE: Timing Interruption Monitoring and Security Assessment for Fronthaul Environments, ACM Transactions on Privacy and Security, 28(5), 2025. DOI 10.1145/3775060.",
    "L. Bonati et al., Colosseum: The Open RAN Digital Twin, IEEE Open Journal of the Communications Society, 2024. DOI 10.1109/OJCOMS.2024.3447472.",
    "Digital Twin for O-RAN Towards 6G, IEEE Communications Magazine, 2024. DOI 10.1109/MCOM.003.2400016.",
    "L. Bonati et al., OpenRAN Gym: AI/ML Development, Data Collection, and Testing for O-RAN on PAWR Platforms, Computer Networks, 2023.",
    "Time-Sensitive Networking Digital Twin for STRIDE-Based Security Testing, EURASIP Journal on Information Security, 2025. DOI 10.1186/s13635-025-00213-7.",
    "The gap statement applies to the locally reviewed source set. It is not a claim that no other publication worldwide addresses any part of the problem.",
  ].join("\n"));
}

// Slide 7: consolidated gaps
{
  const slide = insertNextSlide();
  baseSlide(
    slide,
    "WORKLET M1: RESEARCH GAP ANALYSIS (COMPLETED)",
    "Research Gaps Behind the Experimental Design",
    "Federated Continual Learning for O-RAN Anomaly Detection, IEEE WCNC 2024  |  Adversarial ML Threat Analysis in O-RAN, JNCA 2024, doi:10.1016/j.jnca.2024.104090\nO-RAN xApps: Survey and Research Challenges, Computer Networks 2025  |  Anomaly Detection for xApp and E2 Threats, IEEE 2025"
  );
  const gaps = [
    ["01", "Attack and fault ambiguity", "Prior detectors usually separate attack from normal operation. Operators must also distinguish attacks from real clock, path and configuration faults."],
    ["02", "Unfair AI claims", "Reported model accuracy can look strong without a held-out split, a rule comparator and a trivial constant baseline."],
    ["03", "Protocol evidence separated from ML", "Standards checks and statistical models often appear as separate approaches instead of being evaluated on the same executed runs."],
    ["04", "Detection separated from safe response", "A label alone does not determine whether the network should isolate a source, enter holdover or request operator review."],
  ];
  let y = 188;
  for (const [num, heading, body] of gaps) {
    rect(slide, 60, y, 46, 46, C.blue, C.blue, true);
    textBox(slide, num, 60, y + 10, 46, 23, { size: 15, color: C.white, bold: true, align: "center" });
    textBox(slide, heading, 125, y - 1, 365, 28, { size: 20, color: C.navy, bold: true, font: "Cambria" });
    textBox(slide, body, 125, y + 31, 675, 54, { size: 15.2, color: C.gray });
    y += 101;
  }
  rect(slide, 835, 187, 385, 394, C.dark, C.dark, true);
  textBox(slide, "RESULTING STUDY DESIGN", 865, 215, 325, 24, { size: 12.5, color: C.teal, bold: true });
  const design = [
    ["Matched scenarios", "Attacks and benign lookalikes execute through the same packet path."],
    ["Two decision arms", "ARM A applies standards and operator context. ARM B applies RF plus Isolation Forest."],
    ["Held-out evaluation", "Repetitions 9–12 remain outside training for the 56-run final test."],
    ["Trivial control", "Always-BENIGN establishes whether ARM B adds meaningful information."],
    ["Abstention", "Ambiguous evidence can escalate instead of forcing an unsafe answer."],
  ];
  let dy = 255;
  for (const [heading, body] of design) {
    textBox(slide, heading, 865, dy, 325, 23, { size: 16, color: C.white, bold: true, font: "Cambria" });
    textBox(slide, body, 865, dy + 25, 325, 41, { size: 13.3, color: "#CFD9E5" });
    dy += 65;
  }
  rect(slide, 60, 615, 1160, 59, "#DDF5EF", C.teal, true);
  textBox(slide, "Defensible gap: the reviewed source set did not identify this exact combination of S-plane benign lookalikes, standards-aware rules, ML, abstention and a constant baseline on one held-out campaign.", 82, 630, 1116, 34, { size: 14.2, color: "#0B5547", bold: true, font: "Cambria" });
  slide.speakerNotes.textFrame.setText([
    "Sources:",
    "Federated Continual Learning for Sustainable O-RAN Anomaly Detection, IEEE WCNC, 2024.",
    "Adversarial Machine Learning Threat Analysis and Remediation in Open Radio Access Network, Journal of Network and Computer Applications, 2024. DOI 10.1016/j.jnca.2024.104090.",
    "O-RAN xApps: Survey and Research Challenges, Computer Networks, 2025.",
    "Anomaly Detection for xApp and E2 Interface Threats in O-RAN Near-RT RIC, IEEE, 2025.",
    "The novelty statement is bounded to the reviewed local literature and the demonstrated experimental design.",
  ].join("\n"));
}

// Slide 8: standards grounding
{
  const slide = insertNextSlide();
  baseSlide(
    slide,
    "WORKLET M1: STANDARDS MAPPING (COMPLETED)",
    "Telecom Standards and Profile Grounding",
    "Normative basis: IEEE 1588-2019  |  O-RAN WG4 CUS-Plane Specification  |  O-RAN WG11 Threat Model  |  ITU-T G.8275.1 telecom PTP profile\nTiming performance context: ITU-T G.8273.2 telecom boundary clocks  |  Frequency synchronization context: ITU-T G.8262 SyncE"
  );
  textBox(slide, "AUTHORITY", 70, 174, 245, 24, { size: 12, color: C.blue, bold: true });
  textBox(slide, "WHAT IT DEFINES", 335, 174, 405, 24, { size: 12, color: C.blue, bold: true });
  textBox(slide, "HOW OUR PROJECT USES IT", 770, 174, 420, 24, { size: 12, color: C.blue, bold: true });
  rowRule(slide, 201);
  const rows = [
    ["IEEE 1588-2019", "Legal PTP message fields, datasets and clock behaviour.", "ARM A checks field legality, sequence continuity and timing evidence."],
    ["O-RAN WG4 CUS", "Open Fronthaul C/U/S-plane architecture and synchronization configurations.", "Defines the O-DU–O-RU S-plane boundary used by the experiment."],
    ["O-RAN WG11", "Open Fronthaul threats, including malicious timing-source behaviour.", "Justifies PTP master spoofing as a recognized O-RAN security scenario."],
    ["ITU-T G.8275.1", "Telecom PTP profile for phase and time distribution.", "Grounds profile configuration and telecom-specific clock expectations."],
    ["ITU-T G.8273.2", "Timing characteristics and limits for telecom boundary clocks.", "Provides performance context for interpreting timing-quality evidence."],
  ];
  let y = 214;
  for (const [authority, defines, use] of rows) {
    textBox(slide, authority, 70, y + 8, 245, 48, { size: 17, color: C.navy, bold: true, font: "Cambria" });
    textBox(slide, defines, 335, y + 7, 400, 56, { size: 14.6, color: C.gray });
    textBox(slide, use, 770, y + 7, 420, 56, { size: 14.6, color: C.navy });
    rowRule(slide, y + 69);
    y += 76;
  }
  rect(slide, 60, 604, 1160, 72, "#FFF8E8", C.amber, true);
  textBox(slide, "Scope disclosure", 82, 619, 190, 25, { size: 16, color: C.amber, bold: true, font: "Cambria" });
  textBox(slide, "The software testbed exercised PTP. It did not implement SyncE hardware. Measured detector thresholds remain experimental unless a normative clause defines them.", 265, 618, 930, 38, { size: 14.7, color: C.navy, bold: true });
  slide.speakerNotes.textFrame.setText([
    "Normative and authoritative sources:",
    "IEEE Std 1588-2019, Precision Clock Synchronization Protocol for Networked Measurement and Control Systems.",
    "O-RAN Alliance WG4, Control, User and Synchronization Plane Specification, O-RAN.WG4.CUS.0.",
    "O-RAN Alliance WG11, Security Threat Modeling and Remediation Analysis.",
    "ITU-T G.8275.1, Precision time protocol telecom profile for phase/time synchronization with full timing support from the network.",
    "ITU-T G.8273.2, Timing characteristics of telecom boundary clocks and telecom time slave clocks.",
    "ITU-T G.8262, Timing characteristics of synchronous Ethernet equipment slave clock. SyncE was outside the software testbed.",
  ].join("\n"));
}

// Slide 9: novelty and real-system relevance
{
  const slide = insertNextSlide();
  baseSlide(
    slide,
    "WORKLET M1: PROJECT JUSTIFICATION (COMPLETED)",
    "Standards-Grounded Novelty and Real-System Relevance",
    "Evidence chain: O-RAN WG4 and WG11 define the operational boundary and threat  |  IEEE 1588 and ITU-T profiles define expected timing behaviour\n+Research comparison: TIMESAFE, digital-twin literature and O-RAN AI/ML testbeds define the prior-art boundary"
  );
  const stages = [
    ["01", "Normative ground", "Protocol legality and telecom timing expectations come from recognized standards."],
    ["02", "Executed evidence", "Real PTP daemons, packet captures and telemetry create auditable observations."],
    ["03", "Fair comparison", "Rules, ML and always-BENIGN run against the same 56 held-out cases."],
    ["04", "Governed response", "ATTACK, BENIGN and UNKNOWN map to isolation, holdover or escalation policy."],
  ];
  let x = 60;
  for (let i = 0; i < stages.length; i += 1) {
    const [num, heading, body] = stages[i];
    if (i > 0) rect(slide, x - 29, 290, 23, 2, C.teal);
    rect(slide, x, 184, 260, 214, i === 2 ? "#DDF5EF" : C.white, i === 2 ? C.teal : C.rule, true);
    textBox(slide, num, x + 20, 204, 44, 28, { size: 18, color: C.blue, bold: true, font: "Cambria" });
    textBox(slide, heading, x + 20, 244, 220, 32, { size: 20, color: C.navy, bold: true, font: "Cambria" });
    textBox(slide, body, x + 20, 291, 220, 83, { size: 14.5, color: C.gray });
    x += 300;
  }
  rect(slide, 60, 432, 555, 172, C.dark, C.dark, true);
  textBox(slide, "VALIDATED IN THIS CAMPAIGN", 85, 454, 500, 24, { size: 12.5, color: C.teal, bold: true });
  textBox(slide, "Live PTP packet-path execution\nHeld-out attack and benign-fault classification\nARM A versus ARM B versus constant control\nExplicit abstention and evidence provenance", 85, 491, 500, 96, { size: 16, color: C.white });
  rect(slide, 665, 432, 555, 172, C.pale, C.blue, true);
  textBox(slide, "NEXT PROOF REQUIRED", 690, 454, 500, 24, { size: 12.5, color: C.blue, bold: true });
  textBox(slide, "Digital-twin action verification\nExecuted isolate or holdover recovery\nMeasured MTTR and availability improvement\nA stronger ML model that exceeds transparent baselines", 690, 491, 500, 96, { size: 16, color: C.navy });
  rect(slide, 60, 627, 1160, 50, C.dark, C.dark, true);
  textBox(slide, "Defensible novelty: a standards-aware, controlled S-plane benchmark that tests whether AI adds value before granting it authority over recovery.", 82, 640, 1116, 28, { size: 15, color: C.white, bold: true, font: "Cambria" });
  slide.speakerNotes.textFrame.setText([
    "This slide distinguishes demonstrated novelty from future scope.",
    "Validated: packet-path execution, evidence extraction, held-out classification, rule-versus-ML comparison, trivial baseline, abstention and provenance.",
    "Not validated in the current campaign: digital-twin orchestration, automatic recovery execution, MTTR reduction or availability improvement.",
    "The novelty claim remains bounded to the reviewed literature set and the experimental design actually executed.",
  ].join("\n"));
}

const candidatePath = path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v6_candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const sourceHash = crypto.createHash("sha256").update(await fs.readFile(sourcePath)).digest("hex");
const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href);
await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable,
  integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  explicitTotalSlideCount: 31,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: "reference", families: ["Cambria", "Calibri", "Courier New"], referencePath: sourcePath, referenceSha256: sourceHash },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v6.validation.json"),
});

const finalDeck = await PresentationFile.importPptx(await FileBlob.load(finalPath));
const montage = await finalDeck.export({ format: "png", montage: true, scale: 0.65 });
await fs.writeFile(path.join(buildDir, "v6-montage.png"), new Uint8Array(await montage.arrayBuffer()));
for (let i = 0; i < finalDeck.slides.items.length; i += 1) {
  const png = await finalDeck.slides.getItem(i).export({ format: "png", scale: 1 });
  await fs.writeFile(path.join(buildDir, `v6-slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
}
console.log(finalPath);
