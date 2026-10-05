import fs from "node:fs/promises";
import fssync from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PROJECT = path.resolve(HERE, "..", "..");
const DATASET = path.join(PROJECT, "dataset");
const OUTPUT = path.join(HERE, "ORAN_Dataset_Encyclopedia.xlsx");
const PREVIEWS = path.join(HERE, "previews");

const C = {
  navy: "#102A43",
  teal: "#0F766E",
  cyan: "#D9F3F0",
  blue: "#DCEAF7",
  pale: "#F3F7FA",
  text: "#243B53",
  muted: "#627D98",
  white: "#FFFFFF",
  line: "#BCCCDC",
  green: "#DCFCE7",
  amber: "#FEF3C7",
  red: "#FEE2E2",
  violet: "#EDE9FE",
};

function norm(p) { return p.split(path.sep).join("/"); }
function mb(n) { return Number((n / 1048576).toFixed(3)); }

async function walk(dir) {
  const out = [];
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walk(full));
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function parseCsvRecords(text, maxRecords = 3) {
  const records = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length && records.length < maxRecords; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ',') { row.push(field); field = ""; }
    else if (ch === '\n') {
      row.push(field.replace(/\r$/, "")); field = "";
      records.push(row); row = [];
    } else field += ch;
  }
  if (records.length < maxRecords && (field.length || row.length)) {
    row.push(field.replace(/\r$/, "")); records.push(row);
  }
  return records;
}

async function fileMeta(full) {
  const stat = await fs.stat(full);
  const ext = path.extname(full).toLowerCase();
  const hash = crypto.createHash("sha256");
  let newlines = 0, lastByte = null;
  await new Promise((resolve, reject) => {
    const stream = fssync.createReadStream(full);
    stream.on("data", chunk => {
      hash.update(chunk);
      for (let i = 0; i < chunk.length; i++) if (chunk[i] === 10) newlines++;
      if (chunk.length) lastByte = chunk[chunk.length - 1];
    });
    stream.on("end", resolve); stream.on("error", reject);
  });
  let headers = [], sample = [];
  if (ext === ".csv") {
    const handle = await fs.open(full, "r");
    const buffer = Buffer.alloc(Math.min(stat.size, 1024 * 1024));
    const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0);
    await handle.close();
    const records = parseCsvRecords(buffer.subarray(0, bytesRead).toString("utf8").replace(/^\uFEFF/, ""), 2);
    headers = records[0] || [];
    sample = records[1] || [];
  }
  const physicalLines = newlines + (stat.size > 0 && lastByte !== 10 ? 1 : 0);
  return { bytes: stat.size, sha256: hash.digest("hex"), rows: ext === ".csv" ? Math.max(0, physicalLines - 1) : null, headers, sample };
}

function schemaId(headers) {
  const h = headers.join("|");
  const known = new Map([
    ["Source|Destination|Length|SequenceID|MessageType|Time Interval|Label", "S01"],
    ["Source|Destination|Length|SequenceID|MessageType|Label", "S02"],
    ["Time|Source|Destination|Protocol|Length|SequenceID|MessageType", "S03"],
    ["Source|Destination|Length|SequenceID|MessageType|TimeInterval|Label", "S04"],
    ["No.|Time|Source|Destination|Protocol|Length|Info", "S05"],
    ["Source|Destination|Length|Sequence|MessageType|Label", "S06"],
    ["Source|Destination|Length|Sequence|MessageType|TimeInterval|Label", "S07"],
    ["App name|No.|Time|Source|Destination|Protocol|Length|Info", "S08"],
    ["model|accuracy|precision_macro|recall_macro|f1_macro|roc_auc_h1|confusion_matrix", "S09"],
    ["pcap|status|samples|offset_abs_max_ns|path_delay_mean_ns|error", "S10"],
    ["scenario|status|windows|detail", "S11"],
  ]);
  if (known.has(h)) return known.get(h);
  if (headers.length === 44 && headers.includes("window_start_s")) return "S12";
  if (headers.length === 35 && headers.includes("attack_family")) return "S13";
  if (headers.length === 38 && headers.includes("telemetry_valid")) return "S14";
  if (headers.length === 27 && headers.includes("capture_id")) return "S15";
  if (headers.length === 16 && headers.includes("measured_offset_ns")) return "S16";
  if (headers.length === 13 && headers.includes("protective_2of3")) return "S17";
  if (headers.length === 7 && /^\d/.test(headers[0] || "")) return "S18";
  return "S99";
}

const SCHEMA_INFO = {
  S01: ["Labeled PTP packet features", "One processed PTP packet used for supervised learning; includes relative inter-arrival time and benign/attack label.", "Processed real packet data", "Use for packet-level model training/evaluation; split by capture, not random rows."],
  S02: ["Labeled packet features without time", "One processed PTP packet after removing the time-interval feature.", "Historical processed real data", "Archived ablation datasets; do not combine blindly with S01."],
  S03: ["Raw PTP packet export", "One decoded PTPv2 packet exported from a capture.", "Raw real packet data", "Primary packet evidence before feature encoding and labels."],
  S04: ["Labeled packet features (TimeInterval alias)", "One processed PTP packet; same conceptual schema as S01 with a legacy column spelling.", "Historical processed real data", "Normalize TimeInterval to Time Interval before combining."],
  S05: ["Wireshark packet export", "One packet row exported with Wireshark display fields.", "Raw real packet data", "Useful for manual packet review; Info must be parsed before ML use."],
  S06: ["Heuristic features without time", "One labeled packet using legacy Sequence naming and no timing interval.", "Historical processed real data", "Legacy heuristic experiments only."],
  S07: ["Heuristic packet features", "One labeled packet using legacy Sequence and TimeInterval names.", "Historical processed real data", "Legacy heuristic experiments; normalize aliases first."],
  S08: ["Application-tagged Wireshark export", "One packet row with an application/process label plus Wireshark fields.", "Raw real packet data", "Useful for correlating packet behavior with application traffic."],
  S09: ["Discriminator model metrics", "One trained model and its aggregate classification metrics.", "Derived evaluation output", "Compare candidate models; confusion matrix is the class-count evidence."],
  S10: ["PCAP ingestion summary", "One capture file and the result of converting it to telemetry.", "Derived validation output", "Find incomplete or failed captures before analysis."],
  S11: ["Netem scenario run status", "One network-impairment scenario and its completion status.", "Derived validation output", "Confirms which experiments produced usable windows."],
  S12: ["Window-level model feature matrix", "One overlapping 0.4-second feature window supplied to anomaly/classification models.", "Derived synthetic features", "Primary system-level detection input; keep run boundaries isolated."],
  S13: ["Synthetic S-plane telemetry", "One simulated S-plane observation at time t, before window aggregation.", "Synthetic raw-like telemetry", "Reproducible scenario development and controlled ablations."],
  S14: ["Validity-aware live/netem telemetry", "One real linuxptp/netem telemetry observation with explicit missing/stale-data validity.", "Derived real software telemetry", "Canonical live schema; invalid telemetry must route to UNKNOWN."],
  S15: ["Capture-isolated TIMESAFE telemetry", "One telemetry observation derived from a named real TIMESAFE capture and attack family.", "Derived real testbed telemetry", "Canonical real evaluation schema; capture_id is the holdout boundary."],
  S16: ["Legacy compact telemetry", "One telemetry observation using the earlier 16-column canonical schema.", "Derived real software telemetry", "Historical/compatibility data; lacks explicit validity and BMCA fields."],
  S17: ["Live governed-loop decisions", "One model/twin/healing decision for a feature window.", "Derived decision output", "Audits label, action, reason, latency, and persistence protection."],
  S18: ["Malformed/headerless packet file", "The first data record was interpreted as the header, so column names are numeric values.", "Historical malformed data", "Do not use until a correct seven-column header is restored."],
  S99: ["Unclassified tabular schema", "A CSV schema that did not match the documented patterns.", "Unknown", "Review manually before use."],
};

