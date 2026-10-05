"""R4/R5: complete S14 inventory and sealed-manifest verification. Read-only on raw evidence.

Descriptive only. Condition labels are configured expectations, never harm labels.
"""
from __future__ import annotations
import hashlib, json, re, struct, sys
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
RUNS = HERE / "s14_runs"
MANDATORY = {"capture_seg1.pcap", "capture_seg2.pcap", "events.log", "slave.log",
             "master_a.log", "master_b.log", "slave.conf", "master_a.conf", "master_b.conf",
             "run_environment.txt", "decision_log.jsonl", "source_manifest.sha256"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def parse_manifest(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line.strip())
        if m:
            out[Path(m.group(2)).name] = m.group(1)
    return out


def ptp_count(p: Path) -> dict:
    try:
        with p.open("rb") as f:
            gh = f.read(24)
            if len(gh) < 24:
                return {"parsed": False, "reason": "short global header"}
            magic = struct.unpack("<I", gh[:4])[0]
            end = "<" if magic in (0xA1B2C3D4, 0xA1B23C4D) else ">"
            total = ptp = 0
            while True:
                h = f.read(16)
                if len(h) < 16:
                    break
                _s, _u, incl, _o = struct.unpack(end + "IIII", h)
                d = f.read(incl)
                if len(d) < incl:
                    break
                total += 1
                if len(d) >= 14 and d[12:14] == b"\x88\xf7":
                    ptp += 1
        return {"parsed": True, "records": total, "ptp_records": ptp}
    except Exception as e:
        return {"parsed": False, "reason": f"{type(e).__name__}: {e}"}


def verify(d: Path) -> dict:
    r = {"run": d.name, "files_present": sorted(p.name for p in d.iterdir() if p.is_file())}
    mp = d / "source_manifest.sha256"
    r["sealed"] = mp.is_file()
    problems = []
    if not r["sealed"]:
        problems.append("no source_manifest.sha256 (unsealed)")
        r["problems"] = problems
        return r
    man = parse_manifest(mp.read_text(encoding="utf-8", errors="replace"))
    r["manifest_entries"] = len(man)
    mism, missing = [], []
    for name, want in man.items():
        fp = d / name
        if not fp.is_file():
            missing.append(name); continue
        if name == "source_manifest.sha256":
            continue
        if sha256(fp) != want:
            mism.append(name)
    r["manifest_hash_mismatches"] = mism
    r["manifest_entries_missing_on_disk"] = missing
    r["all_manifest_hashes_match"] = not mism and not missing
    absent = sorted(MANDATORY - set(r["files_present"]))
    r["mandatory_entries_absent"] = absent
    ev = (d / "events.log").read_text(encoding="utf-8", errors="replace") if (d / "events.log").is_file() else ""
    r["phase_finished_present"] = "event=phase_finished" in ev
    r["event_fail_lines"] = [l for l in ev.splitlines() if "status=FAIL" in l]
    r["arm_from_events"] = (re.search(r"arm=(\S+)", ev).group(1) if re.search(r"arm=(\S+)", ev) else None)
    r["capture_seg1"] = ptp_count(d / "capture_seg1.pcap")
    r["capture_seg2"] = ptp_count(d / "capture_seg2.pcap")
    dl = d / "decision_log.jsonl"
    if dl.is_file():
        rows = [json.loads(l) for l in dl.read_text().splitlines() if l.strip()]
        ev_names = Counter(x["event"] for x in rows)
        r["decision_events"] = dict(ev_names)
        r["detector_triggered"] = "detection_trigger" in ev_names
        rc = [x.get("returncode") for x in rows if x["event"] == "action_execution_result"]
        r["action_returncodes"] = rc
    else:
        problems.append("decision_log.jsonl absent")
    if mism:
        problems.append(f"{len(mism)} manifest hash mismatch")
    if missing:
        problems.append(f"{len(missing)} manifest entries missing on disk")
    if absent:
        problems.append(f"mandatory absent: {absent}")
    if not r["phase_finished_present"]:
        problems.append("no phase_finished event")
    for k in ("capture_seg1", "capture_seg2"):
        if not r[k].get("parsed") or r[k].get("ptp_records", 0) == 0:
            problems.append(f"{k}: no decodable PTP records")
    r["problems"] = problems
    r["integrity_status"] = "SEALED_CONSISTENT" if not problems else "RETAINED_WITH_PROBLEMS"
    return r


def main() -> None:
    dirs = sorted(p for p in RUNS.iterdir() if p.is_dir())
    runs = [verify(d) for d in dirs]
    ok = [r for r in runs if r.get("integrity_status") == "SEALED_CONSISTENT"]
    bad = [r for r in runs if r.get("integrity_status") != "SEALED_CONSISTENT"]
    out = {
        "schema_version": "s14-evidence-verification-v1",
        "scope": ("R4/R5 only: complete inventory and sealed-manifest verification after writers "
                  "stopped. Descriptive. Condition labels are configured expectations, never harm "
                  "labels. No acceptance criterion is applied to any run."),
        "checked_after_batch_quiescent": True,
        "run_count": len(runs),
        "sealed_consistent": len(ok),
        "retained_with_problems": len(bad),
        "total_manifest_entries_rehashed": sum(r.get("manifest_entries", 0) for r in runs),
        "arms_present": dict(Counter(r.get("arm_from_events") for r in runs)),
        "runs": runs,
        "limits": [
            "Integrity verification only. It says the bytes are the sealed bytes; it says nothing "
            "about harmfulness, detector correctness, or action benefit.",
            "Condition and expected_classification strings are configured expectations.",
            "No numerical acceptance criterion is introduced here.",
        ],
    }
    (HERE / "S14_EVIDENCE_VERIFICATION.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=2))
    for r in bad:
        print("  PROBLEM", r["run"], r.get("problems"))


if __name__ == "__main__":
    main()
