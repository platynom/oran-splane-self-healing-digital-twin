import fs from "node:fs";
import path from "node:path";
import pptxgen from "../node_modules/.pnpm/pptxgenjs@4.0.1/node_modules/pptxgenjs/dist/pptxgen.cjs.js";

const root = process.cwd();
const baseImageDir = path.join(root, "outputs", "raghu_dataset_conclusion_base_images");
const out = path.join(root, "AI_Native_Self_Healing_with_Raghu_dataset_conclusion.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.subject = "AI-Native Self-Healing O-RAN deck with dataset conclusion";
pptx.title = "AI-Native Self-Healing O-RAN Network using Digital Twin";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });

const W = 13.333;
const H = 7.5;
const colors = {
  navy: "0B1324",
  panel: "111C33",
  panel2: "182642",
  cyan: "00C7E6",
  blue: "3178C6",
  green: "10B981",
  orange: "F59E0B",
  white: "FFFFFF",
  muted: "CBD5E1",
  dim: "94A3B8",
};

function addExistingSlide(imgPath) {
  const slide = pptx.addSlide();
  slide.background = { color: "FFFFFF" };
  slide.addImage({ path: imgPath, x: 0, y: 0, w: W, h: H });
}

function addTitle(slide, eyebrow, title, subtitle) {
  slide.background = { color: colors.navy };
  slide.addText(eyebrow, {
    x: 0.65, y: 0.45, w: 11.8, h: 0.25,
    fontFace: "Aptos", fontSize: 11, bold: true, color: colors.cyan,
    margin: 0,
  });
  slide.addText(title, {
    x: 0.65, y: 0.82, w: 11.8, h: 0.62,
    fontFace: "Aptos Display", fontSize: 27, bold: true, color: colors.white,
    fit: "shrink", margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.65, y: 1.5, w: 11.9, h: 0.42,
      fontFace: "Aptos", fontSize: 14, color: colors.muted,
      fit: "shrink", margin: 0,
    });
  }
}

function addFooter(slide, idx) {
  slide.addText(`Dataset conclusion ${idx}/5`, {
    x: 10.85, y: 7.05, w: 1.8, h: 0.18,
    fontFace: "Aptos", fontSize: 8, color: colors.dim,
    align: "right", margin: 0,
  });
}

function addBullets(slide, items, x, y, w, h, opts = {}) {
  slide.addText(items.map((text) => ({ text, options: { bullet: { type: "bullet" } } })), {
    x, y, w, h,
    fontFace: "Aptos",
    fontSize: opts.fontSize ?? 14,
    color: opts.color ?? colors.muted,
    breakLine: false,
    fit: "shrink",
    valign: "top",
    margin: 0.08,
    paraSpaceAfterPt: opts.paraSpaceAfterPt ?? 8,
    bullet: { indent: 14 },
  });
}

function addCard(slide, title, body, x, y, w, h, accent = colors.cyan) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: colors.panel },
    line: { color: "24324F", transparency: 10 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.06, h,
    fill: { color: accent },
    line: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.22, y: y + 0.18, w: w - 0.38, h: 0.25,
    fontFace: "Aptos", fontSize: 13, bold: true, color: colors.white,
    margin: 0,
  });
  slide.addText(body, {
    x: x + 0.22, y: y + 0.52, w: w - 0.38, h: h - 0.62,
    fontFace: "Aptos", fontSize: 11.5, color: colors.muted,
    fit: "shrink",
    margin: 0,
    breakLine: false,
  });
}

function addTag(slide, text, x, y, w, color) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.34,
    rectRadius: 0.08,
    fill: { color, transparency: 5 },
    line: { color, transparency: 0 },
  });
  slide.addText(text, {
    x: x + 0.08, y: y + 0.08, w: w - 0.16, h: 0.15,
    fontFace: "Aptos", fontSize: 8.5, bold: true,
    color: colors.white, align: "center", margin: 0,
  });
}

