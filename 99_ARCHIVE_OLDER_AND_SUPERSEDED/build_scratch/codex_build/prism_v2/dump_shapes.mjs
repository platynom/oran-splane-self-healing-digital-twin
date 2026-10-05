import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const sourcePath = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/ORAN_SPlane_PRISM_Review_1.pptx";
const wanted = new Set(process.argv.slice(2).map(Number));
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const snapshot = await presentation.inspect({
  kind: "shape,textbox",
  include: "id,slide,name,bbox,text",
  maxChars: 300000,
});
for (const line of snapshot.ndjson.split(/\r?\n/)) {
  if (!line.trim()) continue;
  const record = JSON.parse(line);
  if (wanted.size === 0 || wanted.has(record.slideIndex)) process.stdout.write(JSON.stringify(record) + "\n");
}