function classify(rel, ext) {
  const r = rel.toLowerCase();
  const archive = r.includes("/archive/") || r.includes("/archive\\");
  const git = r.includes("/.git/") || r.startsWith("timesafe/s-plane_security_repo/.git/");
  const cache = r.includes("__pycache__") || ext === ".pyc";
  let fileClass = "Supporting file", provenance = "Project-generated", stage = "Supporting", importance = "Reference";
  if (git) return { fileClass: "Git repository metadata", provenance: "Upstream repository", stage: "Metadata", importance: "Exclude" };
  if (cache) return { fileClass: "Python runtime cache", provenance: "Generated cache", stage: "Cache", importance: "Exclude" };
  if (ext === ".csv") { fileClass = "Tabular dataset"; stage = "Dataset"; importance = archive ? "Historical" : "Important"; }
  else if (ext === ".pcap") { fileClass = "Raw packet capture"; stage = "Raw evidence"; importance = archive ? "Historical" : "Critical"; }
  else if (ext === ".pth") { fileClass = "PyTorch model checkpoint"; stage = "Model artifact"; importance = archive ? "Historical" : "Supporting"; }
  else if (ext === ".json") { fileClass = r.includes("training_log") ? "Model training log" : "JSON summary"; stage = "Derived evidence"; importance = archive ? "Historical" : "Supporting"; }
  else if (ext === ".png") { fileClass = "Evaluation image"; stage = "Derived evidence"; importance = archive ? "Historical" : "Supporting"; }
  else if (ext === ".py") { fileClass = "Python source"; stage = "Reproduction code"; importance = archive ? "Historical" : "Supporting"; }
  else if ([".md", ".txt", ".yaml"].includes(ext)) { fileClass = "Documentation/configuration"; stage = "Documentation"; importance = archive ? "Historical" : "Reference"; }
  else if ([".idx", ".pack", ".promisor", ".rev", ".sample"].includes(ext) || !ext) { fileClass = "Repository/support artifact"; stage = "Metadata"; importance = "Exclude"; }

  if (r.startsWith("synthetic s-plane/")) provenance = "Synthetic experiment";
  else if (r.startsWith("netem/") && (r.includes("netem_") || r.includes("fail_closed") || ext === ".pcap")) provenance = ext === ".pcap" ? "Real software packet capture" : "Derived from real software experiment";
  else if (r.startsWith("netem/") && r.includes("splane_")) provenance = "Synthetic duplicate";
  else if (r.startsWith("timesafe/") && [".csv", ".pcap", ".txt"].includes(ext)) provenance = archive ? "Historical real testbed derivative" : (ext === ".pcap" ? "Real external testbed capture" : "Derived/decoded real external data");
  else if (r.startsWith("timesafe/s-plane_security_repo/")) provenance = "Upstream TIMESAFE repository";

  if (r.includes("timesafe_sessions/") || r.includes("timesafe_multi_raw/") || r.startsWith("netem/") || r.startsWith("synthetic s-plane/")) {
    if (importance === "Important") importance = "Critical";
  }
  return { fileClass, provenance, stage, importance };
}

function filePurpose(rel, ext, sid) {
  const r = rel.toLowerCase();
  const name = path.basename(rel).toLowerCase();
  if (ext === ".csv") {
    if (name === "splane_telemetry.csv") return "Time-series telemetry used to construct window features; Synthetic copy under Netem is packaging duplication.";
    if (name === "splane_windows.csv") return "Window-level feature matrix used by the detector and controlled scenario evaluation.";
    if (name.includes("netem_telemetry")) return "Decoded linuxptp/netem timing telemetry for baseline, PDV, loss, or holdover validation.";
    if (name.includes("live_decisions")) return "Governed-loop decisions demonstrating behavior before or after fail-closed handling.";
    if (name.includes("labels")) return "Packet-level labels aligned with the companion PCAP session.";
    if (r.includes("timesafe_sessions/")) return "Capture-isolated real TIMESAFE telemetry segment for leakage-resistant evaluation.";
    if (name.includes("labeled") || name.includes("dataset")) return "Labeled PTP packet features for model development or historical comparison.";
    if (name.includes("metrics")) return "Aggregate model performance metrics.";
    if (name.includes("status") || name.includes("summary")) return "Experiment/capture status and quality-control summary.";
    return `${SCHEMA_INFO[sid]?.[0] || "CSV dataset"}; see Schema Guide and Column Dictionary.`;
  }
  if (ext === ".pcap") return "Original packet-level capture; immutable source evidence for decoding and relabeling.";
  if (ext === ".pth") return "Serialized trained neural-network weights; load only with the matching architecture and feature order.";
  if (ext === ".json") return name.includes("training_log") ? "Training history/metrics for one model experiment." : "Machine-readable experiment summary.";
  if (ext === ".png") return "Rendered confusion matrix or evaluation figure; presentation evidence, not training input.";
  if (ext === ".py") return "Source code for collection, transformation, training, inference, or evaluation.";
  if (ext === ".md" || ext === ".txt") return "Human-readable documentation, logs, or traffic-generator output.";
  if (ext === ".yaml") return "Configuration parameters for the upstream pipeline.";
  return "Support or repository-management artifact; not a dataset input.";
}

