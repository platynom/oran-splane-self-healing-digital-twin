import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin";
const sourcePath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v4.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v5.pptx");
const skillDir = "C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.927.11222/skills/presentations";
const runtimePython = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
process.env.RUNTIME_NODE_MODULES = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({ kind: "textbox", include: "id,slide,bbox,text", maxChars: 400000 });
const records = snapshot.ndjson.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));

function edit(slideIndex, needle, replacement, options = {}) {
  const hits = records.filter((r) => r.slideIndex === slideIndex && (r.text ?? "").includes(needle));
  if (hits.length !== 1) throw new Error(`Expected one text box on slide ${slideIndex + 1} containing ${JSON.stringify(needle)}, found ${hits.length}`);
  const target = presentation.resolve(hits[0].id);
  target.text.replace(needle, replacement);
  if (options.fontSize !== undefined) target.text.fontSize = options.fontSize;
  if (options.autoFit !== undefined) target.text.autoFit = options.autoFit;
  return target;
}

function editExact(slideIndex, needle, replacement, options = {}) {
  const hits = records.filter((r) => r.slideIndex === slideIndex && (r.text ?? "") === needle);
  if (hits.length !== 1) throw new Error(`Expected one exact text box on slide ${slideIndex + 1} equal to ${JSON.stringify(needle)}, found ${hits.length}`);
  const target = presentation.resolve(hits[0].id);
  target.text.replace(needle, replacement);
  if (options.fontSize !== undefined) target.text.fontSize = options.fontSize;
  if (options.autoFit !== undefined) target.text.autoFit = options.autoFit;
  return target;
}

function editExactNth(slideIndex, needle, ordinal, replacement, options = {}) {
  const hits = records.filter((r) => r.slideIndex === slideIndex && (r.text ?? "") === needle);
  if (hits.length <= ordinal) throw new Error(`Expected exact text box ${ordinal} on slide ${slideIndex + 1} equal to ${JSON.stringify(needle)}, found ${hits.length}`);
  const target = presentation.resolve(hits[ordinal].id);
  target.text.replace(needle, replacement);
  if (options.fontSize !== undefined) target.text.fontSize = options.fontSize;
  if (options.autoFit !== undefined) target.text.autoFit = options.autoFit;
  return target;
}

function setNotes(slideIndex, text) {
  presentation.slides.getItem(slideIndex).speakerNotes.textFrame.setText(text);
  presentation.slides.getItem(slideIndex).speakerNotes.setVisible(true);
}

// Slides 1-2 are intentionally untouched. Slide 1 remains the supplied worklet image.
edit(2, "PROJECT HIT: OPEN FRONTHAUL S-PLANE\nPTP / SyncE timing evidence captured on brUP and brDN", "PROJECT FOCUS: OPEN FRONTHAUL S-PLANE\nPTP timing evidence observed on brUP and brDN; SyncE was outside this software testbed", { autoFit: "shrinkText" });
edit(2, "Validated here: packet capture, feature extraction and classification. Remaining scope: digital-twin orchestration and automated recovery.", "Validated here: live packet-path execution, extracted timing evidence and classification. Remaining scope: digital-twin orchestration, fault prediction, automated recovery and outcome measurement.", { autoFit: "shrinkText" });

edit(3, "Category-A relative alignment target between radio units\nO-RAN Open Fronthaul CUS-plane specification", "5G FR2 intraband-contiguous CA relative TAE · Timing Category A\nPairwise; ≈±65 ns/RU only under equal allocation", { autoFit: "shrinkText" });
edit(3, "1.5 µs", "±1.5 µs", { autoFit: "shrinkText" });
edit(3, "Application-level time-error limit from O-RU to PRTC\nITU-T G.8271.1", "End-application absolute time-error limit at reference point E\nRelative to a common recognized time standard · ITU-T G.8271.1", { autoFit: "shrinkText" });
edit(3, "Observed service failure after a timing attack in one study\nTIMESAFE", "Observed RU crash after a timing attack in one published study\nTIMESAFE · ACM TOPS · DOI 10.1145/3775060", { autoFit: "shrinkText" });
edit(3, "The ~2 s figure is an observed result from one published study, not a standardised limit. We treat it as a design target.", "130 ns and ±1.5 µs re-express upstream 3GPP radio requirements. TIMESAFE observed an RU software crash requiring manual reboot with dynamic PTP-port roles; another configuration degraded over ~580 s. These are study-specific, not standardised limits.", { autoFit: "shrinkText" });

