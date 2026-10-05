"""Bounded OOXML inspection of final workbook without loading all source rows."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
BOOK = BASE / "ORAN_All_Current_Datasets_CORRECTED.xlsx"

with zipfile.ZipFile(BOOK) as archive:
    workbook = archive.read("xl/workbook.xml").decode("utf-8")
    names = re.findall(r'<(?:x:)?sheet name="([^"]+)" sheetId="(\d+)"', workbook)
    checks = {"zip_integrity": archive.testzip() is None, "sheet_count": len(names), "sheets": {}}
    for name, sid in names:
        if name in {"Summary", "Source status", "Evidence examples", "Read me"}:
            continue
        xml = archive.read(f"xl/worksheets/sheet{sid}.xml").decode("utf-8")
        checks["sheets"][name] = {
            "filter": "autoFilter" in xml,
            "freeze_pane": ":pane" in xml,
            "inline_strings": "inlineStr" in xml,
            "raw_header_present": "Audit source record" in xml,
            "status_field_present": "Audit eligibility" in xml,
            "proposed_action_field_present": "Proposed recovery action" in xml,
        }
    s001_id = next(sid for name, sid in names if name.startswith("S001 "))
    s001 = archive.read(f"xl/worksheets/sheet{s001_id}.xml").decode("utf-8")
    checks["s001_timestamp_literal"] = "2026-08-07T04:31:22.765639+00:00" in s001
    checks["s001_timestamp_column_width"] = bool(re.search(r'<x:col min="1" max="1" width="36"', s001))
    checks["all_detail_checks_pass"] = all(all(item.values()) for item in checks["sheets"].values())
print(json.dumps(checks, indent=2))
(BASE / "saved_workbook_bounded_inspection.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