const DEF = {
  "Source": ["Encoded source endpoint or source MAC address.", "identifier", "categorical identifier", "0/1 or MAC address", "Separates trusted clock traffic from a possible attacker/source."],
  "Destination": ["Encoded destination endpoint or destination MAC address.", "identifier", "categorical identifier", "2 or multicast MAC", "Shows which clock/domain received the packet."],
  "Length": ["Captured packet length.", "bytes", "integer", "typically 58, 60, 68", "Abnormal lengths can reveal unexpected message forms."],
  "SequenceID": ["IEEE 1588 PTP sequence identifier.", "counter", "integer", "0–65535", "Regressions or repeats support replay/reordering detection."],
  "Sequence": ["Legacy name for the PTP sequence identifier.", "counter", "integer", "0–65535", "Normalize to SequenceID before combining schemas."],
  "MessageType": ["PTP message type encoded as an integer.", "PTPv2 code", "integer/category", "for example 0 Sync, 8 Follow_Up, 11 Announce", "Distinguishes Announce/BMCA attacks from Sync replay."],
  "Time Interval": ["Elapsed time since the preceding packet after preprocessing.", "seconds", "floating point", "0 or small positive value", "Burst/replay timing patterns appear in inter-arrival changes."],
  "TimeInterval": ["Legacy spelling of Time Interval.", "seconds", "floating point", "0 or small positive value", "Normalize the name before combining datasets."],
  "Label": ["Packet-level ground-truth class.", "class", "integer/category", "0 benign, 1 malicious", "Target variable for supervised packet classification."],
  "Time": ["Capture timestamp, usually relative seconds in exported packet data.", "seconds", "floating point/text", "0.000000 or capture time", "Aligns packets with attack intervals and other telemetry."],
  "Protocol": ["Decoded protocol name.", "category", "text", "PTPv2", "Filters the capture to relevant synchronization traffic."],
  "No.": ["Packet ordinal assigned by the export tool.", "row number", "integer", "1, 2, 3…", "Traceability back to Wireshark order; not a model feature."],
  "Info": ["Human-readable packet summary produced by Wireshark.", "text", "text", "message details", "Useful for manual forensic review; parse before ML use."],
  "App name": ["Application/process label associated with captured traffic.", "category", "text", "application name", "Correlates PTP behavior with application traffic."],
  "t_s": ["Elapsed experiment time for this observation.", "seconds", "floating point", "non-negative", "Orders telemetry and aligns events across sources."],
  "scenario": ["Experiment condition or fault/attack scenario name.", "category", "text", "healthy, netem_loss, ptp_replay…", "Primary grouping key for cause-to-effect analysis."],
  "offset_ns": ["Clock offset from the selected master/reference.", "nanoseconds", "floating point", "signed value", "Large magnitude or steps indicate synchronization disturbance."],
  "measured_offset_ns": ["Observed clock offset before any model-side interpretation.", "nanoseconds", "floating point", "signed value", "Preserves the measured value separately from derived/simulated state."],
  "path_delay_ns": ["Estimated master-to-slave network path delay.", "nanoseconds", "floating point", "non-negative", "Rises under congestion/asymmetry and localizes transport problems."],
  "offset_valid": ["Whether offset_ns is a current valid measurement.", "boolean", "boolean", "True/False", "False bypasses ML and triggers conservative UNKNOWN handling."],
  "path_delay_valid": ["Whether path_delay_ns is a current valid measurement.", "boolean", "boolean", "True/False", "Prevents missing delay from being interpreted as zero delay."],
  "telemetry_valid": ["Overall provenance/completeness validity of the sample or window.", "boolean", "boolean", "True/False", "Central fail-closed safety gate."],
  "stale_s": ["Age of the last trustworthy measurement.", "seconds", "floating point", "0 for fresh; positive when stale", "Detects pmc serving plausible but outdated values during outage."],
  "pdv_ns": ["Packet-delay variation relative to the local path-delay baseline.", "nanoseconds", "floating point", "signed residual", "Localizes jitter/congestion in the fronthaul network."],
  "freq_error_ppb": ["Estimated oscillator frequency error.", "parts per billion", "floating point", "signed value", "Reveals clock drift and holdover instability."],
  "oscillator_holdover_nominal_ppb": ["Declared nominal oscillator drift while in holdover.", "parts per billion", "floating point", "configured constant", "Reference used to judge physically plausible holdover."],
  "oscillator_holdover_tolerance_ppb": ["Allowed drift around the holdover nominal value.", "parts per billion", "floating point", "configured positive value", "Violations distinguish benign holdover from abnormal behavior."],
  "oscillator_disciplined_tolerance_ppb": ["Allowed frequency error while the clock is disciplined.", "parts per billion", "floating point", "configured positive value", "Flags inconsistency between declared sync state and oscillator behavior."],
  "gnss_reference_ns": ["GNSS reference-clock error/offset.", "nanoseconds", "floating point", "signed value", "Supports GNSS-versus-PTP cross-checking."],
  "ptp_reference_ns": ["PTP/LLS-C reference-clock error/offset.", "nanoseconds", "floating point", "signed value", "Cross-checks the local GNSS and peer reference."],
  "peer_reference_ns": ["Independent peer reference-clock error/offset.", "nanoseconds", "floating point", "signed value", "Provides another comparison source when enabled."],
  "source_agreement_tolerance_ns": ["Maximum normal disagreement allowed between timing references.", "nanoseconds", "floating point", "configured positive threshold", "Turns reference disagreement into a testable anomaly condition."],
  "synce_ql": ["Observed SyncE quality level encoded numerically.", "quality-level code", "integer/category", "implementation-specific", "Degradation points to the Ethernet clock distribution chain."],
  "ptp_seq_id": ["Canonical PTP sequence identifier in telemetry.", "counter", "integer", "0–65535", "Used to compute regressions and continuity features."],
  "ptp_msg_type": ["Canonical PTP message type name.", "category", "text", "Sync, Follow_Up, Announce…", "Separates BMCA, replay, and traffic-mix symptoms."],
  "msg_rate_hz": ["Trailing PTP message arrival rate.", "messages/second", "floating point", "non-negative", "Extreme rises suggest flood/DoS; compare with legitimate bursts."],
  "grandmaster_identity": ["Identity of the selected PTP grandmaster.", "identifier", "text", "clock identity", "Unexpected transitions suggest takeover; excluded from model as a raw fingerprint."],
  "grandmaster_priority1": ["PTP BMCA priority1 advertised by the grandmaster.", "PTP field", "integer", "0–255, lower wins", "Forged improvement can win BMCA election."],
  "grandmaster_clock_class": ["Advertised quality/class of the grandmaster clock.", "PTP field", "integer", "0–255, lower generally better", "Implausible improvement supports Announce spoof detection."],
  "grandmaster_clock_accuracy": ["Advertised clock-accuracy code.", "PTP field", "integer/code", "IEEE 1588 code", "Checks plausibility of a candidate grandmaster."],
  "offset_scaled_log_variance": ["Advertised PTP clock variance field.", "PTP field", "integer", "0–65535", "Part of BMCA quality plausibility."],
  "grandmaster_priority2": ["PTP BMCA tie-break priority2.", "PTP field", "integer", "0–255", "Helps explain grandmaster selection changes."],
  "steps_removed": ["Number of PTP boundary-clock hops from the grandmaster.", "hops", "integer", "0 or positive", "Unexpected changes may indicate re-parenting/topology manipulation."],
  "time_source": ["PTP time-source code advertised by the grandmaster.", "PTP field", "integer/code", "for example 32/160", "Indicates claimed timing origin; must not be trusted alone."],
  "gnss_sync_status": ["Receiver-reported GNSS synchronization state.", "category", "text", "SYNCHRONIZED, HOLDOVER, BOOTING…", "Useful only when corroborated because the receiver can be deceived."],
  "satellites_tracked": ["Number of GNSS satellites currently tracked.", "satellites", "integer", "-1 unavailable or non-negative", "Drops support jamming/antenna fault localization."],
  "gnss_available": ["Whether GNSS timing is available.", "boolean", "boolean", "True/False", "Loss moves the system toward holdover and GNSS-path diagnosis."],
  "holdover": ["Whether the oscillator is free-running in holdover.", "boolean", "boolean", "True/False", "Separates expected holdover from disciplined operation."],
  "attack_flag": ["Simulator/source indicator that an attack is active.", "boolean", "boolean", "True/False", "Ground truth for controlled attack timing; not an inference feature."],
  "fault_flag": ["Simulator/source indicator that a non-malicious fault is active.", "boolean", "boolean", "True/False", "Separates operational faults from attacks."],
  "run_id": ["Independent experiment/run identifier.", "identifier", "integer/text", "0, 1, 2…", "Keep runs isolated between training and evaluation."],
  "label": ["System/window class label.", "class", "text/category", "healthy, H0, H1, UNKNOWN, PENDING", "H0 is benign/degraded; H1 is harmful; UNKNOWN is fail-safe uncertainty."],
  "capture_id": ["Identity of the source packet-capture session.", "identifier", "text", "announce_session_1…", "Mandatory grouping boundary to prevent real-data leakage."],
  "attack_family": ["Attack family associated with the observation.", "category", "text", "announce, replay, dos, gnss_jam…", "Supports leave-one-family-out generalization tests."],
  "window_start_s": ["Start time of the aggregation window.", "seconds", "floating point", "non-negative", "Locates a decision in the experiment timeline."],
  "window_end_s": ["End time of the aggregation window.", "seconds", "floating point", "greater than start", "Defines the evidence interval summarized by the row."],
  "is_anomalous": ["Ground-truth anomaly indicator for the simulated window.", "boolean", "boolean/integer", "0/1", "Evaluation target; not used as an input feature."],
  "valid_sample_rate": ["Rate of valid telemetry samples inside the window.", "samples/second", "floating point", "non-negative", "Low coverage signals acquisition failure."],
  "valid_sample_fraction": ["Fraction of window samples passing validity checks.", "proportion", "floating point", "0–1", "Fails closed when insufficient valid evidence exists."],
  "offset_mean": ["Mean clock offset inside the window.", "nanoseconds", "floating point", "signed", "Captures sustained synchronization bias."],
  "offset_std": ["Standard deviation of clock offset inside the window.", "nanoseconds", "floating point", "non-negative", "Captures instability/jitter."],
  "offset_abs_max": ["Largest absolute clock offset inside the window.", "nanoseconds", "floating point", "non-negative", "Captures worst timing excursion."],
  "path_delay_mean": ["Mean network path delay inside the window.", "nanoseconds", "floating point", "non-negative", "Locates congestion/asymmetry effects."],
  "pdv_std": ["Standard deviation of packet-delay variation in the window.", "nanoseconds", "floating point", "non-negative", "Primary congestion/jitter feature."],
  "seq_regressions": ["Count of backward/repeated PTP sequence movements.", "count/window", "integer", "0 or positive", "Strong replay/reordering indicator."],
  "msg_irregularity": ["Deviation of the PTP message pattern from expected regularity.", "score", "floating point", "0 or positive", "Supports malformed/replay detection."],
  "synce_ql_max": ["Worst/highest encoded SyncE quality level in the window.", "quality-level code", "integer", "implementation-specific", "Localizes SyncE chain degradation."],
  "gnss_loss_rate": ["Fraction of samples without GNSS availability.", "proportion", "floating point", "0–1", "High values localize GNSS loss/jamming."],
  "holdover_rate": ["Fraction of samples in holdover.", "proportion", "floating point", "0–1", "Measures duration/severity of reference loss."],
  "msg_rate_mean": ["Mean PTP message rate in the window.", "messages/second", "floating point", "non-negative", "Flood detection; compare with traffic_burst H0 control."],
  "msg_rate_std": ["Variability of PTP message rate in the window.", "messages/second", "floating point", "non-negative", "Separates stable rate from bursts/floods."],
  "gm_identity_changes": ["Count of grandmaster identity transitions in the window.", "count/window", "integer", "0 or positive", "Signals takeover or planned failover."],
  "gm_identity_churn": ["Normalized rate of grandmaster identity changes.", "score", "floating point", "0–1 or positive", "High churn suggests unstable/malicious BMCA behavior."],
  "clock_class_changes": ["Count of grandmaster clock-class changes.", "count/window", "integer", "0 or positive", "Supports BMCA transition analysis."],
  "clock_class_improve_jump": ["Magnitude of an abrupt advertised clock-class improvement.", "PTP class units", "floating point", "0 or positive", "Forged superior clocks often advertise sudden improvement."],
  "priority1_changes": ["Count of BMCA priority1 changes.", "count/window", "integer", "0 or positive", "Supports Announce spoof versus stable GM diagnosis."],
  "steps_removed_changes": ["Count of changes in boundary-clock hop count.", "count/window", "integer", "0 or positive", "Shows re-parenting/topology transitions."],
  "steps_removed_min": ["Minimum advertised PTP hop count in the window.", "hops", "integer", "0 or positive", "Unexpectedly low hops can make a forged GM appear superior."],
  "gnss_status_changes": ["Count of GNSS receiver status transitions.", "count/window", "integer", "0 or positive", "Shows loss/recovery/holdover transitions."],
  "antenna_fault_rate": ["Fraction of samples reporting a GNSS antenna fault.", "proportion", "floating point", "0–1", "Localizes failure to antenna/RF chain when observable."],
  "satellites_drop_max": ["Largest drop in tracked-satellite count within the window.", "satellites", "floating point", "0 or positive", "Sudden drop supports jamming/antenna obstruction."],
  "satellites_mean": ["Average tracked-satellite count in the window.", "satellites", "floating point", "-1 unavailable or non-negative", "Low average supports GNSS availability diagnosis."],
  "holdover_entry_count": ["Number of transitions into holdover.", "count/window", "integer", "0 or positive", "Separates stable state from repeated timing-source loss."],
  "drift_vs_declared_state_residual": ["Mismatch between measured oscillator drift and the drift expected for the declared state.", "parts per billion", "floating point", "non-negative magnitude", "Detects inconsistent GNSS/holdover behavior."],
  "holdover_spec_violation_rate": ["Fraction of samples outside the configured holdover envelope.", "proportion", "floating point", "0–1", "Separates benign holdover from harmful instability."],
  "status_behaviour_disagreement": ["Disagreement between reported timing status and measured physical behavior.", "score", "floating point", "0–1 or positive", "Flags receiver reports that should not be trusted alone."],
  "offset_step_vs_drift_ratio": ["Ratio of abrupt offset step to gradual oscillator drift.", "ratio", "floating point", "non-negative", "Large ratios indicate injected steps/replay rather than natural drift."],
  "max_pairwise_source_disagreement_ns": ["Largest disagreement between any two timing references.", "nanoseconds", "floating point", "non-negative", "Detects loss of multi-source consensus."],
  "disagreement_growth_rate": ["Rate at which reference disagreement increases.", "nanoseconds/second", "floating point", "signed/non-negative", "Localizes a diverging timing source."],
  "n_sources_outside_tolerance": ["Number of timing sources outside the configured agreement tolerance.", "count", "integer", "0–number of sources", "Measures breadth of disagreement."],
  "minority_source_isolation_score": ["Degree to which one timing source is isolated from the others.", "score", "floating point", "0–1 or positive", "Identifies a single-source compromise when peers agree."],
  "gnss_consensus_residual_ns": ["GNSS deviation from the multi-source consensus.", "nanoseconds", "floating point", "signed/magnitude", "High residual points toward GNSS as the outlier."],
  "ptp_consensus_residual_ns": ["PTP reference deviation from the multi-source consensus.", "nanoseconds", "floating point", "signed/magnitude", "High residual points toward PTP transport/master."],
  "peer_consensus_residual_ns": ["Peer-clock deviation from the multi-source consensus.", "nanoseconds", "floating point", "signed/magnitude", "High residual points toward the peer reference."],
  "wall_time": ["UTC wall-clock time when the decision was emitted.", "timestamp", "datetime text", "ISO 8601", "Audits real operational ordering."],
  "offset_abs_max_ns": ["Largest absolute offset for the decision/capture summary.", "nanoseconds", "floating point", "non-negative or blank", "Shows worst timing excursion; blank is meaningful under invalid telemetry."],
  "pdv_std_ns": ["Packet-delay-variation standard deviation for the decision window.", "nanoseconds", "floating point", "non-negative or blank", "Localizes transport jitter; blank under missing data."],
  "action": ["Recovery recommendation selected by the governed loop.", "category", "text", "safe_default, failover…", "States what the system would do; recommendation-only in live validation."],
  "reason": ["Human-readable explanation for the decision/action.", "text", "text", "decision rationale", "Provides auditability and distinguishes invalid telemetry from model alarms."],
  "decision_latency_s": ["Compute time for model/twin decision.", "seconds", "floating point", "non-negative", "Verifies decision computation performance."],
  "end_to_end_latency_s": ["Elapsed time from window readiness to final recommendation.", "seconds", "floating point", "non-negative", "Tests the two-second recovery requirement."],
  "within_budget": ["Whether end-to-end latency met the configured deadline.", "boolean", "boolean", "True/False", "Direct deadline compliance indicator."],
  "protective_1of1": ["Whether the raw one-window policy would respond protectively.", "boolean", "boolean", "True/False", "Shows sensitivity before temporal persistence."],
  "protective_2of3": ["Whether two of the last three windows support a protective response.", "boolean", "boolean", "True/False", "Deployed persistence result that suppresses isolated alarms."],
  "model": ["Model identifier/name.", "identifier", "text", "RF, model filename…", "Links metrics to the evaluated model."],
  "accuracy": ["Fraction of all predictions classified correctly.", "proportion", "floating point", "0–1", "Useful overview but can hide class imbalance."],
  "precision_macro": ["Unweighted mean precision across classes.", "proportion", "floating point", "0–1", "Measures false-positive burden across both classes."],
  "recall_macro": ["Unweighted mean recall across classes.", "proportion", "floating point", "0–1", "Measures missed events across both classes."],
  "f1_macro": ["Unweighted mean harmonic precision/recall score.", "proportion", "floating point", "0–1", "Balanced classifier comparison metric."],
  "roc_auc_h1": ["Area under ROC curve treating H1 as the positive class.", "proportion", "floating point", "0–1", "Ranks H1 discrimination independent of one threshold."],
  "confusion_matrix": ["Counts of true/false predictions arranged by class.", "counts", "serialized array", "[[TN,FP],[FN,TP]]", "Shows exact error types hidden by aggregate metrics."],
  "pcap": ["Packet-capture filename processed by the pipeline.", "identifier", "text", "*.pcap", "Traceability to immutable source evidence."],
  "status": ["Processing or scenario completion state.", "category", "text", "ok, failed, partial…", "Quality-control gate before including an experiment."],
  "samples": ["Number of telemetry samples recovered from the capture.", "count", "integer", "0 or positive", "Very small counts limit confidence and window construction."],
  "path_delay_mean_ns": ["Mean path delay recovered from the capture.", "nanoseconds", "floating point", "non-negative", "Summarizes transport behavior."],
  "error": ["Error message when capture processing failed or was partial.", "text", "text", "blank or error detail", "Explains why evidence is missing."],
  "windows": ["Number of valid analysis windows produced by the scenario.", "count", "integer", "0 or positive", "Confirms usable evaluation volume."],
  "detail": ["Additional scenario execution notes.", "text", "text", "status detail", "Provides context for incomplete runs."],
};

