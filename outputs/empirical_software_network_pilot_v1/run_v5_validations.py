#!/usr/bin/env python3
"""Run validate_pilot_v5 on every directory in v5_runs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_pilot_v5 import validate
RUNS = HERE / "v5_runs"


def main() -> None:
    if not RUNS.is_dir():
        print("v5_runs directory does not exist")
        return

    dirs = sorted([d for d in RUNS.iterdir() if d.is_dir()])
    structurally_complete = 0
    failed = 0
    failed_names = []

    for d in dirs:
        report = validate(d)
        (d / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if report.get("status") == "STRUCTURALLY_COMPLETE":
            structurally_complete += 1
        else:
            failed += 1
            failed_names.append(d.name)

    res = {
        "total": len(dirs),
        "structurally_complete": structurally_complete,
        "failed": failed,
        "failed_directories": failed_names,
    }
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
