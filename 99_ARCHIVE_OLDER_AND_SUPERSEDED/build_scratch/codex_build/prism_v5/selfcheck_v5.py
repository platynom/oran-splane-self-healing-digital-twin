from __future__ import annotations

import difflib
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(r"C:\Users\Admin\Documents\AI-Native Self-Healing O-RAN Network using a Digital Twin")
V4 = ROOT / "deliverables" / "ORAN_SPlane_PRISM_Review_v4.pptx"
V5 = ROOT / "deliverables" / "ORAN_SPlane_PRISM_Review_v5.pptx"
OUT = ROOT / ".codex_build" / "prism_v5"
NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def natural_key(name: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", name)]


def extract(path: Path):
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)],
            key=natural_key,
        )
        notes = sorted(
            [n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)],
            key=natural_key,
        )

        def text_of(name: str) -> str:
            root = ET.fromstring(z.read(name))
            return "\n".join((node.text or "") for node in root.iter(NS_A + "t"))

        slide_text = [text_of(n) for n in slides]
        note_text = [text_of(n) for n in notes]
        while len(note_text) < len(slide_text):
            note_text.append("")
        return slide_text, note_text


v4_text, v4_notes = extract(V4)
v5_text, v5_notes = extract(V5)

md = []
for i, (text, notes) in enumerate(zip(v5_text, v5_notes), start=1):
    md += [f"# Slide {i}", "", "## Text", "", text, "", "## Notes", "", notes, ""]
(OUT / "deck_v5_text_and_notes.md").write_text("\n".join(md), encoding="utf-8")

removed = [
    "PROJECT HIT: OPEN FRONTHAUL S-PLANE",
    "PTP / SyncE timing evidence captured on brUP and brDN",
    "approximately 62% boundary",
    "~62%",
    "because of a single known failure",
    "entire reason specificity is 0.783 rather than 1.000",
    "Every milestone except the paper/IP draft is now closed",
    "WORKLET M5: DECISION ENGINE (COMPLETED)",
    "WORKLET M5: SAFE ABSTENTION LOGIC (COMPLETED)",
    "WORKLET M3: FAULT INJECTION (COMPLETED)",
    "36 “replicates” were one capture copied 12 times",
    "WORKLET STATUS: VALIDATED S-PLANE SUB-SCOPE",
]
added = [
    "60.54% threshold crossing",
    "47/48 = 0.979",
    "12 false ATTACK calls",
    "one UNKNOWN",
    "window-level ROC-AUC 0.604 across 1,923",
    "Prediction before service disruption was not attempted",
    "No corrective action was executed or measured",
    "The digital twin was not exercised in this campaign",
    "No MTTR, recovery-time, availability or downtime figure was measured here",
    "T-SPLANE-05",
    "timePropertiesDS §8.2.4",
]
all_v5 = "\n".join(v5_text + v5_notes)

assertions = []
assertions.append(("slide count", len(v5_text) == 27, f"{len(v5_text)}"))
for s in removed:
    assertions.append((f"removed: {s}", s not in all_v5, "absent" if s not in all_v5 else "PRESENT"))
for s in added:
    assertions.append((f"added: {s}", s in all_v5, "present" if s in all_v5 else "MISSING"))

preserved = [
    "168", "14", "12", "51/56", "24/56", "20/56", "0.911", "0.429", "0.357",
    "0.969", "0.156", "0.800", "0.950", "0.893", "0.839", "0.268", "0.262",
    "0.208", "48/168", "36 C runs", "0.783", "1.000", "0.875",
]
all_v4 = "\n".join(v4_text + v4_notes)
for s in preserved:
    assertions.append((f"preserved verified number: {s}", s in all_v4 and s in all_v5, "present in v4 and v5"))

diff_lines = []
for old_i in range(25):
    old = (v4_text[old_i] + "\n[NOTES]\n" + v4_notes[old_i]).splitlines()
    new = (v5_text[old_i] + "\n[NOTES]\n" + v5_notes[old_i]).splitlines()
    if old != new:
        diff_lines += [f"## Slide {old_i + 1}"] + list(difflib.unified_diff(old, new, lineterm="")) + [""]
old = (v4_text[25] + "\n[NOTES]\n" + v4_notes[25]).splitlines()
new = (v5_text[26] + "\n[NOTES]\n" + v5_notes[26]).splitlines()
diff_lines += ["## V4 slide 26 -> V5 slide 27"] + list(difflib.unified_diff(old, new, lineterm="")) + [""]
diff_lines += ["## New V5 slide 26", v5_text[25], "[NOTES]", v5_notes[25], ""]
(OUT / "v4_v5_text_notes.diff.md").write_text("\n".join(diff_lines), encoding="utf-8")

result = {
    "slide_count_v4": len(v4_text),
    "slide_count_v5": len(v5_text),
    "assertions": [{"check": a, "pass": b, "detail": c} for a, b, c in assertions],
    "all_assertions_pass": all(b for _, b, _ in assertions),
    "v4_sha256": hashlib.sha256(V4.read_bytes()).hexdigest(),
    "v5_sha256": hashlib.sha256(V5.read_bytes()).hexdigest(),
}
(OUT / "selfcheck_assertions.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