edit(6, "M4 and M6 closed by the AI-vs-rule comparison completed on the 168-run campaign (slide 20).", "M4 model evaluation and M6 testing are supported by 56 held-out runs from the 168-run campaign (slide 21). M3 and M5 remain partial; prediction, healing execution and outcome metrics remain open.", { autoFit: "shrinkText" });
editExact(6, "HARDWARE-BLOCKED", "", { autoFit: "shrinkText" });
editExactNth(6, "M6", 0, "M6a", { autoFit: "shrinkText" });
editExactNth(6, "M6", 1, "M6b", { autoFit: "shrinkText" });

edit(7, "IsolationForest open-set layer providing abstention", "IsolationForest open-set layer intended to provide abstention (held-out score: 0.000)", { autoFit: "shrinkText" });

edit(8, "tcpdump on both bridges — every PTP frame on the wire is recorded, unmodified.", "tcpdump was configured on both bridges. The corrected archive retains extracted deep CSVs and decisions, but not the source PCAPs.", { autoFit: "shrinkText" });

edit(9, "The campaign read back every configuration value from the running system and traced it to the governing standard.", "Configuration values are consistent with repository scripts and cited standards; the corrected archive does not retain the complete runtime config set.", { autoFit: "shrinkText" });
edit(9, "G.8275.1 forwardable address", "Permitted forwardable address; ptp4l global default", { autoFit: "shrinkText" });
edit(9, "Some ITU-T values are cited via vendor application notes because the normative recommendations are paywalled — disclosed in the workbooks.", "Official ITU recommendation pages are cited. Where full normative text is access-restricted, V5 distinguishes primary metadata from corroborating implementation documentation.", { autoFit: "shrinkText" });

edit(10, "Software timestamping only: microsecond noise floor against a nanosecond target", "Software timestamping only: baseline mean |offset| = 1,866 ns in this testbed, above the 130 ns category-specific target", { autoFit: "shrinkText" });

edit(12, "WORKLET M5: DECISION ENGINE (COMPLETED)", "WORKLET M5: DECISION ENGINE (PARTIAL — CLASSIFICATION EVALUATED)", { autoFit: "shrinkText" });
edit(12, "clockClass 6→7 on GNSS loss, an ESMC quality downgrade, drift bounded by the holdover mask.", "clockClass 6→7 for a T-GM entering holdover while still within its configured specification, or drift bounded by an explicit holdover mask.", { autoFit: "shrinkText" });

edit(13, "WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)", "WORKLET M5: SAFE ABSTENTION LOGIC (PARTIAL — VERDICT LOGIC EVALUATED)", { autoFit: "shrinkText" });
edit(13, "ISOLATE", "ISOLATE — recommended response; not executed", { autoFit: "shrinkText" });
edit(13, "TOLERATE / HOLDOVER", "TOLERATE / HOLDOVER — recommended; not executed", { autoFit: "shrinkText" });

edit(14, "Attack classes align where applicable with ETSI TR 104 106. Benign classes are test conditions, not threat identifiers. SW* means software detection logic only; physical impact needs hardware.", "ETSI mapping is partial: A5→T-SPLANE-01, A1→T-SPLANE-02/-03, C1→T-SPLANE-04, A4 delay→T-SPLANE-05. Replay and GNSS classes lack a clean one-to-one mapping. Eight of 16 A/B classes were run. SW* means detection logic only; physical impact needs hardware.", { autoFit: "shrinkText" });
for (const code of ["A1", "A2", "A3", "A5", "A8", "B2", "B3", "B7"]) editExact(14, code, `${code} · TESTED`, { autoFit: "shrinkText" });

