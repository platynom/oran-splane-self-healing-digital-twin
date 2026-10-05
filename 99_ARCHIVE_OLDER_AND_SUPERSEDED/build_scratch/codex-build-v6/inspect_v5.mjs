import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = new URL("../deliverables/ORAN_SPlane_PRISM_Review_v5.pptx", import.meta.url);
const presentation = await PresentationFile.importPptx(await FileBlob.load(fileURLToPath(source)));
const snapshot = await presentation.inspect({
  kind: "deck,slide,textbox,shape,image,table,chart,notes,layout",
  include: "id,slide,name,title,text,textPreview,bbox,bboxUnit,isPlaceholder,placeholders",
  maxChars: 50000,
});
await fs.writeFile(new URL("./v5-inspect.ndjson", import.meta.url), snapshot.ndjson);
const montage = await presentation.export({ format: "png", montage: true, scale: 0.7 });
await fs.writeFile(new URL("./v5-montage.png", import.meta.url), new Uint8Array(await montage.arrayBuffer()));
const slideCount = presentation.slides.items.length;
for (let i = 0; i < slideCount; i += 1) {
  const slide = presentation.slides.getItem(i);
  const png = await slide.export({ format: "png", scale: 1 });
  await fs.writeFile(new URL(`./v5-slide-${String(i + 1).padStart(2, "0")}.png`, import.meta.url), new Uint8Array(await png.arrayBuffer()));
}
console.log(`slides=${slideCount}`);
