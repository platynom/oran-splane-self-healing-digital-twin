"""COVERAGE_REPORT.md built entirely from full_coverage_inventory.jsonl. No value typed by hand."""
from __future__ import annotations
import json, os
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COV = HERE / "coverage"
rows = [json.loads(l) for l in (COV / "full_coverage_inventory.jsonl").read_text(
    encoding="utf-8", errors="replace").splitlines() if l.strip()]


def root_of(p: str) -> str:
    for r in ("dataset", "02_PREVIOUS_Work",
              "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data", "outputs"):
        if p.startswith(r + "/") or p == r:
            return r
    return "(other)"


by_root = Counter(root_of(r["path"]) for r in rows)
by_ext = Counter(r.get("extension", "?") for r in rows)
by_type = Counter(r.get("type", "?") for r in rows)
parsed_ok = Counter()
for r in rows:
    ok = bool(r.get("parse", {}).get("parsed")) or r.get("type") in ("model_checkpoint",)
    parsed_ok[(r.get("type"), ok)] += 1

# duplicates
groups = defaultdict(list)
for r in rows:
    h = r.get("sha256")
    if h and not h.startswith("NOT_HASHED"):
        groups[h].append(r["path"])
dups = {h: sorted(v) for h, v in groups.items() if len(v) > 1}

# manifest coverage gap
man = json.loads((HERE / "manifest.json").read_text())
listed = set()
for row in man["sources"]:
    for x in row:
        s = str(x)
        if ("/" in s or "\\" in s) and not s.isdigit():
            listed.add(s.replace("\\", "/"))
DATA_EXT = {".csv", ".tsv", ".pcap", ".pcapng", ".pth"}
gap = [r for r in rows if root_of(r["path"]) == "dataset"
       and r.get("extension") in DATA_EXT and r["path"] not in listed]

pth = [r for r in rows if r.get("type") == "model_checkpoint"]
unread = [r for r in rows if r.get("type") in ("UNREADABLE", "UNREADABLE_DIRECTORY")
          or (r.get("parse", {}).get("parsed") is False and r.get("type") not in ("OPAQUE", "model_checkpoint"))]

s = ["# Repository-wide software read coverage", "",
     f"Date 2026-09-13. Source of every number below: `coverage/full_coverage_inventory.jsonl` "
     f"({len(rows)} records). Built by `build_coverage_report.py`; no value typed by hand.",
     "", "Model checkpoints were **never unpickled** - only their ZIP central directory was read. "
     "Python files were **never executed** - only parsed with `ast`.", "",
     "## 1. Files opened, per root", "", "| Root | Files |", "|---|---|"]
for k, v in sorted(by_root.items()):
    s.append(f"| `{k}` | {v} |")
s += ["", "## 2. By handler type", "", "| Type | Files | Parsed successfully |", "|---|---|---|"]
for t in sorted(by_type):
    s.append(f"| {t} | {by_type[t]} | {parsed_ok[(t, True)]} |")
s += ["", "## 3. Duplicate groups (the leakage map)", "",
      f"{len(dups)} sha256 values occur on more than one path, covering "
      f"{sum(len(v) for v in dups.values())} files.", ""]
known = [v for v in dups.values() if any("announce_session_1.pcap" in x for x in v)]
s.append("Correctness check on this code: the two Announce session captures are expected to collide. "
         + ("They appear in the map as " + json.dumps(known[0]) + "." if known
            else "**They do NOT appear - this duplicate map is not trustworthy.**"))
s += ["", "Largest groups:", "", "| sha256 (first 16) | Files | Paths |", "|---|---|---|"]
for h, v in sorted(dups.items(), key=lambda x: -len(x[1]))[:15]:
    s.append(f"| `{h[:16]}` | {len(v)} | " + "<br>".join(f"`{x}`" for x in v[:6])
             + (f"<br>…and {len(v)-6} more" if len(v) > 6 else "") + " |")
s += ["", "## 4. Coverage gap: data files under `dataset/` not in the 45-source manifest", "",
      f"{len(gap)} data files (csv, tsv, pcap, pcapng, pth) are present but not manifested.", "",
      "| Path | Type | Records / rows |", "|---|---|---|"]
for r in sorted(gap, key=lambda r: r["path"])[:40]:
    pa = r.get("parse", {})
    n = pa.get("rows", pa.get("records", pa.get("entry_count", "-")))
    s.append(f"| `{r['path']}` | {r['type']} | {n} |")
if len(gap) > 40:
    s.append(f"| …and {len(gap)-40} more | | |")
s += ["", "## 5. Model checkpoint inventory", "",
      f"{len(pth)} `.pth` files. **Training-data provenance for these checkpoints is not established "
      f"by this inventory.** Reading a checkpoint's archive listing says what tensors it holds, not "
      f"what data produced them.", "", "| Path | Zip archive | Entries | Uncompressed bytes |", "|---|---|---|---|"]
for r in sorted(pth, key=lambda r: r["path"])[:25]:
    pa = r.get("parse", {})
    s.append(f"| `{r['path']}` | {pa.get('torch_zip_archive')} | {pa.get('entry_count','-')} | "
             f"{pa.get('total_uncompressed_bytes','-')} |")
if len(pth) > 25:
    s.append(f"| …and {len(pth)-25} more, all recorded in the JSONL | | | |")
s += ["", "## 6. Unreadable or unparsed", ""]
if unread:
    s += ["| Path | Type | Reason |", "|---|---|---|"]
    for r in unread[:30]:
        s.append(f"| `{r['path']}` | {r.get('type')} | {r.get('parse',{}).get('reason','')[:120]} |")
    if len(unread) > 30:
        s.append(f"| …and {len(unread)-30} more | | |")
else:
    s.append("None. Every file opened either parsed or was recorded as OPAQUE with size and hash.")
s += ["", "## 7. What this does and does not close", "",
      "Closes: every file in the four roots has now been opened by a tool and inventoried, and the "
      "duplicate map covers the whole repository rather than one directory.", "",
      "Does not close: an inventory is not a dependency trace. Knowing a checkpoint's tensor names "
      "does not establish which captures trained it. Criterion 2 stays BLOCKED_EXTERNAL for the "
      "provenance question; what this removes is the excuse that the files were never read.", ""]
(HERE / "COVERAGE_REPORT.md").write_text("\n".join(s) + "\n", encoding="utf-8")
summary = {"records": len(rows), "by_root": dict(by_root), "duplicate_groups": len(dups),
           "duplicate_files": sum(len(v) for v in dups.values()),
           "manifest_gap_data_files": len(gap), "model_checkpoints": len(pth),
           "unreadable_or_unparsed": len(unread),
           "announce_session_duplicate_detected": bool(known)}
(COV / "coverage_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