function inferType(value) {
  if (value == null || value === "") return "blank/unknown";
  if (/^(true|false)$/i.test(String(value))) return "boolean";
  if (!Number.isNaN(Number(value))) return Number.isInteger(Number(value)) ? "integer" : "floating point";
  return "text/category";
}

function defFor(name, sid, index) {
  if (sid === "S18") return [
    `Malformed observed header at column ${index + 1}; this value is actually from the first data row, not a field name.`,
    "unknown", "unknown", "numeric value from lost first row", "Restore the expected seven-column packet header before analysis."
  ];
  return DEF[name] || [`Field named ${name} in the source schema.`, "unspecified", "unknown", "source-defined", "Review upstream code before model use."];
}

function canonicalRank(rel) {
  const r = rel.toLowerCase();
  let score = 0;
  if (r.includes("/.git/") || r.includes("__pycache__")) score += 1000;
  if (r.includes("/archive/")) score += 500;
  if (r.startsWith("netem/splane_")) score += 100;
  if (r.startsWith("synthetic s-plane/")) score -= 30;
  if (r.startsWith("timesafe/timesafe_")) score -= 30;
  score += rel.split("/").length * 3 + rel.length / 1000;
  return score;
}

function folderPurpose(rel) {
  const r = rel.toLowerCase();
  if (!rel) return "Root of the extracted evidence package.";
  if (r === "netem") return "Linux/linuxptp network-emulation captures, telemetry, decisions, and validation summaries.";
  if (r === "synthetic s-plane") return "Controlled simulator telemetry and window features for attacks, faults, and benign confounders.";
  if (r === "timesafe") return "Real TIMESAFE PTP-security captures, processed sessions, and the upstream research repository.";
  if (r.includes("timesafe_multi_raw")) return "Canonical raw real captures paired with packet labels.";
  if (r.includes("timesafe_sessions")) return "Canonical capture-isolated real telemetry segments for evaluation.";
  if (r.includes("datacollectionptp")) return "Upstream raw PTP data collection and packet exports.";
  if (r.includes("production_environment")) return "Upstream deployment/test outputs and selected production model artifacts.";
  if (r.includes("testbed")) return "Scripts and models used to collect/test traffic on DU, RU, and attacker nodes.";
  if (r.includes("digital_twin")) return "Selected model checkpoints placed for digital-twin/production experiments.";
  if (r.includes("du_model")) return "DU-side model training outputs, logs, and architectures.";
  if (r.includes("ru_model")) return "RU-side model training outputs, logs, and architectures.";
  if (r.includes("archive")) return "Historical or superseded datasets/models retained for provenance; not canonical evidence.";
  if (r.includes(".git")) return "Git version-control internals; exclude from dataset analysis.";
  if (r.includes("__pycache__")) return "Generated Python bytecode cache; exclude from dataset analysis.";
  if (r.includes("models")) return "Serialized trained model checkpoints.";
  if (r.includes("scripts")) return "Collection, attack-generation, processing, or evaluation scripts.";
  if (r.includes("pipeline")) return "Detection pipeline code, outputs, or supporting artifacts.";
  return "Supporting subfolder in the packaged project/research repository; inspect File Inventory for exact contents.";
}

