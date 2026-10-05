"""Create a read-only, evidence-first inventory of active external TIMESAFE files.

This is a static dependency audit.  A textual reference demonstrates that code can
load a file; it does not prove a particular runtime invocation used it.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
EXTERNAL = APP / "data" / "external"
SOURCE = ROOT / "dataset" / "timesafe"
TEXT_SUFFIXES = {".py", ".yaml", ".yml", ".toml", ".json", ".md"}
SKIP_PARTS = {"data", "results", ".git", "__pycache__", ".pytest_cache", ".codex_tmp_consistency"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_facts(path: Path) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return {"row_count": rows, "columns": header}


def code_references() -> list[dict]:
    references = []
    for path in APP.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            rel = path.relative_to(APP)
        except ValueError:
            continue
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"data[\\/]external|timesafe_sessions|timesafe_.*\.pcap", line, re.I):
                references.append({"file": str(rel), "line": number, "text": line.strip()})
    return references


def main() -> None:
    external_files = sorted(path for path in EXTERNAL.rglob("*") if path.is_file())
    source_files = sorted(path for path in SOURCE.rglob("*") if path.is_file())
    # Hash all candidate originals once. This permits byte-identical copies to
    # be stated precisely without inferring the experiment or label semantics.
    source_by_hash: dict[str, list[str]] = {}
    for path in source_files:
        source_by_hash.setdefault(sha256(path), []).append(str(path.relative_to(ROOT)))

    inventory = []
    for path in external_files:
        digest = sha256(path)
        item = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": digest,
            "suffix": path.suffix.lower(),
            "source_byte_identical_paths": source_by_hash.get(digest, []),
            "disposition": "requires use/label review",
        }
        if path.suffix.lower() == ".csv":
            item.update(csv_facts(path))
        if "timesafe_sessions" in path.parts:
            item["disposition"] = "projected session; evaluation gate rejects it without traceable independent validation"
        elif item["source_byte_identical_paths"]:
            item["disposition"] = "byte-identical project copy; preserve provenance, do not count as independent evidence"
        inventory.append(item)

    result = {
        "purpose": "Read-only source traceability and static dependency audit.",
        "scope": {
            "project_external_root": str(EXTERNAL.relative_to(ROOT)),
            "candidate_original_root": str(SOURCE.relative_to(ROOT)),
            "static_scan_exclusions": sorted(SKIP_PARTS),
        },
        "runtime_interpretation": "Static references show code paths that can load data. They do not prove a runtime invocation or prove other historical files are unused.",
        "static_references": code_references(),
        "external_inventory": inventory,
    }
    output = Path(__file__).with_name("source_traceability_audit.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {output}: external_files={len(inventory)}, static_references={len(result['static_references'])}")


if __name__ == "__main__":
    main()
