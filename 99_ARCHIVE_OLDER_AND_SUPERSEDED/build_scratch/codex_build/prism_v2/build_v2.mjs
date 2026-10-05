import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin";
const sourcePath = path.join(workspaceDir, "ORAN_SPlane_PRISM_Review_1.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v2.pptx");
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

// Slide 1: replace the unreadable, PII-heavy screenshot with a clean worklet brief.
{
  const slide = presentation.slides.getItem(0);
  const bg = slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: 1280, height: 720 },
    fill: "#F8FAFC",
    line: { fill: "none", width: 0 },
  });
  bg.name = "V2 clean worklet brief background";
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 1280, height: 16 }, fill: "#18B89A", line: { fill: "none", width: 0 } });
  addText(slide, "SAMSUNG PRISM WORKLET", { left: 64, top: 48, width: 520, height: 28 }, { typeface: "Calibri", fontSize: 15, bold: true, color: "#1C7293" });
  addText(slide, "AI-Native Self-Healing O-RAN Network using a Digital Twin", { left: 64, top: 82, width: 1152, height: 104 }, { typeface: "Cambria", fontSize: 42, bold: true, color: "#12263A" });
  addText(slide, "Validated sub-scope: Open Fronthaul S-plane timing security", { left: 64, top: 190, width: 1152, height: 38 }, { typeface: "Calibri", fontSize: 22, color: "#5B6B7C" });

  const cards = [
    ["CORE QUESTION", "Can benign timing faults be distinguished from attacks before choosing a recovery action?", "#1C7293"],
    ["VALIDATED EVIDENCE", "Six-daemon standards-based testbed, 168-run campaign, and a held-out AI-versus-rule comparison.", "#18B89A"],
    ["SCOPE BOUNDARY", "This campaign validates detection and classification. Digital-twin orchestration and closed-loop healing were not validated in it.", "#B3402F"],
  ];
  cards.forEach(([heading, body, color], i) => {
    const left = 64 + i * 390;
    slide.shapes.add({ geometry: "roundRect", position: { left, top: 286, width: 356, height: 228 }, fill: "#FFFFFF", line: { fill: "#D7E1EA", width: 1.2 } });
    slide.shapes.add({ geometry: "rect", position: { left: left + 24, top: 318, width: 54, height: 5 }, fill: color, line: { fill: "none", width: 0 } });
    addText(slide, heading, { left: left + 24, top: 338, width: 308, height: 30 }, { typeface: "Calibri", fontSize: 14, bold: true, color });
    addText(slide, body, { left: left + 24, top: 382, width: 308, height: 104 }, { typeface: "Calibri", fontSize: 18, color: "#12263A" });
  });
  addText(slide, "Team: Tanmaya Kumar · Raghu Ram K · Munipalle Jaswanth Kumar", { left: 64, top: 618, width: 780, height: 28 }, { typeface: "Calibri", fontSize: 15, color: "#5B6B7C" });
  addText(slide, "Evidence review updated 24 Sep 2026", { left: 844, top: 618, width: 372, height: 28 }, { typeface: "Calibri", fontSize: 15, color: "#5B6B7C", alignment: "right" });
  setNotes(0, "Clean worklet brief for the reviewed deck. Personal email addresses and phone numbers from the original screenshot are intentionally omitted. The validated scope is S-plane detection and classification; digital-twin orchestration and closed-loop healing remain outside this campaign.");
}

// Slides 3-4: larger, professional problem framing and evidence-accurate wording.
edit(2, "THE PROBLEM", "PROBLEM STATEMENT", { fontSize: 20 });
edit(2, "Radios must agree", "Tightly bounded time alignment underpins Open Fronthaul", { fontSize: 50.67, autoFit: "shrinkText" });
edit(2, "Relative time alignment", "Category-A relative alignment target between radio units\nO-RAN Open Fronthaul CUS-plane specification", { fontSize: 14.67 });
edit(2, "End-to-end network", "Application-level time-error limit from O-RU to PRTC\nITU-T G.8271.1", { fontSize: 14.67 });
edit(2, "Fastest publicly", "Observed service failure after a timing attack in one study\nTIMESAFE", { fontSize: 14.67 });
edit(2, "That is what makes", "Because timing is distributed as network traffic, it is attackable. Loss of a shared time reference can degrade radio coordination, making the S-plane a security surface as well as an engineering constraint.", { fontSize: 16.67 });
setNotes(2, "The 130 ns value is category-specific, the ±1.5 µs value is an application-level O-RU-to-PRTC limit, and the roughly 2 s result is an observation from TIMESAFE, not a standardised bound or a fastest-known claim.");

edit(3, "THE CORE QUESTION", "RESEARCH QUESTION", { fontSize: 20 });
edit(3, "Same symptom", "Can timing attacks be distinguished from benign faults?", { fontSize: 50.67, autoFit: "shrinkText" });
edit(3, "From the packets alone", "For selected look-alike events, packet symptoms overlap. The decision requires protocol legality and provisioned operator context.", { fontSize: 20.67 });

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

const requirements = {
  explicitTotalSlideCount: 25,
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
const candidatePath = path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v2_candidate.pptx");
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
  receiptPath: path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v2.validation.json"),
});
process.stdout.write(JSON.stringify({ finalPath, result }, null, 2));