function folderRole(rel) {
  const p = folderPurpose(rel).toLowerCase();
  if (p.includes("exclude") || p.includes("internals") || p.includes("cache")) return "Exclude/metadata";
  if (p.includes("historical")) return "Historical archive";
  if (p.includes("raw") || p.includes("capture")) return "Raw evidence";
  if (p.includes("telemetry") || p.includes("dataset")) return "Dataset/processed evidence";
  if (p.includes("model")) return "Models/evaluation";
  if (p.includes("script") || p.includes("code")) return "Reproduction code";
  return "Supporting";
}

function importantCatalog() {
  return [
    ["Netem", "Linux/netem PCAP set", "netem_baseline.pcap; netem_pdv.pcap; netem_loss.pcap; netem_holdover.pcap", "Real software experiment", "One packet in a raw capture", "Baseline vs PDV, packet loss, and holdover transport behavior", "Use as immutable source evidence; decode rather than edit."],
    ["Netem", "Validity-aware netem telemetry", "netem_telemetry*.csv", "Derived real software telemetry", "One decoded linuxptp/PTP observation", "Where delay, loss, offset, or missing telemetry appears", "Primary real netem analysis input; S14/S16."],
    ["Netem", "Fail-closed before/after decisions", "fail_closed_live_decisions*.csv", "Derived live decision output", "One governed-loop decision window", "Demonstrates telemetry validity gate defect and correction", "Compare before and after; do not train on decisions."],
    ["Netem", "Model and run summaries", "model/discriminator_metrics.csv; netem_run_status.csv; netem_partial_capture_summary.csv", "Derived validation output", "One model, scenario, or capture summary", "Confirms performance and usable experiment coverage", "Quality-control/reporting evidence."],
    ["Netem", "Packaged synthetic copy", "splane_telemetry.csv; splane_windows.csv", "Synthetic duplicate", "One telemetry sample or feature window", "Same controlled scenarios as Synthetic S-Plane", "Use the Synthetic S-Plane copy as canonical; do not double count."],
    ["Synthetic S-Plane", "Synthetic telemetry", "splane_telemetry.csv", "Synthetic experiment", "One simulated observation at time t", "Controlled PTP, GNSS, SyncE, congestion, and benign scenarios", "Use for reproducible scenario development and ablation."],
    ["Synthetic S-Plane", "Window feature matrix", "splane_windows.csv", "Derived synthetic features", "One overlapping 0.4-second model window", "28 shipped features plus disabled research cross-source features", "Use run-aware splits; labels are evaluation truth."],
    ["timesafe", "Production Announce capture", "timesafe_prod_successful_announce_attack_ptp.pcap/.csv", "Real external testbed", "One raw/decoded PTP packet", "Successful Announce/BMCA takeover evidence", "Canonical raw real Announce evidence."],
    ["timesafe", "Production labeled packet features", "timesafe_prod_successful_announce_attack_labeled.csv", "Derived real external data", "One labeled PTP packet", "Packet-level benign/malicious learning data", "Keep source capture isolated during evaluation."],
    ["timesafe", "Compact attack/benign telemetry split", "timesafe_split_attack_telemetry.csv; timesafe_split_benign_telemetry.csv", "Derived real external data", "One canonical telemetry observation", "Early compact TIMESAFE calibration inputs", "Legacy S16; prefer capture-isolated sessions for final evaluation."],
    ["timesafe/timesafe_multi_raw", "Five raw session pairs", "*.pcap + *_labels.csv", "Real external testbed", "One packet capture plus packet label rows", "Announce, Sync/Follow-Up, and Single-Step attack families", "Canonical raw multi-session real evidence."],
    ["timesafe/timesafe_sessions", "Capture-isolated telemetry segments", "*.csv", "Derived real external data", "One telemetry observation from a named capture", "Leakage-resistant H0/H1 evaluation across attack families", "Canonical real model evaluation; group by capture_id."],
    ["timesafe/s-plane_security_repo/DataCollectionPTP", "Upstream packet exports", "*.csv and RU traffic logs", "Real upstream testbed", "One decoded packet or traffic-log entry", "Source experiments used in historical dataset construction", "Reference/provenance; normalize schemas before reuse."],
    ["timesafe/s-plane_security_repo/Archive", "Historical combined datasets", "Combinations, Datasets, DatasetNoTimestamp", "Historical real derivatives", "One labeled packet", "Earlier preprocessing/model experiments", "Do not merge with canonical data without lineage and deduplication."],
    ["timesafe/s-plane_security_repo/DU_model and RU_model", "Training logs, checkpoints, confusion matrices", "*.json, *.pth, *.png", "Derived upstream models", "One experiment log/model/image file", "Reproduces prior packet classifiers", "Not raw data; architecture/feature order must match."],
    ["timesafe/s-plane_security_repo/Production_Environment", "Production/test outputs", "CSV, PTH, PNG, scripts", "Derived upstream deployment evidence", "Depends on file type", "Prior deployment and digital-twin model experiments", "Supporting comparison only; many archived duplicates."],
    ["timesafe/s-plane_security_repo/Testbed", "Collection and attack scripts", "Python scripts and model checkpoints", "Upstream reproduction code", "Not row-based", "Explains how DU, RU, attacker, and background traffic were operated", "Use to understand data generation; do not treat code/models as observations."],
  ];
}

const LABELS = [
  ["System label", "healthy", "Normal baseline before an event", "Neither H0 nor H1 event is active", "Keep as matched baseline."],
  ["System label", "H0", "Benign but degraded/confounding condition", "Congestion, planned GM failover, traffic burst, SyncE degradation, benign holdover", "Do not automatically quarantine."],
  ["System label", "H1", "Harmful attack or fault requiring protection", "PTP spoof/replay/DoS or harmful GNSS jam/spoof", "Trigger governed protective evaluation."],
  ["System label", "UNKNOWN", "Evidence is novel, missing, stale, or invalid", "Classifier certainty is unsafe", "Route to safe_default and audit reason."],
  ["System label", "PENDING", "Protective candidate awaiting persistence", "First positive in a 2-of-3 sequence", "Wait for persistence unless immediate safety policy overrides."],
  ["Packet Label", "0", "Benign packet", "Source packet not labeled malicious", "Supervised packet target."],
  ["Packet Label", "1", "Malicious packet", "Source packet belongs to attack activity", "Supervised packet target."],
  ["Scenario", "ptp_spoof", "Forged superior grandmaster/Announce behavior", "H1", "Inspect BMCA and Announce origin."],
  ["Scenario", "ptp_replay", "Replayed or reordered timing messages", "H1", "Inspect sequence continuity and Sync/Follow-Up stream."],
  ["Scenario", "ptp_dos_flood", "Excessive PTP message rate", "H1", "Inspect/rate-limit S-plane ingress."],
  ["Scenario", "gnss_jam", "GNSS loss with harmful holdover behavior", "H1", "Inspect antenna/RF/receiver and independent clock."],
  ["Scenario", "gnss_spoof", "Manipulated GNSS time reference", "H1", "Requires independent/authenticated corroboration."],
  ["Scenario", "pdv_congestion", "High packet-delay variation", "H0", "Inspect fronthaul queues/QoS."],
  ["Scenario", "traffic_burst", "Legitimate traffic/message-rate burst", "H0", "Confounder for DoS; avoid false quarantine."],
  ["Scenario", "planned_gm_failover", "Authorized BMCA re-parenting", "H0", "Validate maintenance/failover context."],
  ["Scenario", "synce_degrade", "SyncE quality degradation", "H0", "Inspect Ethernet Equipment Clock chain."],
  ["Scenario", "gnss_loss_holdover", "Benign GNSS loss within oscillator envelope", "H0", "Monitor duration and specification compliance."],
  ["Netem", "netem_baseline", "Normal software PTP transport", "Reference", "Comparison baseline."],
  ["Netem", "netem_pdv", "Injected delay variation", "Transport impairment", "Localizes jitter/congestion."],
  ["Netem", "netem_loss", "Injected packet loss", "Transport impairment", "Localizes sparse/missing timing delivery."],
  ["Netem", "netem_holdover", "Master/reference loss and holdover", "Timing-source impairment", "Localizes reference loss and telemetry validity."],
];

