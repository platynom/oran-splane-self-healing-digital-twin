import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const artifactPath = require.resolve("@oai/artifact-tool");
const { FileBlob, PresentationFile } = await import(pathToFileURL(artifactPath).href);

const ROOT = process.cwd();
const SHOW_FIRST = path.join(ROOT, "outputs", "EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED", "01_show_first");
const FINAL_SHOW = path.join(SHOW_FIRST, "01_FINAL_PRESENTATION.pptx");
const WORKFLOW = path.join(SHOW_FIRST, "11_COMPLETE_WORKFLOW_AND_DATASET_REQUIREMENTS.pptx");
const OUT_PRESENTATIONS = path.join(ROOT, "outputs", "presentations", "O-RAN_AI_Native_Self_Healing_Final_Expert_Review_COMBINED.pptx");
const OUT_SHOW = FINAL_SHOW;
const TMP = path.join(os.tmpdir(), "codex-presentations", "oran-combined-final");
const PREVIEW = path.join(TMP, "workflow-slide-previews");

await fs.mkdir(PREVIEW, { recursive: true });
await fs.mkdir(path.dirname(OUT_PRESENTATIONS), { recursive: true });

const finalDeck = await PresentationFile.importPptx(await FileBlob.load(FINAL_SHOW));
const workflowDeck = await PresentationFile.importPptx(await FileBlob.load(WORKFLOW));

const finalCount = finalDeck.slides.items.length;
const workflowCount = workflowDeck.slides.items.length;

for (const [i, workflowSlide] of workflowDeck.slides.items.entries()) {
  const png = await workflowDeck.export({ slide: workflowSlide, format: "png", scale: 2 });
  const bytes = new Uint8Array(await png.arrayBuffer());
  const imgPath = path.join(PREVIEW, `workflow-${String(i + 1).padStart(2, "0")}.png`);
  await fs.writeFile(imgPath, bytes);

  const s = finalDeck.slides.add();
  s.background.fill = "white";
  s.images.add({
    blob: bytes,
    contentType: "image/png",
    alt: `Workflow and dataset requirements slide ${i + 1}`,
    fit: "cover",
    position: { left: 0, top: 0, width: 1280, height: 720 },
  });
}

const combined = await PresentationFile.exportPptx(finalDeck);
await combined.save(OUT_PRESENTATIONS);
await combined.save(OUT_SHOW);

console.log(JSON.stringify({
  source_final_slides: finalCount,
  appended_workflow_slides: workflowCount,
  combined_slides: finalDeck.slides.items.length,
  OUT_PRESENTATIONS,
  OUT_SHOW,
  PREVIEW,
}, null, 2));