edit(15, "WORKLET M3: FAULT INJECTION (COMPLETED)", "WORKLET M3: FAULT INJECTION (PARTIAL — DIGITAL TWIN NOT RUN)", { autoFit: "shrinkText" });
edit(15, "A new namespace runs a genuine ptp4l with attacker-chosen identity and a superior priority2, then competes in BMCA for real.", "A new namespace runs genuine ptp4l with an unallow-listed identity and a superior dataset, then competes under the G.8275.1 alternate BMCA.", { autoFit: "shrinkText" });
edit(15, "Hand-built frames: forged Sync with manipulated originTimestamp; illegal version/length/control fields; Announce with leap61 set and UTC offset wrong.", "Hand-built frames: forged two-step timing messages; C2 uses versionPTP=3, a reserved message type and a short length; C3 changes leap61/UTC properties. G.8275.1 ignores controlField, so it is not used as sole legality evidence.", { autoFit: "shrinkText" });
edit(15, "An attack and its benign twin are often the same physical action — what separates them is the provisioned context, not the packets.", "An attack and its benign twin can share a packet-path mechanism; provisioned context separates them. IEEE 1588-2019: timePropertiesDS §8.2.4; leap-second handling §9.4. controlField is deprecated and ignored by G.8275.1.", { autoFit: "shrinkText" });

edit(16, "rules scored on the same runs", "rules scored on the same captures; v2 and v3 verdicts are identical", { autoFit: "shrinkText" });

edit(17, "95% CI", "95% CI\n(v3, Wilson)", { autoFit: "shrinkText" });
edit(17, "Green = the three coverage gaps closed this cycle. Red = the one known open failure, B_bc_replacement, explained on slide 22.", "Green = three post-campaign coverage fixes. Red = the dominant open false-positive scenario, B_bc_replacement, explained on slide 23. B3 also contains one UNKNOWN benign run.", { autoFit: "shrinkText" });

edit(18, "Macro attack sensitivity", "Macro attack sensitivity · v3", { autoFit: "shrinkText" });
edit(18, "across 8 attack scenarios", "Base rule on same captures: 0.625", { autoFit: "shrinkText" });
edit(18, "Attribution accuracy", "Attribution accuracy · v3", { autoFit: "shrinkText" });
edit(18, "correct fault identified", "84/96 attack runs", { autoFit: "shrinkText" });
edit(18, "Three coverage gaps closed this cycle: packet removal, malformed frames and whole-second abuse went from 0/12 to 11/12, 12/12 and 12/12 — with no loss of specificity.", "The v3 defect-fix rule closes three observed coverage gaps on the same captures: C1 11/12, C2 12/12 and C3 12/12. This is transparent post-observation evaluation, not independent pre-registered validation.", { autoFit: "shrinkText" });
edit(18, "Specificity is 0.783 — not 1.000 — because of a single known failure. We report it rather than exclude it.", "Specificity is 0.783 because B_bc_replacement yields 12 false ATTACK calls and B3 has one UNKNOWN. Excluding B_bc_replacement, specificity is 47/48 = 0.979.", { autoFit: "shrinkText" });

edit(19, "The evaluation measured adjacent interception levels and reports the approximately 62% boundary as an interpolation.", "The tested bracket is 60–65%. Linear interpolation of the observed/declared ratio gives a 60.54% threshold crossing.", { autoFit: "shrinkText" });
edit(19, "Fraction of the observation window blackholed", "Configured blackhole fraction of the post-warm-up C1 injection window", { autoFit: "shrinkText" });
edit(19, "75 %", "75 % · n=6", { autoFit: "shrinkText" });
edit(19, "observed / declared rate  0.366", "median observed / declared rate  0.366530", { autoFit: "shrinkText" });
edit(19, "70 %", "70 % · n=3", { autoFit: "shrinkText" });
edit(19, "observed / declared rate  0.414", "median observed / declared rate  0.413656", { autoFit: "shrinkText" });
edit(19, "65 %", "65 % · n=2", { autoFit: "shrinkText" });
edit(19, "observed / declared rate  0.458", "observed ratios  0.4581 / 0.4619", { autoFit: "shrinkText" });
editExact(19, "60 %", "60 % · n=1", { autoFit: "shrinkText" });
edit(19, "observed / declared rate  0.505", "observed / declared rate  0.504889", { autoFit: "shrinkText" });
edit(19, "The detector fires when a source delivers below half the rate it itself declares. At a 60 % blackhole the ratio is 0.505 — a 1 % margin above the threshold, so the attack evades.", "The detector fires below 0.500. At 60%, ratio 0.504889 is 0.004889 absolute (0.98% relative) above threshold, so it evades.", { autoFit: "shrinkText" });
edit(19, "Observed: 65% blackhole was caught and 60% was missed. The ~62% evasion boundary is an interpolation, not a directly tested point. Short or bursty interception may average out.", "Observed: 65% caught; 60% missed. The 60.54% crossing is linearly interpolated, not measured. Configured 55% was never drawn; window arithmetic predicts ratio ≈0.568, also missed.", { autoFit: "shrinkText" });