const LOCALIZATION = [
  [1, "Grandmaster identity/priority/class changes plus offset step", "Announce spoof or GM takeover", "PTP BMCA at O-DU/O-RU S-plane boundary", "Quarantine unexpected GM; verify Announce source", "gm_identity_changes; clock_class_improve_jump; priority1_changes; offset_abs_max", "H1 when unauthorized; H0 if planned failover"],
  [2, "Sequence regressions/repeats without GM change", "PTP replay or reordering", "Sync/Follow-Up packet stream on fronthaul", "Block replay source; reset/revalidate sequence continuity", "seq_regressions; msg_irregularity; offset_step_vs_drift_ratio", "H1"],
  [3, "Message rate rises sharply", "PTP flood/DoS or legitimate burst", "S-plane ingress and traffic source", "Compare timing impact and traffic_burst H0 control before rate limiting", "msg_rate_mean; msg_rate_std", "H1 only with harmful behavior; otherwise H0"],
  [4, "PDV/path delay rises while GM remains stable", "Congestion, asymmetry, queueing", "Fronthaul switches, queues, QoS, scheduling", "Inspect QoS/queues; reroute or reprioritize timing packets", "pdv_std; path_delay_mean; offset_abs_max", "Usually H0 degradation"],
  [5, "Packet/capture density collapses", "Packet loss or acquisition gap", "Fronthaul link or capture path", "Inspect link loss, filters, capture completeness", "samples; valid_sample_rate; msg_rate_hz", "H0/H1 depends on cause"],
  [6, "GNSS available/satellite count drops; holdover rises", "GNSS jam, antenna fault, obstruction, or benign loss", "GNSS antenna, RF feed, receiver, local oscillator", "Switch to trusted reference and inspect RF chain", "gnss_loss_rate; satellites_drop_max; holdover_rate", "H1 if harmful/out of envelope; H0 if compliant holdover"],
  [7, "Holdover drift exceeds declared envelope", "Oscillator instability or deceptive status", "Local oscillator/timing source", "Use alternate reference; inspect oscillator health", "holdover_spec_violation_rate; drift_vs_declared_state_residual", "H1"],
  [8, "GNSS status claims healthy but behavior disagrees", "Possible GNSS spoof or receiver deception", "GNSS source; requires external corroboration", "Cross-check authenticated GNSS/independent clock", "status_behaviour_disagreement; consensus residuals", "H1 suspicion; strict unseen spoof remains unresolved"],
  [9, "SyncE quality level degrades", "Frequency-distribution degradation", "Ethernet Equipment Clock/SyncE chain", "Trace QL advertisements; select better EEC source", "synce_ql; synce_ql_max", "H0 degradation"],
  [10, "Telemetry invalid, absent, stale, NaN, or provenance-less", "Monitoring/control-plane evidence failure", "pmc collector and telemetry-validity decision gate", "Bypass ML; route to UNKNOWN/safe_default", "telemetry_valid; offset_valid; path_delay_valid; stale_s", "Protective uncertainty"],
];

