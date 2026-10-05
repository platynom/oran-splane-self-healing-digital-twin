import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin";
const sourcePath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v3.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "ORAN_SPlane_PRISM_Review_v4.pptx");
const skillDir = "C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.927.11222/skills/presentations";
const runtimePython = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
process.env.RUNTIME_NODE_MODULES = "C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";

const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({ kind: "textbox", include: "id,slide,bbox,text", maxChars: 300000 });
const records = snapshot.ndjson.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));

function edit(slideIndex, needle, replacement, options = {}) {
  const hits = records.filter((r) => r.slideIndex === slideIndex && (r.text ?? "").includes(needle));
  if (hits.length !== 1) throw new Error(`Expected one text box on slide ${slideIndex + 1} containing ${JSON.stringify(needle)}, found ${hits.length}`);
  const target = presentation.resolve(hits[0].id);
  target.text.replace(hits[0].text, replacement);
  if (options.fontSize !== undefined) target.text.fontSize = options.fontSize;
  if (options.autoFit !== undefined) target.text.autoFit = options.autoFit;
  return target;
}

// Declarative titles tied to the objective or milestone shown above each title.
edit(2, "Where the project acts", "End-to-End O-RAN Architecture and S-Plane Project Boundary", { fontSize: 36, autoFit: "shrinkText" });
edit(2, "Completed: mapped", "The mapped architecture isolates the Open Fronthaul S-plane timing boundary between O-DU and O-RU.", { fontSize: 17.33, autoFit: "shrinkText" });

edit(3, "Tightly bounded time alignment", "Open Fronthaul Timing Requirements and Security Exposure", { fontSize: 43, autoFit: "shrinkText" });

const classificationTitle = edit(4, "Can timing attacks", "Timing Attack and Benign Fault Classification", { fontSize: 42, autoFit: "shrinkText" });
classificationTitle.position = { left: 59.52, top: 48, width: 1157.76, height: 69.12 };
classificationTitle.text.alignment = "left";
{
  const kicker = records.find((r) => r.slideIndex === 4 && (r.text ?? "").includes("WORKLET M1: DECISION REQUIREMENTS"));
  if (!kicker) throw new Error("Missing decision-requirements kicker");
  const target = presentation.resolve(kicker.id);
  target.position = { left: 59.52, top: 19.2, width: 1157.76, height: 24.96 };
  target.text.fontSize = 12.67;
  target.text.alignment = "left";
}

edit(5, "Why we scoped", "Rationale for the Open Fronthaul S-Plane Scope", { fontSize: 46, autoFit: "shrinkText" });
edit(5, "The worklet covers", "The selected sub-scope targets timing events where benign faults and attacks require different recovery actions.", { fontSize: 19.33, autoFit: "shrinkText" });

edit(6, "Milestone status", "Worklet Milestone Completion Status", { fontSize: 48, autoFit: "shrinkText" });

edit(7, "Two detection arms", "Rule and ML Detection Evaluation Design", { fontSize: 46, autoFit: "shrinkText" });
edit(7, "Worklet objective 5", "Worklet objective 5 requires a direct comparison between AI-based detection and traditional fault management.", { fontSize: 19.33, autoFit: "shrinkText" });

edit(8, "A real testbed", "Open Fronthaul Timing Testbed with Six Daemons", { fontSize: 44, autoFit: "shrinkText" });

edit(9, "Every value traced", "Timing Configuration Derived from Standards", { fontSize: 46, autoFit: "shrinkText" });
edit(9, "No configuration value", "The campaign read back every configuration value from the running system and traced it to the governing standard.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(10, "What the platform cannot provide", "Verified Platform Constraints", { fontSize: 48, autoFit: "shrinkText" });
edit(10, "Each limit verified", "Direct queries of the running system confirmed each platform limitation.", { fontSize: 19.33, autoFit: "shrinkText" });

edit(11, "Data flow", "Data Flow from Packet Capture to Verdict", { fontSize: 46, autoFit: "shrinkText" });

edit(12, "What separates an attack", "Attack Classification Using Protocol and Operator Context", { fontSize: 43, autoFit: "shrinkText" });
edit(12, "Not the magnitude", "Classification combines protocol consistency, observed timing behaviour and provisioned operator context.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(13, "A detector that will not guess", "Safe Abstention for Ambiguous Timing Events", { fontSize: 46, autoFit: "shrinkText" });
edit(13, "Some faults are genuinely undecidable", "The decision engine abstains when packet evidence cannot support a reliable attack or benign classification.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(14, "16 fault classes", "Fault Taxonomy and Test Coverage", { fontSize: 46, autoFit: "shrinkText" });

edit(15, "Four mechanisms", "Fault Injection on the Live Packet Path", { fontSize: 46, autoFit: "shrinkText" });

edit(16, "How the campaign was run", "Campaign Design and Reproducibility Controls", { fontSize: 44, autoFit: "shrinkText" });
edit(16, "The base rule was pre-frozen", "The campaign froze the base rule before execution. The team documented v3 as a post-campaign defect-fix revision.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(17, "Per-scenario detection", "Detection Results by Scenario", { fontSize: 48, autoFit: "shrinkText" });

edit(18, "Measured on 168 live runs", "Results Across 168 Live Runs", { fontSize: 48, autoFit: "shrinkText" });

edit(19, "Where the interception detector", "Measured Boundary of the Interception Detector", { fontSize: 44, autoFit: "shrinkText" });
edit(19, "We characterised the boundary", "The evaluation measured adjacent interception levels and reports the approximately 62% boundary as an interpolation.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(20, "AI-native vs rule-based", "Rule, ML and Always-BENIGN Performance on 56 Held-Out Runs", { fontSize: 38, autoFit: "shrinkText" });
edit(20, "Session-disjoint split", "The session-disjoint evaluation trained on replicates 1 to 8 and tested on replicates 9 to 12.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(21, "Why the ML arm struggled", "Telemetry Constraints Behind ARM B Performance", { fontSize: 44, autoFit: "shrinkText" });

edit(22, "Open limitations", "Documented Study Limitations", { fontSize: 48, autoFit: "shrinkText" });

edit(23, "We audited our own pipeline", "Pipeline Audit and Corrective Reruns", { fontSize: 44, autoFit: "shrinkText" });
edit(23, "Four defects found", "The audit identified four defects. Two defects had produced invalid data before the corrective reruns.", { fontSize: 18.67, autoFit: "shrinkText" });

edit(24, "Next steps", "Remaining Software and Hardware Validation", { fontSize: 44, autoFit: "shrinkText" });

edit(25, "Summary", "Validated Findings and Remaining Scope", { fontSize: 46, autoFit: "shrinkText" });

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
  referenceSha256: "7e305244113deb7734737911dff2490985394275561f31bf4f0a9ee112786956",
};

const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });
const candidatePath = path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v4_candidate.pptx");
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
  receiptPath: path.join(stagingDir, "ORAN_SPlane_PRISM_Review_v4.validation.json"),
});
process.stdout.write(JSON.stringify({ finalPath, result }, null, 2));