function addDatasetMotivation() {
  const slide = pptx.addSlide();
  addTitle(
    slide,
    "Conclusion: dataset requirement",
    "Why the dataset request matters",
    "FlexRIC proves the RIC/KPM/xApp flow; stronger validation needs richer, labelled O-RAN/5G telemetry."
  );
  addCard(slide, "Current prototype already validates", "FlexRIC KPM ingestion, controlled fault injection, anomaly detection, RCA, healing recommendations, benchmarking, and digital twin replay.", 0.75, 2.15, 3.95, 2.0, colors.cyan);
  addCard(slide, "What is still missing for stronger claims", "Production-grade evidence needs context, timing, fault truth, service impact, and post-healing outcomes, not KPI values alone.", 4.95, 2.15, 3.95, 2.0, colors.orange);
  addCard(slide, "Why this improves the project", "It lets us measure accuracy, root-cause quality, recovery performance, service impact, and model generalization across cells and services.", 9.15, 2.15, 3.4, 2.0, colors.green);
  slide.addText("Core conclusion", {
    x: 0.78, y: 4.7, w: 2.0, h: 0.28,
    fontSize: 12, bold: true, color: colors.cyan, margin: 0,
  });
  slide.addText("A smaller well-labelled dataset is more useful than a huge unlabelled dataset; ideally, we need both KPI volume and clean timestamped labels.", {
    x: 0.78, y: 5.08, w: 11.6, h: 0.7,
    fontSize: 20, bold: true, color: colors.white,
    fit: "shrink", margin: 0,
  });
  addFooter(slide, 1);
}

function addPrioritySources() {
  const slide = pptx.addSlide();
  addTitle(slide, "Dataset request summary", "Priority data sources", "Requested data should strengthen RAN, Core, RIC, transport, and cloud-native fault coverage.");
  addCard(slide, "Important", "O-RAN testbed data with RAN/Core/RIC and timestamped fault labels\nO-CU / O-DU / O-RU telemetry for architecture-level KPI visibility\nOperator-style anonymized KPI logs\nControlled fault-injection experiment logs", 0.72, 2.0, 3.85, 3.72, colors.cyan);
  addCard(slide, "Very useful", "OAI or srsRAN gNB/nrUE setup logs\nRF simulator or SDR-based experiment logs\n5G Core, UPF, transport, and backhaul telemetry\nPublic or internal Open RAN experimental datasets", 4.74, 2.0, 3.85, 3.72, colors.green);
  addCard(slide, "Supporting", "FlexRIC / Near-RT RIC logs for E2/KPM/xApp integration proof\nKubernetes and O-Cloud telemetry for edge CPU, pod, container, and node-pressure faults\nRaw logs are acceptable if parsed KPI files are not available", 8.76, 2.0, 3.85, 3.72, colors.orange);
  addTag(slide, "Best source = labelled testbed or anonymized operator data", 3.9, 6.28, 5.55, colors.blue);
  addFooter(slide, 2);
}

function addSchemaSlide() {
  const slide = pptx.addSlide();
  addTitle(slide, "Required dataset structure", "Each row should be a timestamped KPI window", "The model needs to see how metrics evolve before, during, and after a fault.");
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.75, y: 2.0, w: 11.85, h: 0.75,
    rectRadius: 0.08,
    fill: { color: colors.panel2 },
    line: { color: "2B3B5C" },
  });
  slide.addText("timestamp + site/cell/sector + CU/DU/RU + UE or aggregate + slice/service + KPI window", {
    x: 1.05, y: 2.24, w: 11.2, h: 0.25,
    fontSize: 17, bold: true, color: colors.white,
    align: "center", margin: 0,
  });
  addCard(slide, "Identifiers and context", "timestamp, site_id, cell_id, sector_id, gNB/CU/DU/RU IDs, UE hash, slice_id, 5QI/QCI, service_class, scenario_id, experiment_id, mobility_state, traffic_profile", 0.75, 3.15, 3.85, 2.35, colors.cyan);
  addCard(slide, "KPI groups requested", "Radio/PHY/RF, beamforming, MAC/RLC/scheduler, PDCP/SDAP/RRC/mobility, transport/backhaul/fronthaul, 5G Core, O-Cloud/Kubernetes, RIC/xApp/policy logs", 4.75, 3.15, 3.85, 2.35, colors.green);
  addCard(slide, "Service classes", "eMBB for throughput, URLLC for latency, mMTC for density, FWA for capacity and coverage, V2X for mobility and safety-sensitive behavior", 8.75, 3.15, 3.85, 2.35, colors.orange);
  slide.addText("Without context, the model may detect an anomaly but cannot reliably prove where it happened, why it happened, or which service was affected.", {
    x: 1.0, y: 6.1, w: 11.4, h: 0.32,
    fontSize: 13.5, color: colors.muted, italic: true,
    align: "center", margin: 0,
  });
  addFooter(slide, 3);
}

