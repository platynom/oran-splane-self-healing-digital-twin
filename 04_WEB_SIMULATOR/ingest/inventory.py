#!/usr/bin/env python3
"""Generate docs/3D_DATA_INVENTORY.md: path, format, size, sha256 and git status of every data source the 3D explorer
needs. Re-runnable; nothing is approximated. A source that is absent from the repository is recorded as such.

  python3 ingest/inventory.py            (from 04_WEB_SIMULATOR)
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.abspath(os.path.join(HERE, "..", "docs", "3D_DATA_INVENTORY.md"))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def tracked(rel):
    r = subprocess.run(["git", "-C", REPO, "ls-files", "--error-unmatch", rel], capture_output=True)
    return r.returncode == 0

def mb(n):
    return f"{n / 1e6:.2f} MB" if n >= 1e5 else f"{n / 1e3:.1f} kB"

rows = []
def add(group, rel, fmt, note=""):
    p = os.path.join(REPO, rel)
    if os.path.isfile(p):
        rows.append((group, rel, fmt, mb(os.path.getsize(p)), sha(p), "in git" if tracked(rel) else "present, NOT in git", note))
    else:
        rows.append((group, rel, fmt, "-", "-", "ABSENT from repository", note))

RL = "03_RECOVERY_LOOP_S-PLANE"
CF = "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/gap_coverage_2026-09-20/corrected_final"
P = "outputs/empirical_software_network_pilot_v1"
B6 = "outputs/B6_two_machine_2026-10-02"
DECK = "00_LATEST_PRESENTED_DECK_AND_DELIVERABLES"

# A. 140 recovery-loop runs
add("A. 140 recovery-loop runs", f"{RL}/results/recovery_eval_runs_r13-r17.tgz", "tar.gz, 140 run dirs", "observer.jsonl, loop.jsonl, ptp4l logs, dn/up pcap.gz, nft_final.txt, context/timeline/state json")
add("A. 140 recovery-loop runs", f"{RL}/results/EVALUATION_RL.json", "json", "per-run scores; cross-check target")
add("A. 140 recovery-loop runs", f"{RL}/results/SHA256SUMS.txt", "text", "published hashes")
add("A. 140 recovery-loop runs", f"{RL}/results/recovery_dev_runs_r101.tgz", "tar.gz", "development replicate 101; never pooled with evaluation; NOT ingested")
add("A. 140 recovery-loop runs", "04_WEB_SIMULATOR/data/derived/recovery_runs.json.gz", "json.gz", "derived by ingest/extract.py; loaded into PostgreSQL")
# B. 168-run campaign
add("B. 168-run detector campaign", f"{CF}/splane_campaign_CORRECTED_2026-09-20.tgz", "tar.gz, 168 run dirs", "deep CSVs (56 columns per PTP frame), context.json, decision*.json; raw PCAPs not in archive")
add("B. 168-run detector campaign", f"{CF}/splane_campaign_CORRECTED_2026-09-20.tgz.sha256", "text", "published hash")
add("B. 168-run detector campaign", f"{CF}/EVALUATION_V4.json", "json", "cross-check target")
add("B. 168-run detector campaign", "04_WEB_SIMULATOR/data/derived/campaign_runs.json.gz", "json.gz", "verdict-level rows (already in DB on branch webapp)")
# C. B6
for f in ["DRIFT_REPORT.md", "drift_pair.json", "drift_pair.png", "PRE_REGISTRATION.md", "B6_MEASUREMENT_RECORD_2026-10-02.md",
          "run2/DRIFT_REPORT_run2.md", "run2/drift_pair_run2.json", "run2/drift_pair_run2.png", "run2/PRE_REGISTRATION_RUN2.md", "run2/B6_MEASUREMENT_RECORD_run2.md"]:
    add("C. B6 oscillator drift (two laptops)", f"{B6}/{f}", f.rsplit(".", 1)[-1], "analysis output / record")
for run, js in (("run1", f"{B6}/drift_pair.json"), ("run2", f"{B6}/run2/drift_pair_run2.json")):
    d = json.load(open(os.path.join(REPO, js)))
    for arm in ("arm_a", "arm_b"):
        a = d[arm]
        rows.append(("C. B6 oscillator drift (two laptops)", f"(raw, {run}) {a['csv']}", "csv, per-sample NTP offset", "-", f"recorded sha256 {a['csv_sha256']}", "ABSENT from repository (not in repo)", f"{a['rows_total']} rows recorded; not approximated"))
# D. 13 Sep pilot
for f in ["S11_CLOSED_LOOP_EVALUATION.json", "S11_CLOSED_LOOP_PROTOCOL.json", "S11_S12_CURRENT_REPORT.md", "S12_MEASURED_OUTCOME.json",
          "S15_INDEPENDENT_VALIDATION_EVALUATION.json", "S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json", "START_HERE_FINAL.md", "EMPIRICAL_RUN_REGISTRY.json",
          "s13_dataset/s13_runs.csv", "s14_dataset/s14_runs.csv", "s14_dataset/s14_outcomes.csv"]:
    add("D. 13 Sep pilot (software testbed)", f"{P}/{f}", f.rsplit(".", 1)[-1], "")
def count_dirs(rel):
    p = os.path.join(REPO, rel)
    return len([x for x in os.listdir(p) if os.path.isdir(os.path.join(p, x))]) if os.path.isdir(p) else 0
for sub, note in (("s11_runs", "S11 closed-loop trials (act/noact)"), ("s15_runs", "S15 independent validation trials"), ("s14_runs", "S14 broader experiment"), ("runs", "earlier V2-V5 runs")):
    n = count_dirs(f"{P}/{sub}")
    rows.append(("D. 13 Sep pilot (software testbed)", f"{P}/{sub}/", "directories of logs", f"{n} run dirs", "-", "in git" if n else "ABSENT", note))
# D2. large files excluded from git (LARGE_FILES_NOT_IN_GIT.md)
large = open(os.path.join(REPO, "LARGE_FILES_NOT_IN_GIT.md")).read()
for m in re.finditer(r"\| `([^`]+)` \| ([\d.]+) \| `([0-9a-f]{64})` \|", large):
    rel, size, h = m.groups()
    present = os.path.isfile(os.path.join(REPO, rel))
    rows.append(("E. Large files listed in LARGE_FILES_NOT_IN_GIT.md", rel, rel.rsplit(".", 1)[-1], f"{size} MB (listed)", f"listed sha256 {h}", "present" if present else "ABSENT from repository (excluded, by design)", ""))
# F. catalogue and narrative
for f in ["ORAN_Fault_Detectability_v2026-10-05.xlsx", "ORAN_SPlane_Attack_vs_Benign_Classification_v2026-10-05.xlsx", "ORAN_SPlane_Packets_to_Classification_2026-10-05.xlsx",
          "ORAN_SPlane_Parameter_Fault_Matrix_v2026-10-05.xlsx", "ORAN_SPlane_Testbed_Configuration_Reference_v2026-10-05.pdf", "ORAN_SPlane_PRISM_Review_v8_view.pdf",
          "SPlane_Project_Story_Guide.pdf", "verification_records/V8_SLIDE_SOURCE_MAP.md"]:
    add("F. Catalogue, narrative and source documents", f"{DECK}/{f}", f.rsplit(".", 1)[-1], "")
for f in ["RESULTS_2026-10-05.md", "PREREGISTRATION.md", "STANDARDS_EVIDENCE.md", "RECOVERY_LOOP_DESIGN.md", "code/provisioning.json"]:
    add("F. Catalogue, narrative and source documents", f"{RL}/{f}", f.rsplit(".", 1)[-1], "")
add("F. Catalogue, narrative and source documents", "01_CURRENT_SPlane_SelfHealing/literature-survey/papers/Standards/ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf", "pdf", "listed in V8_SLIDE_SOURCE_MAP.md as a local copy")

# row counts that the ingest checks against
def tgz_dirs(path):
    with tarfile.open(path, "r:gz") as t:
        return len({n.lstrip("./").split("/")[0] for n in t.getnames() if "__r" in n})

summary = {
    "recovery_run_dirs_in_archive": tgz_dirs(os.path.join(REPO, RL, "results/recovery_eval_runs_r13-r17.tgz")),
}
with tarfile.open(os.path.join(REPO, CF, "splane_campaign_CORRECTED_2026-09-20.tgz"), "r:gz") as t:
    summary["campaign_run_dirs_in_archive"] = len({n.split("/")[2] for n in t.getnames() if n.startswith("./cap/") and n.count("/") >= 3})
s11 = json.load(open(os.path.join(REPO, P, "S11_CLOSED_LOOP_EVALUATION.json")))
summary["s11_runs"] = sum(len(v) for v in s11["runs"].values())
s15 = json.load(open(os.path.join(REPO, P, "S15_INDEPENDENT_VALIDATION_EVALUATION.json")))
summary["s15_runs"] = len(s15["runs"])

md = ["# 3D explorer: data inventory", "",
      "Generated by `ingest/inventory.py` (re-runnable). Hashes are computed from the files in this checkout; for files absent from the",
      "repository the hash shown is the one *recorded* in the project documents. Nothing absent is approximated.", "",
      "Legend: **in git** = tracked on this branch; **ABSENT** = not in the repository (so it cannot be ingested, and the 3D explorer must show",
      "it as \"not in repo / not measured\").", ""]
group = None
for g, rel, fmt, size, h, status, note in rows:
    if g != group:
        group = g
        md += ["", f"## {g}", "", "| Path | Format | Size | sha256 | Status | Note |", "|---|---|---:|---|---|---|"]
    md.append(f"| `{rel}` | {fmt} | {size} | `{h}` | {status} | {note} |")
md += ["", "## Counts used by the ingest row-count checks", "", "| Quantity | Value |", "|---|---:|"]
for k, v in summary.items():
    md.append(f"| {k} | {v} |")
md += ["", "## Findings", "",
  "1. **B6 raw samples are not in the repository.** Only the analysis outputs (`drift_pair*.json`, reports, PNGs) are. The raw per-sample CSVs are named, with their sha256, inside those JSON files but are absent. The app may show the derived figures (relative offset, per-arm ppm, ADEV/TDEV/MTIE) as *derived from the analysis output*; it must not draw a raw time series or approximate one. Run 1 is NOT ESTABLISHED (+20.161 ppm); run 2 is ESTABLISHED (+21.013 ppm [20.623, 21.403]).",
  "2. **13 Sep pilot.** S11 (10 trials, 5 act / 5 no-act) and S15 (30 trials) evaluation JSON and per-run logs are in git. The packet-level CSVs of S13/S14 and the large workbooks are excluded (see group E). S15 independent validation is NOT ESTABLISHED (trigger rate above boundary 14/15; no-trigger rate below boundary 8/15 vs the frozen 0.8).",
  "3. **168-run campaign.** `s14_runs`/`S14` (168 \"empirical software-testbed rows\" in `START_HERE_FINAL.md`) is a different 168 from the 14 scenarios x 12 replicates detector campaign; the 3D explorer uses the latter and calls the former \"13 Sep pilot S14\". Raw PCAPs of the detector campaign are not in its archive (deep CSVs are).",
  "4. **ETSI TS 103 982 v8 is listed as a local copy in `V8_SLIDE_SOURCE_MAP.md` but the PDF is not in this repository**, so no clause of it can be opened from here; clause citations that depend on it are carried only as relayed by the project documents and are marked UNVERIFIED or SOURCE_NEEDED in `content/architecture.json`.",
  "5. Not ingested: `recovery_dev_runs_r101.tgz` (pre-freeze development runs)."]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("\n".join(md) + "\n")
json.dump(summary, open(os.path.join(HERE, "..", "data", "derived", "inventory_counts.json"), "w"), indent=1)
print("wrote", OUT, summary)
