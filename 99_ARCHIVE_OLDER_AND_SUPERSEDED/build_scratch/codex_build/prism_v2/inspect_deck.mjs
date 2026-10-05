import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const sourcePath = "C:/Users/Admin/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/ORAN_SPlane_PRISM_Review_1.pptx";
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));
const search = process.argv[2] || undefined;
const snapshot = await presentation.inspect({
  kind: "deck,slide,textbox,shape,table,image,notes,layout",
  search,
  include: "id,slide,name,title,bbox,text,textPreview,rows,cols,isPlaceholder,placeholders",
  maxChars: 120000,
});
process.stdout.write(snapshot.ndjson);