function addLabelsSlide() {
  const slide = pptx.addSlide();
  addTitle(slide, "Ground truth requirement", "Fault labels and healing outcomes are the answer key", "Labels convert anomaly detection into measurable RCA, prediction, and self-healing validation.");
  addCard(slide, "Fault / event label table", "start_time, end_time, affected site/cell/slice/service, fault_type, severity, injected-or-real flag, expected symptoms, expected RCA, expected healing action, label source, label confidence", 0.75, 2.0, 5.75, 2.65, colors.cyan);
  addCard(slide, "Healing / action outcome table", "action_id, timestamp, fault_event_id, affected cell/slice, action_type, manual-or-automated flag, expected effect, actual effect, success, rollback, recovery time, post-action KPI state", 6.85, 2.0, 5.75, 2.65, colors.green);
  slide.addText("Fault classes of interest", {
    x: 0.78, y: 5.15, w: 2.4, h: 0.25,
    fontSize: 12, bold: true, color: colors.cyan, margin: 0,
  });
  addBullets(slide, [
    "normal, cell_congestion, backhaul_degradation, packet_loss_degradation, radio_link_degradation, handover_instability",
    "spectrum_interference, timing_drift, fronthaul_degradation, core_session_degradation, UPF user-plane degradation",
    "edge_overload, O-Cloud resource pressure, beam_misalignment, antenna/RF degradation, PTP sync degradation, xApp policy conflict",
  ], 0.95, 5.55, 11.6, 1.0, { fontSize: 12.2, paraSpaceAfterPt: 5 });
  addFooter(slide, 4);
}

function addScalePrivacySlide() {
  const slide = pptx.addSlide();
  addTitle(slide, "Validation scale and practical constraints", "What makes the dataset usable", "The dataset can be real, lab-generated, emulated, anonymized, or controlled fault-injection based.");
  addCard(slide, "Minimum useful", "1-2 hours\n1-3 cells\n1-2 service classes\n10k-100k KPI rows\n5-10 labelled fault events", 0.72, 2.0, 2.45, 2.55, colors.cyan);
  addCard(slide, "Research-grade", "24-72 hours\n3-10 cells\n3-5 service classes\n1M-10M KPI rows\n50-100 labelled events", 3.35, 2.0, 2.45, 2.55, colors.green);
  addCard(slide, "Industry-grade", "2-4 weeks\n10-50 cells\nall 5 service classes\n50M-500M KPI rows\n500+ labelled events", 5.98, 2.0, 2.45, 2.55, colors.orange);
  addCard(slide, "Production validation", "30-90 days\n50+ cells\n100M-1B+ KPI rows\n1000+ labelled events\n50-1000 labels per fault class depending on claim strength", 8.61, 2.0, 3.0, 2.55, colors.blue);
  addCard(slide, "Preferred formats", "CSV for small exports, Parquet for large telemetry, JSONL for logs and decision streams, SQLite/PostgreSQL/ClickHouse dumps where available, PCAP/raw logs if parsed KPI files are not available.", 0.72, 5.05, 5.35, 1.15, colors.cyan);
  addCard(slide, "Privacy and fallback", "Sensitive subscriber/operator fields can be hashed or anonymized. Even partial data is useful: KPM logs, cell/UE KPI CSVs, RIC/xApp logs, Core/UPF/backhaul logs, tickets, or controlled traces.", 6.28, 5.05, 5.35, 1.15, colors.green);
  addTag(slide, "Final ask: share available data, format, access limits, and restrictions; parser/training pipeline can adapt.", 1.75, 6.62, 9.85, colors.blue);
  addFooter(slide, 5);
}

const baseImages = fs
  .readdirSync(baseImageDir)
  .filter((file) => file.endsWith(".png"))
  .sort()
  .map((file) => path.join(baseImageDir, file));

for (const img of baseImages) addExistingSlide(img);
addDatasetMotivation();
addPrioritySources();
addSchemaSlide();
addLabelsSlide();
addScalePrivacySlide();

await pptx.writeFile({ fileName: out });
console.log(JSON.stringify({ out, baseSlides: baseImages.length, addedSlides: 5, totalSlides: baseImages.length + 5 }, null, 2));