function setTitle(sheet, lastCol, title, subtitle) {
  sheet.showGridLines = false;
  sheet.mergeCells(`A1:${lastCol}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}1`).format = { fill: C.navy, font: { bold: true, color: C.white, size: 16 }, verticalAlignment: "center" };
  sheet.getRange("A1").format.rowHeight = 30;
  sheet.mergeCells(`A2:${lastCol}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${lastCol}2`).format = { fill: C.blue, font: { color: C.text, italic: true, size: 10 }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange("A2").format.rowHeight = 34;
}

function addTable(sheet, startRow, headers, rows, name) {
  const start = startRow - 1;
  const matrix = [headers, ...rows];
  const range = sheet.getRangeByIndexes(start, 0, matrix.length, headers.length);
  range.values = matrix;
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  const headerRange = sheet.getRangeByIndexes(start, 0, 1, headers.length);
  headerRange.format = { fill: C.teal, font: { bold: true, color: C.white }, wrapText: true, verticalAlignment: "center" };
  headerRange.format.rowHeight = 30;
  return { range, table, start, endRow: start + matrix.length };
}

function widths(sheet, specs) {
  for (const [col, width] of Object.entries(specs)) sheet.getRange(`${col}:${col}`).format.columnWidth = width;
}

function wrapBody(sheet, range) {
  sheet.getRange(range).format.wrapText = true;
  sheet.getRange(range).format.verticalAlignment = "top";
}

const paths = await walk(DATASET);
const records = [];
for (let i = 0; i < paths.length; i++) {
  const full = paths[i];
  const rel = norm(path.relative(DATASET, full));
  const ext = path.extname(full).toLowerCase();
  const meta = await fileMeta(full);
  const sid = ext === ".csv" ? schemaId(meta.headers) : "";
  const cls = classify(rel, ext);
  records.push({ id: i + 1, full, rel, ext: ext || "[none]", top: rel.split("/")[0], name: path.basename(rel), ...meta, sid, ...cls, purpose: filePurpose(rel, ext, sid) });
}

// Exact duplicate groups and canonical representative.
const hashGroups = new Map();
for (const rec of records) {
  const key = `${rec.bytes}:${rec.sha256}`;
  if (!hashGroups.has(key)) hashGroups.set(key, []);
  hashGroups.get(key).push(rec);
}
let dupCounter = 0;
for (const group of hashGroups.values()) {
  if (group.length < 2) continue;
  dupCounter++;
  group.sort((a, b) => canonicalRank(a.rel) - canonicalRank(b.rel));
  const canonical = group[0].rel;
  group.forEach((rec, index) => {
    rec.duplicateGroup = `D${String(dupCounter).padStart(3, "0")}`;
    rec.duplicateStatus = index === 0 ? "Canonical in group" : "Exact duplicate";
    rec.canonicalFile = canonical;
  });
}
for (const rec of records) {
  rec.duplicateGroup ||= ""; rec.duplicateStatus ||= "Unique"; rec.canonicalFile ||= rec.rel;
  if (rec.duplicateStatus === "Exact duplicate" && rec.importance === "Critical") rec.importance = "Duplicate";
}

// Folder inventory, including every ancestor directory represented in the ZIP.
const folderSet = new Set([""]);
for (const rec of records) {
  const parts = rec.rel.split("/").slice(0, -1);
  for (let i = 1; i <= parts.length; i++) folderSet.add(parts.slice(0, i).join("/"));
}
const folderRows = [...folderSet].sort().map(rel => {
  const prefix = rel ? `${rel}/` : "";
  const direct = records.filter(r => norm(path.dirname(r.rel)) === (rel || ".")).length;
  const recursive = records.filter(r => !rel || r.rel.startsWith(prefix)).length;
  const bytes = records.filter(r => !rel || r.rel.startsWith(prefix)).reduce((s, r) => s + r.bytes, 0);
  return [rel ? rel.split("/").length : 0, rel || "dataset/", rel ? (rel.includes("/") ? rel.slice(0, rel.lastIndexOf("/")) : "dataset/") : "—", direct, recursive, mb(bytes), folderRole(rel), folderPurpose(rel)];
});

// Schema groups and column dictionary.
const csvRecords = records.filter(r => r.ext === ".csv");
const schemaGroups = new Map();
for (const rec of csvRecords) {
  if (!schemaGroups.has(rec.sid)) schemaGroups.set(rec.sid, []);
  schemaGroups.get(rec.sid).push(rec);
}
const schemaRows = [...schemaGroups.entries()].sort().map(([sid, rs]) => {
  const info = SCHEMA_INFO[sid];
  const representative = [...rs].sort((a, b) => canonicalRank(a.rel) - canonicalRank(b.rel))[0];
  return [sid, info[0], rs.length, representative.headers.length, rs.reduce((s, r) => s + r.rows, 0), info[2], info[1], info[3], representative.rel];
});
const dictionaryRows = [];
const exampleRows = [];
let undocumented = 0;
for (const [sid, rs] of [...schemaGroups.entries()].sort()) {
  const rep = [...rs].sort((a, b) => canonicalRank(a.rel) - canonicalRank(b.rel))[0];
  const info = SCHEMA_INFO[sid];
  for (let i = 0; i < rep.headers.length; i++) {
    const name = rep.headers[i];
    const d = defFor(name, sid, i);
    if (!DEF[name] && sid !== "S18") undocumented++;
    const sample = rep.sample[i] ?? "";
    dictionaryRows.push([sid, info[0], i + 1, sid === "S18" ? `Column ${i + 1} (observed '${name}')` : name, d[0], d[1], d[2] === "unknown" ? inferType(sample) : d[2], d[3], info[2], d[4], sample, sample === "" ? "Blank in the representative first row; consult later rows and validity fields." : `In the sample row, ${name} is ${sample}.`, rep.rel]);
  }
  const rowText = rep.headers.map((h, i) => `${h}=${rep.sample[i] ?? ""}`).join(" | ");
  exampleRows.push([sid, info[0], rep.rel, rep.rows, rowText, info[1], info[3]]);
}
if (undocumented) throw new Error(`${undocumented} legitimate columns lack definitions`);

const duplicateRows = [];
for (const group of [...hashGroups.values()].filter(g => g.length > 1).sort((a, b) => a[0].duplicateGroup.localeCompare(b[0].duplicateGroup))) {
  for (const rec of group) duplicateRows.push([rec.duplicateGroup, rec.duplicateStatus, rec.rel, rec.canonicalFile, rec.bytes, rec.sha256, rec.fileClass, rec.purpose]);
}

const workbook = Workbook.create();
const start = workbook.worksheets.add("START HERE");
const folders = workbook.worksheets.add("Folder Guide");
const catalog = workbook.worksheets.add("Dataset Catalog");
const inventory = workbook.worksheets.add("File Inventory");
const schema = workbook.worksheets.add("Schema Guide");
const dictionary = workbook.worksheets.add("Column Dictionary");
const examples = workbook.worksheets.add("Example Rows");
const labels = workbook.worksheets.add("Labels & Scenarios");
const localize = workbook.worksheets.add("Problem Localization");
const dupes = workbook.worksheets.add("Duplicates & Archives");
const usage = workbook.worksheets.add("How to Use");

// START HERE dashboard.
setTitle(start, "J", "O-RAN S-Plane Dataset Encyclopedia", "A searchable guide to every folder, file, CSV schema, column, example row, label, and problem-location rule in dataset.zip. Prepared for technical review; source data is not altered.");
start.getRange("A4:J4").merge(); start.getRange("A4").values = [["What this workbook answers"]];
start.getRange("A4:J4").format = { fill: C.teal, font: { bold: true, color: C.white, size: 12 } };
start.getRange("A5:J7").merge(); start.getRange("A5").values = [["For each important dataset: What is it? What does one row mean? What does every column mean? Is it real, synthetic, derived, historical, or duplicate? Which signal change indicates which problem and where should an operator inspect first?"]];
start.getRange("A5:J7").format = { fill: C.cyan, font: { color: C.text, size: 11 }, wrapText: true, verticalAlignment: "center" };
const cards = [
  ["A9:B9", "A10:B11", "Total files", "=COUNTA('File Inventory'!$A$6:$A$649)", "#,##0"],
  ["C9:D9", "C10:D11", "CSV datasets", "=COUNTIF('File Inventory'!$E$6:$E$649,\".csv\")", "#,##0"],
  ["E9:F9", "E10:F11", "Unique CSV schemas", "=COUNTA('Schema Guide'!$A$6:$A$23)", "#,##0"],
  ["G9:H9", "G10:H11", "Raw PCAP captures", "=COUNTIF('File Inventory'!$E$6:$E$649,\".pcap\")", "#,##0"],
  ["I9:J9", "I10:J11", "Expanded size (GiB)", "=SUM('File Inventory'!$L$6:$L$649)/1073741824", "0.000"],
];
for (const [lab, val, label, formula, numFmt] of cards) {
  start.getRange(lab).merge(); start.getRange(lab.split(":")[0]).values = [[label]];
  start.getRange(lab).format = { fill: C.navy, font: { bold: true, color: C.white }, horizontalAlignment: "center" };
  start.getRange(val).merge(); start.getRange(val.split(":")[0]).formulas = [[formula]];
  start.getRange(val).format = { fill: C.pale, font: { bold: true, color: C.teal, size: 16 }, horizontalAlignment: "center", verticalAlignment: "center", numberFormat: numFmt, borders: { preset: "outside", style: "thin", color: C.line } };
}
const nav = [
  ["Folder Guide", "Every directory and its purpose."], ["Dataset Catalog", "Important logical datasets and how one row should be read."],
  ["File Inventory", "All 644 files with provenance, stage, importance, size, schema, hash, and duplicate status."], ["Schema Guide", "The 18 unique CSV layouts and their safe use."],
  ["Column Dictionary", "Every column in every unique schema, with unit, type, values, sample, and problem significance."], ["Example Rows", "A representative row for each schema and how to interpret it."],
  ["Labels & Scenarios", "H0/H1/healthy/UNKNOWN and all major attack/degradation scenarios."], ["Problem Localization", "Signal change → probable cause → exact first inspection point → action."],
  ["Duplicates & Archives", "Exact SHA-256 duplicates and canonical file for each group."], ["How to Use", "Recommended workflow for sir, analysis, training, and reporting."],
];
start.getRange("A14:B14").merge(); start.getRange("A14").values = [["Sheet"]];
start.getRange("C14:J14").merge(); start.getRange("C14").values = [["What it contains"]];
start.getRange("A14:J14").format = { fill: C.teal, font: { bold: true, color: C.white }, verticalAlignment: "center" };
for (let i = 0; i < nav.length; i++) {
  const row = 15 + i;
  start.getRange(`A${row}:B${row}`).merge(); start.getRange(`A${row}`).values = [[nav[i][0]]];
  start.getRange(`C${row}:J${row}`).merge(); start.getRange(`C${row}`).values = [[nav[i][1]]];
  start.getRange(`A${row}:J${row}`).format = { fill: i % 2 === 0 ? "#B9E0F0" : C.white, font: { color: C.text }, borders: { bottom: { style: "thin", color: C.line } }, verticalAlignment: "center" };
}
start.getRange("A27:J27").merge(); start.getRange("A27").values = [["Critical interpretation rule"]]; start.getRange("A27:J27").format = { fill: C.red, font: { bold: true, color: "#991B1B" } };
start.getRange("A28:J30").merge(); start.getRange("A28").values = [["dataset.zip is a consolidated evidence package. It contains real TIMESAFE data, real software/netem experiments, synthetic scenarios, derived features/decisions, exact duplicates, historical archives, models, and repository metadata. Do not count duplicate files as new experiments, and do not call synthetic GNSS data real hardware evidence."]];
start.getRange("A28:J30").format = { fill: "#FFF7ED", font: { color: C.text }, wrapText: true, verticalAlignment: "center" };
widths(start, { A: 18, B: 18, C: 18, D: 18, E: 18, F: 18, G: 18, H: 18, I: 18, J: 18 });

setTitle(folders, "H", "Folder-by-Folder Guide", "Every folder in the extracted ZIP, including canonical evidence, historical archives, models, code, caches, and repository metadata.");
addTable(folders, 5, ["Level", "Folder", "Parent", "Direct Files", "Recursive Files", "Size MB", "Role", "Purpose"], folderRows, "FolderGuideTable");
folders.freezePanes.freezeRows(5); widths(folders, { A: 8, B: 52, C: 42, D: 12, E: 14, F: 13, G: 22, H: 70 }); wrapBody(folders, `A6:H${folderRows.length + 5}`);
folders.getRange(`D6:E${folderRows.length + 5}`).format.numberFormat = "#,##0";
folders.getRange(`F6:F${folderRows.length + 5}`).format.numberFormat = "#,##0.000";

setTitle(catalog, "G", "Important Dataset Catalog", "One folder and logical dataset at a time: purpose, provenance, meaning of one row, analytical role, and safe use.");
const catRows = importantCatalog();
addTable(catalog, 5, ["Folder", "Logical Dataset", "Files / Pattern", "Provenance", "Meaning of One Row", "Purpose in This Project", "Recommended Use"], catRows, "DatasetCatalogTable");
catalog.freezePanes.freezeRows(5); widths(catalog, { A: 35, B: 32, C: 45, D: 29, E: 36, F: 50, G: 50 }); wrapBody(catalog, `A6:G${catRows.length + 5}`);

setTitle(inventory, "R", "Complete File Inventory", "All files in dataset.zip. Filter by top folder, extension, provenance, importance, schema, or duplicate status. SHA-256 provides exact provenance verification.");
const invRows = records.map(r => [r.id, r.top, r.rel, r.name, r.ext, r.fileClass, r.provenance, r.stage, r.importance, r.sid, r.rows, r.bytes, mb(r.bytes), r.sha256, r.duplicateGroup, r.duplicateStatus, r.canonicalFile, r.purpose]);
addTable(inventory, 5, ["ID", "Top Folder", "Relative Path", "File Name", "Extension", "File Class", "Provenance", "Stage", "Importance", "Schema ID", "Rows / Records", "Size Bytes", "Size MB", "SHA-256", "Duplicate Group", "Duplicate Status", "Canonical File", "Purpose / Operator Meaning"], invRows, "FileInventoryTable");
inventory.freezePanes.freezeRows(5); inventory.freezePanes.freezeColumns(3);
widths(inventory, { A: 8, B: 20, C: 64, D: 38, E: 12, F: 26, G: 32, H: 22, I: 14, J: 12, K: 15, L: 16, M: 13, N: 34, O: 15, P: 20, Q: 64, R: 62 });
wrapBody(inventory, `A6:R${invRows.length + 5}`); inventory.getRange(`A6:A${invRows.length + 5}`).format.numberFormat = "#,##0";
inventory.getRange(`K6:L${invRows.length + 5}`).format.numberFormat = "#,##0";
inventory.getRange(`M6:M${invRows.length + 5}`).format.numberFormat = "#,##0.000";
inventory.getRange(`I6:I${invRows.length + 5}`).conditionalFormats.add("containsText", { text: "Critical", format: { fill: C.green, font: { color: "#166534", bold: true } } });
inventory.getRange(`I6:I${invRows.length + 5}`).conditionalFormats.add("containsText", { text: "Exclude", format: { fill: C.red, font: { color: "#991B1B" } } });
inventory.getRange(`P6:P${invRows.length + 5}`).conditionalFormats.add("containsText", { text: "Exact duplicate", format: { fill: C.amber, font: { color: "#92400E" } } });

setTitle(schema, "I", "CSV Schema Guide", "The 117 CSV files reduce to 18 distinct schemas. Explain a schema once, then use Schema Map/File Inventory to see every file that uses it.");
addTable(schema, 5, ["Schema ID", "Schema Title", "Files", "Columns", "Total Physical Data Rows", "Data Stage", "Meaning of One Row", "Safe Use / Caution", "Representative File"], schemaRows, "SchemaGuideTable");
schema.freezePanes.freezeRows(5); widths(schema, { A: 11, B: 34, C: 10, D: 10, E: 20, F: 28, G: 62, H: 58, I: 70 }); wrapBody(schema, `A6:I${schemaRows.length + 5}`); schema.getRange(`C6:E${schemaRows.length + 5}`).format.numberFormat = "#,##0";

setTitle(dictionary, "M", "Complete Column Dictionary", "Every position in every unique CSV schema: plain-language meaning, unit, type, typical values, role, problem significance, and a real sample value.");
addTable(dictionary, 5, ["Schema ID", "Schema Title", "Position", "Column", "Plain-Language Meaning", "Unit", "Data Type", "Typical Values", "Data Stage", "Why It Matters / Problem Use", "Example Value", "Example Interpretation", "Representative File"], dictionaryRows, "ColumnDictionaryTable");
dictionary.freezePanes.freezeRows(5); dictionary.freezePanes.freezeColumns(4); widths(dictionary, { A: 11, B: 32, C: 10, D: 34, E: 62, F: 22, G: 22, H: 32, I: 28, J: 66, K: 28, L: 60, M: 70 }); wrapBody(dictionary, `A6:M${dictionaryRows.length + 5}`);

setTitle(examples, "G", "Representative Example Rows", "One actual first data row per schema. Read together with Column Dictionary; identifiers and values are examples, not universal thresholds.");
addTable(examples, 5, ["Schema ID", "Schema Title", "Representative File", "Physical Data Rows", "Example Row (column=value)", "What One Row Represents", "How to Use It"], exampleRows, "ExampleRowsTable");
examples.freezePanes.freezeRows(5); widths(examples, { A: 11, B: 34, C: 64, D: 18, E: 110, F: 58, G: 58 }); wrapBody(examples, `A6:G${exampleRows.length + 5}`); examples.getRange(`D6:D${exampleRows.length + 5}`).format.numberFormat = "#,##0";

setTitle(labels, "E", "Labels and Scenario Dictionary", "Ground-truth labels, detector states, attack families, benign confounders, and netem impairment names used across the package.");
addTable(labels, 5, ["Type", "Value", "Plain Meaning", "Class / Context", "Operator Interpretation"], LABELS, "LabelsTable");
labels.freezePanes.freezeRows(5); widths(labels, { A: 18, B: 28, C: 58, D: 45, E: 60 }); wrapBody(labels, `A6:E${LABELS.length + 5}`);

setTitle(localize, "G", "Problem Localization Matrix", "Use measured signal changes to decide what likely happened, where to inspect first, and what governed response is appropriate.");
addTable(localize, 5, ["Priority", "Observed Change", "Likely Cause", "Exact First Inspection Point", "Recommended Response", "Key Columns", "Classification Guardrail"], LOCALIZATION, "LocalizationTable");
localize.freezePanes.freezeRows(5); widths(localize, { A: 10, B: 50, C: 38, D: 55, E: 58, F: 58, G: 46 }); wrapBody(localize, `A6:G${LOCALIZATION.length + 5}`);

setTitle(dupes, "H", "Exact Duplicates and Historical Material", "Files in this table share identical byte content within a duplicate group. Use the canonical file once; never count another group member as an independent experiment.");
addTable(dupes, 5, ["Duplicate Group", "Status", "File", "Canonical File", "Size Bytes", "SHA-256", "File Class", "Purpose / Caution"], duplicateRows, "DuplicateMapTable");
dupes.freezePanes.freezeRows(5); widths(dupes, { A: 16, B: 20, C: 72, D: 72, E: 16, F: 38, G: 28, H: 64 }); wrapBody(dupes, `A6:H${duplicateRows.length + 5}`); dupes.getRange(`E6:E${duplicateRows.length + 5}`).format.numberFormat = "#,##0";
dupes.getRange(`B6:B${duplicateRows.length + 5}`).conditionalFormats.add("containsText", { text: "Exact duplicate", format: { fill: C.amber, font: { color: "#92400E" } } });

setTitle(usage, "F", "How Sir Should Use This Package", "A defensible workflow for explanation, analysis, model evaluation, and reporting without leakage, duplication, or overstated real-world claims.");
const useRows = [
  [1, "Start with Dataset Catalog", "Understand each logical dataset and what one row represents.", "Do not start by opening the 1+ GiB archive CSVs."],
  [2, "Locate a file in File Inventory", "Confirm provenance, stage, importance, schema, hash, and duplicate status.", "Use Canonical File when Duplicate Status is Exact duplicate."],
  [3, "Read Schema Guide", "Understand the table layout and safe-use warning.", "S18 is malformed/headerless and must not be used as-is."],
  [4, "Read Column Dictionary", "Filter Schema ID or column name for a complete field explanation.", "Units belong to columns; blank/invalid values are not automatically zero."],
  [5, "Review Example Rows", "See one real row in column=value form.", "Example values are illustrative, not detection thresholds."],
  [6, "Separate data stages", "PCAP = raw; telemetry = decoded; windows = features; decisions = outputs.", "Never train on decision/action columns or ground-truth flags."],
  [7, "Prevent leakage", "Split TIMESAFE by capture_id and simulator data by run_id.", "Random row splitting exaggerates performance because adjacent rows/windows are correlated."],
  [8, "Remove duplicates", "Use SHA-256 duplicate groups and canonical path.", "Duplicate rows/files add no independent evidence."],
  [9, "Interpret H0 vs H1", "Use Labels & Scenarios and Problem Localization.", "Congestion, traffic burst, planned GM failover, and compliant holdover are not automatically attacks."],
  [10, "Fail closed on missing evidence", "Check telemetry_valid, offset_valid, path_delay_valid, and stale_s.", "Invalid evidence routes to UNKNOWN/safe_default before ML."],
  [11, "State evidence honestly", "TIMESAFE and netem are real packet/software evidence; GNSS/S-plane scenarios are synthetic.", "No physical O-DU/O-RU, hardware timestamp NIC, authenticated GNSS, or independent clock is proven here."],
  [12, "Recommended presentation", "Use START HERE → Dataset Catalog → one filtered Schema/Column view → Problem Localization.", "This creates a clear, application-oriented explanation for review and resume demonstration."],
];
addTable(usage, 5, ["Step", "Action", "Why", "Critical Rule"], useRows, "UsageGuideTable");
usage.freezePanes.freezeRows(5); widths(usage, { A: 10, B: 38, C: 70, D: 72, E: 12, F: 12 }); wrapBody(usage, `A6:D${useRows.length + 5}`);
usage.getRange("A20:F20").merge(); usage.getRange("A20").values = [["Recommended canonical analysis chain"]]; usage.getRange("A20:F20").format = { fill: C.teal, font: { bold: true, color: C.white } };
usage.getRange("A21:F24").merge(); usage.getRange("A21").values = [["Raw evidence (PCAP / packet export) → decoded telemetry → validity check → short feature windows → H0/H1/UNKNOWN decision → digital-twin verification → governed recovery recommendation. Preserve capture_id/run_id throughout for auditability."]]; usage.getRange("A21:F24").format = { fill: C.cyan, font: { color: C.text, size: 11 }, wrapText: true, verticalAlignment: "center" };

// Compact verification and visual previews.
await fs.mkdir(PREVIEWS, { recursive: true });
const inspect1 = await workbook.inspect({ kind: "table", range: "START HERE!A1:J30", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 10, maxChars: 8000 });
const inspect2 = await workbook.inspect({ kind: "table", range: "Column Dictionary!A1:M20", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 13, maxChars: 8000 });
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(inspect1.ndjson);
console.log(inspect2.ndjson);
console.log(errors.ndjson);

const previewSpecs = [
  ["START HERE", "A1:J30"], ["Folder Guide", "A1:H24"], ["Dataset Catalog", "A1:G23"],
  ["File Inventory", "A1:R18"], ["Schema Guide", "A1:I23"], ["Column Dictionary", "A1:M20"],
  ["Example Rows", "A1:G23"], ["Labels & Scenarios", "A1:E26"], ["Problem Localization", "A1:G16"],
  ["Duplicates & Archives", "A1:H20"], ["How to Use", "A1:F24"],
];
for (const [sheetName, range] of previewSpecs) {
  const blob = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(PREVIEWS, `${sheetName.replace(/[^A-Za-z0-9]+/g, "_")}.png`), new Uint8Array(await blob.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(OUTPUT);
console.log(JSON.stringify({ output: OUTPUT, files: records.length, csvFiles: csvRecords.length, schemas: schemaGroups.size, dictionaryRows: dictionaryRows.length, duplicateRows: duplicateRows.length, folders: folderRows.length }, null, 2));