edit(20, "ARM B outputs BENIGN on 47/56 and has ROC-AUC 0.604.", "ARM B outputs BENIGN on 47/56 and has window-level ROC-AUC 0.604 across 1,923 known-scenario windows.", { autoFit: "shrinkText" });

edit(21, "Its input is suppressed by the attacks it must detect", "Telemetry starvation compounds broader feature poverty", { autoFit: "shrinkText" });
edit(21, "C1 blackholes the timing path and C3 disrupts BMCA. Servo samples fall from 88 per baseline run to 44 and 28. The ML arm loses evidence; the rule arm can still use packet-rate deficit plus legality and context evidence.", "Servo samples average 88.0 per baseline run, 44.5 for C1 and 28.0 for C3. Starvation hurts those cases, but ARM B sensitivity is also low where telemetry remains; feature poverty and class overlap are primary constraints.", { autoFit: "shrinkText" });
edit(21, "Only 6 of 28 features were observable", "Only 6 of 28 configured features were populated and used", { autoFit: "shrinkText" });
edit(21, "GNSS, SyncE, oscillator and all protocol-legality features are absent from ptp4l servo logs. The model could key only on offset, path-delay and PDV magnitude.", "GNSS, SyncE, oscillator and protocol-legality features are absent from ptp4l servo logs. Six features were used, but holdover_rate had zero importance; five features carried model signal.", { autoFit: "shrinkText" });

edit(22, "This one scenario is the entire reason specificity is 0.783 rather than 1.000. Fix requires an allow-list change and a re-freeze.", "This scenario causes 12 false ATTACK calls and dominates the 0.783 specificity. B3 contributes one UNKNOWN; excluding BC replacement, specificity is 47/48 = 0.979. Fix requires an allow-list change and a re-freeze.", { autoFit: "shrinkText" });
edit(22, "A coherent GNSS spoof is undetectable", "GNSS spoofing is not established by this testbed", { autoFit: "shrinkText" });
edit(22, "physical limit", "testbed limit", { autoFit: "shrinkText" });
edit(22, "A spoof that perfectly mimics a healthy clock is in-distribution from a single reference. No software feature engineering removes this — it needs an independently trustworthy anchor.", "Downstream ptp4l telemetry alone cannot establish coherent-spoof detection. Trusted receiver/RF observables, spatial checks or an independent time anchor are outside this setup.", { autoFit: "shrinkText" });

edit(23, "36 “replicates” were one capture copied 12 times", "36 “replicates” were three captures copied 12 times", { autoFit: "shrinkText" });
edit(23, "A script created non-executable returned exit 126, silenced by output redirection; a stale capture then satisfied the validity guard.", "A script was created without the execute bit; exit 126 was silenced by redirection, and a stale capture satisfied the validity guard.", { autoFit: "shrinkText" });
edit(23, "Pooled metrics moved with run count; additive-only was “proven” by comparing two scalars.", "Pooled metrics moved with run count; an additive-only effect had been asserted from two scalars with no per-run test. V2 and v3 were subsequently compared on all 168 captures.", { autoFit: "shrinkText" });

edit(24, "Test additional interception levels around the interpolated ~62% boundary", "Test additional interception levels around the interpolated 60.54% crossing", { autoFit: "shrinkText" });
edit(24, "M6 deliverable: paper and IP disclosure draft", "Fault prediction before disruption — not attempted\nExecute and measure corrective action — verdict labels are not actions taken\nExercise the digital twin — not run in this campaign\nMeasure MTTR, recovery time, availability and downtime — no figure yet\nM6 deliverable: paper and IP disclosure draft", { autoFit: "shrinkText" });

edit(25, "0.990 macro attack sensitivity", "0.990 macro attack sensitivity · post-observation v3", { autoFit: "shrinkText" });
edit(25, "Three coverage gaps closed; benign specificity remains 0.783", "Pre-frozen base: 0.625; specificity: 0.783 (0.979 excluding BC replacement)", { autoFit: "shrinkText" });
edit(25, "~62% is interpolated; BC replacement remains open; 5 HW plus 3 detection-only classes", "60.54% is interpolated; BC replacement remains open; source PCAPs are not retained in the corrected archive", { autoFit: "shrinkText" });
edit(25, "WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE", "STATUS: S-PLANE DETECTION AND CLASSIFICATION EVALUATED · PREDICTION, DIGITAL TWIN AND HEALING NOT YET RUN", { autoFit: "shrinkText" });

