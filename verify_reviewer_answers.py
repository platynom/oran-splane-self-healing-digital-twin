#!/usr/bin/env python3
"""Re-read consequential numbers and workbook fields used by the reviewer pack."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "03_RECOVERY_LOOP_S-PLANE" / "RESULTS_2026-10-05.md"
PREREG = ROOT / "03_RECOVERY_LOOP_S-PLANE" / "PREREGISTRATION.md"
EVAL_V4 = (
    ROOT
    / "01_CURRENT_SPlane_SelfHealing"
    / "oran_splane_selfhealing"
    / "gap_coverage_2026-09-20"
    / "corrected_final"
    / "EVALUATION_V4.json"
)
AUDIT = ROOT / "CITATION_VERIFICATION_2026-11.md"
ANSWERS = ROOT / "REVIEWER_ANSWERS_2026-11.md"
IMPACT = ROOT / "IMPACT_EVIDENCE_SCOPE.md"
REACTIVE = ROOT / "03_RECOVERY_LOOP_S-PLANE" / "REACTIVE_VS_PROACTIVE.md"
LATEST = ROOT / "00_LATEST_PRESENTED_DECK_AND_DELIVERABLES"


def require(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) is not None


def four_column_rows(path: Path, sheet: str) -> dict[str, tuple[str, str, str, str]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    wanted = [
        "Source (of attack or fault)",
        "Destination (where it hits in the architecture)",
        "Attack devices (possible originating devices)",
        "Consequence (effect)",
    ]
    for index, row in enumerate(rows):
        values = [str(value).strip() if value is not None else "" for value in row]
        if all(name in values for name in wanted):
            columns = [values.index(name) for name in wanted]
            output = {}
            for data_row in rows[index + 1 :]:
                key = str(data_row[0]).strip() if data_row and data_row[0] is not None else ""
                if key:
                    output[key] = tuple(str(data_row[col]).strip() for col in columns)
            return output
    raise RuntimeError(f"four-column header not found in {path.name}:{sheet}")


def main() -> int:
    failures: list[str] = []
    results = RESULTS.read_text(encoding="utf-8")
    prereg = PREREG.read_text(encoding="utf-8")
    answers = ANSWERS.read_text(encoding="utf-8")
    impact = IMPACT.read_text(encoding="utf-8")
    reactive = REACTIVE.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    evaluation = json.loads(EVAL_V4.read_text(encoding="utf-8"))

    # Campaign design and class counts.
    require(evaluation["n_runs"] == 168, "EVALUATION_V4 n_runs != 168", failures)
    require(len(evaluation["per_scenario_n"]) == 14, "campaign scenario count != 14", failures)
    require(set(evaluation["per_scenario_n"].values()) == {12}, "not every campaign scenario has 12 runs", failures)
    require(evaluation["v3"]["n_attack"] == 96, "v3 attack count != 96", failures)
    require(evaluation["v3"]["n_benign"] == 60, "v3 benign count != 60", failures)
    require(evaluation["v3"]["n_unknown"] == 12, "v3 unknown count != 12", failures)
    for scenario, correct in {
        "A1_rogue_master": 12,
        "A2_sync_spoof": 12,
        "A3_replay": 12,
        "A5_dos_flood": 12,
        "A8_rogue_bc": 12,
        "C1_removal": 11,
        "C2_malformed": 12,
        "C3_wholesecond": 12,
    }.items():
        actual = evaluation["v3"]["per_scenario"][scenario]["correct"]
        require(actual == correct, f"{scenario} correct={actual}, expected {correct}", failures)

    # Recovery design and all headline outcome numbers quoted in the new documents.
    for label, pattern in {
        "140-run design": r"\*\*140 live runs\*\*: 14 scenarios × 2 arms × 5 replicates",
        "A1 control/loop": r"A1 rogue grandmaster.*38\.5 s of 40.*\*\*2\.0 s\*\* median.*restored 5/5",
        "C1 control/loop": r"C1 interception.*39\.0 s of 40.*\*\*2\.5 s\*\* median.*restored 5/5",
        "C3 control/loop": r"C3 whole-second abuse.*38\.5 s of 40.*\*\*2\.0 s\*\* median.*restored 5/5",
        "zero-impact group": r"A2, A3, A5, A8, C2.*0 s.*0 s",
        "benign disruptive action": r"1 disruptive action in 25 runs",
        "detection/action timing": r"detection about 1\.1 s.*action about 2\.1 s",
        "isolation artifact count": r"35/35 isolations",
        "standby artifact count": r"6/6 standby activations",
    }.items():
        require(has(results, pattern), f"RESULTS missing {label}", failures)
    require(has(prereg, r"14 scenarios × 2 arms × 5 = \*\*140 runs\*\*"), "PREREGISTRATION 140-run arithmetic missing", failures)
    require(has(prereg, r"(?:at least|≥) 2 of the last 3 evaluations ATTACK"), "2-of-3 persistence missing", failures)
    require(has(prereg, r"no Announce.*for 2 s; 10 s while a maintenance window is open"), "service-loss thresholds missing", failures)

    # Citation verdict counts are computed from the audit rather than copied from prose.
    verdict_counts = {
        verdict: len(re.findall(rf"\|\s*{verdict}\s*\|$", audit, flags=re.MULTILINE))
        for verdict in ("CONFIRMED", "WRONG_CLAUSE", "NOT_SUPPORTED", "NOT_ACCESSIBLE")
    }
    require(
        verdict_counts == {"CONFIRMED": 63, "WRONG_CLAUSE": 2, "NOT_SUPPORTED": 3, "NOT_ACCESSIBLE": 14},
        f"citation verdict counts changed: {verdict_counts}",
        failures,
    )

    # The reviewer documents must carry the checked values and the explicit scope boundary.
    combined = "\n".join((answers, impact, reactive))
    for token in ("168", "140", "38.5", "39.0", "2.0", "2.5", "35/35", "6/6", "free_running 1"):
        require(token in combined, f"new documents missing checked token {token}", failures)
    require("3b not run: the active host is Windows" in impact, "3b host decision missing", failures)
    require("not predictive" in reactive.lower(), "predictive limitation missing", failures)

    # Confirm the four added columns agree across the three workbooks that repeat A1/A2/A3/A5/A8.
    workbook_rows = [
        four_column_rows(LATEST / "ORAN_Fault_Detectability_v2026-10-05.xlsx", "DETECTABILITY"),
        four_column_rows(LATEST / "ORAN_SPlane_Attack_vs_Benign_Classification_v2026-10-05.xlsx", "ATTACK catalog"),
        four_column_rows(LATEST / "ORAN_SPlane_Parameter_Fault_Matrix_v2026-10-05.xlsx", "FAULT KEY"),
    ]
    for attack_id in ("A1", "A2", "A3", "A5", "A8"):
        values = [rows.get(attack_id) for rows in workbook_rows]
        require(None not in values, f"{attack_id} missing from a repeated workbook", failures)
        require(values[0] == values[1] == values[2], f"{attack_id} four-column text disagrees", failures)

    # Every question has a direct section, Evidence and Limits block.
    for number in range(1, 17):
        section = re.search(
            rf"^## Q{number}\..*?(?=^## Q{number + 1}\.|^## Superseded|\Z)",
            answers,
            flags=re.MULTILINE | re.DOTALL,
        )
        require(section is not None, f"Q{number} section missing", failures)
        if section:
            require("**Evidence:**" in section.group(0), f"Q{number} Evidence block missing", failures)
            require("**Limits:**" in section.group(0), f"Q{number} Limits block missing", failures)

    print(f"Campaign/source checks: 31")
    print(f"Workbook agreement checks: 5")
    print(f"Reviewer section checks: 48")
    print(f"Citation verdict counts: {verdict_counts}")
    print(f"Mismatches: {len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