// Insert the required objectives-not-yet-addressed slide immediately before the closing slide.
const inserted = presentation.slides.add();
inserted.moveTo(25);
inserted.shapes.add({ geometry: "rect", name: "background", position: { left: 0, top: 0, width: 1280, height: 720 }, fill: { type: "solid", color: "#07121F" }, line: { style: "solid", fill: "#07121F", width: 0 } });
function addText(text, x, y, w, h, size, color = "#FFFFFF", bold = false, name = undefined) {
  const box = inserted.shapes.add({ geometry: "textbox", name, position: { left: x, top: y, width: w, height: h }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
  box.text = text;
  box.text.fontFamily = "Calibri";
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = bold;
  box.text.autoFit = "shrinkText";
  return box;
}
addText("WORKLET SCOPE DISCLOSURE", 60, 26, 1160, 28, 13, "#51D6C9", true, "kicker");
addText("Objectives Not Yet Addressed", 60, 62, 1160, 58, 36, "#FFFFFF", true, "title");
addText("1", 70, 154, 45, 40, 24, "#51D6C9", true);
addText("Fault prediction", 125, 150, 340, 30, 20, "#FFFFFF", true);
addText("Prediction before service disruption was not attempted.", 125, 184, 1015, 44, 18, "#C7D5E5");
addText("2", 70, 268, 45, 40, 24, "#51D6C9", true);
addText("Corrective action", 125, 264, 340, 30, 20, "#FFFFFF", true);
addText("No corrective action was executed or measured. ISOLATE, HOLDOVER and ESCALATE elsewhere are verdict outputs—not actions taken.", 125, 298, 1015, 52, 18, "#C7D5E5");
addText("3", 70, 390, 45, 40, 24, "#51D6C9", true);
addText("Digital twin", 125, 386, 340, 30, 20, "#FFFFFF", true);
addText("The digital twin was not exercised in this campaign.", 125, 420, 1015, 44, 18, "#C7D5E5");
addText("4", 70, 508, 45, 40, 24, "#51D6C9", true);
addText("Outcome metrics", 125, 504, 340, 30, 20, "#FFFFFF", true);
addText("No MTTR, recovery-time, availability or downtime figure was measured here.", 125, 538, 1015, 52, 18, "#C7D5E5");
addText("Next gate · execute the missing objectives and measure recovery outcomes before claiming self-healing", 60, 646, 1160, 24, 13, "#7FA8C9", true, "footer");

setNotes(2, "Architecture scope: O-RAN reference architecture and this repository's six-daemon S-plane testbed. The corrected archive retains extracted evidence, not PCAP files. O-RAN overview: https://mediastorage.o-ran.org/overview/O-RAN.Overview-of-the-O-RAN-ALLIANCE-presentation.pdf");
setNotes(3, "Standards scope verified 2026-09-28. 130 ns: ETSI TS 103 859 V7.0.2, table for 5G FR2 intraband-contiguous CA relative TAE, Timing Category A: https://www.etsi.org/deliver/etsi_ts/103800_103899/103859/07.00.02_60/ts_103859v070002p.pdf . ±1.5 µs: ITU-T G.8271.1 reference point E/end application relative to common recognized time standard: https://www.itu.int/rec/T-REC-G.8271.1/ . TIMESAFE: ACM TOPS DOI https://doi.org/10.1145/3775060 .");
setNotes(6, "Independent V5 audit: M3 remains partial because a digital twin was not run; M5 remains partial because response labels were not executed as closed-loop actions. Objective 2 prediction and MTTR/availability outcomes were not measured.");
setNotes(8, "The corrected campaign archive SHA-256 is 6149b4fb15940cdac694ba8666d97041b4eb62d5523d2631c1edf96d531e4ed9 with 1,096 entries and 168 run directories. It contains scenario-named deep CSVs, context and decisions, but no retained PCAP files.");
setNotes(9, "G.8275.1 profile source: https://www.itu.int/rec/T-REC-G.8275.1/ . The forwardable destination is permitted, but 01:1B:19:00:00:00 is ptp4l's global default rather than the profile reference address. Complete runtime cfg files are absent from the corrected archive.");
setNotes(10, "Direct retained-servo parsing: baseline 1,056 samples, mean |offset| 1,866.252 ns; C1 534 samples, 1,583.672 ns; C3 336 samples, 1,764.598 ns. This supports a testbed-specific limitation, not a universal software-timestamping range. Linux timestamping documentation: https://docs.kernel.org/networking/timestamping.html");
setNotes(12, "ClockClass 6→7 is valid for a T-GM entering holdover only while it remains within its configured specification. Verdict labels were evaluated; response actions were not executed.");
setNotes(14, "ETSI TR 104 106 V3.0.0 mappings: T-SPLANE-01 DoS, -02 spoofed GM, -03 rogue PTP instance, -04 selective interception/removal, -05 delay manipulation. Source: https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf");
setNotes(15, "C2 remains malformed because of versionPTP=3, reserved message type and short length. controlField is ignored by G.8275.1 and is not a standalone profile-legality discriminator. For two-step operation, preciseOriginTimestamp is carried in Follow_Up; Sync originTimestamp is not authoritative.");
setNotes(18, "Independent recomputation from all 168 retained run directories: base macro sensitivity 0.625; v3 95/96 attack detections = 0.989583 macro sensitivity; specificity 47/60 = 0.783333; specificity excluding BC replacement 47/48 = 0.979167; attribution 84/96 = 0.875. V3 is post-observation and not an independent pre-registered validation.");
setNotes(19, "C1 medians recomputed from retained deep CSVs: 60%=0.504889 (n=1), 65%=0.459859 (n=2), 70%=0.413656 (n=3), 75%=0.366530 (n=6). Linear crossing at ratio 0.500 is 60.542884%. The configured fraction applies to the 36-second post-warm-up injection window, not the whole 44-second capture.");
setNotes(20, "Held-out runs: ARM A 51/56, ARM B 24/56, always-BENIGN 20/56. ARM B versus baseline discordant pairs are 5 and 1; exact two-sided McNemar p=0.21875. ROC-AUC 0.603792 is computed over 1,923 known-scenario windows, not 56 runs. Both ARM B and always-BENIGN score 4/4 on B_bc_replacement.");
setNotes(21, "ARM B used six populated features from 28 configured features; holdover_rate importance is 0. Feature importances: 0.267588, 0.261517, 0.208277, 0.138827, 0.123790 and 0. Servo-sample averages: baseline 88.0/run, C1 44.5/run, C3 28.0/run.");
setNotes(22, "The corrected conclusion is testbed-scoped: downstream ptp4l telemetry cannot establish detection of a coherent GNSS spoof. Additional trusted receiver/RF evidence can support detection. NIST GNSS resilience resources: https://www.nist.gov/pnt . Specificity excluding BC replacement is 47/48, not 1.000.");
setNotes(23, "The 36 invalid runs were three scenario captures copied across 12 replicate directories. V2 and v3 verdicts were compared per run and are identical on all 168 retained captures.");
setNotes(24, "The 60.54% value is interpolated and needs denser direct testing. Worklet objectives still open: prediction before disruption, digital-twin validation, executed corrective action, and measured MTTR/downtime/availability.");
setNotes(25, "Independent V5 corrections are detailed in V5_VERIFICATION_LOG.md and V5_DISAGREEMENTS.md. These statements distinguish measured results, post-observation corrections, standards scope and evidence-retention limits.");
inserted.speakerNotes.textFrame.setText("This slide closes the silent worklet gaps identified by the independent V5 audit. Prediction, executed corrective action, digital-twin validation, and MTTR/recovery/availability/downtime measurement remain future work.");
inserted.speakerNotes.setVisible(true);

const requirements = {
  explicitTotalSlideCount: 27,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  sourceTemplatePath: sourcePath,
};
const fontPolicy = {
  basis: "reference",
  families: ["Cambria", "Calibri", "Courier New"],
  referencePath: sourcePath,
  referenceSha256: "df7f32939b27188207eb98846daa3f5d6890ba37419b68a48c481b6f1837d4ab",
};

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const candidatePath = path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v5_candidate.pptx");
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
  receiptPath: path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v5.validation.json"),
});
process.stdout.write(JSON.stringify({ finalPath, result }, null, 2));
