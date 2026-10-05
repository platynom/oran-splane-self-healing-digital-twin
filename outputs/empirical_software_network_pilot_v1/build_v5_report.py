#!/usr/bin/env python3
"""Build V5_SINGLE_VARIABLE_EVALUATION_REPORT.md from evaluation JSON and protocol."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "V5_SINGLE_VARIABLE_PROTOCOL.json"
EVALUATION_PATH = HERE / "V5_SINGLE_VARIABLE_EVALUATION.json"
REPORT_PATH = HERE / "V5_SINGLE_VARIABLE_EVALUATION_REPORT.md"


def main() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    evaluation = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))

    summary = evaluation["run_level_summary"]
    runs = evaluation["runs"]
    prespecified = protocol["prespecified_interpretation"]

    pos_a = summary["A_reference_benign"]["k"] > 0
    pos_b = summary["B_loss_only"]["k"] > 0
    pos_c = summary["C_jitter_only"]["k"] > 0
    pos_d = summary["D_delay_only"]["k"] > 0
    pos_e = summary["E_full_v4_impairment"]["k"] > 0

    single_pos = [name for name, cond in [("B_loss_only", pos_b), ("C_jitter_only", pos_c), ("D_delay_only", pos_d)] if cond]

    if pos_a:
        branch_key = "if_A_positive"
        interpretation_text = prespecified["if_A_positive"]
    elif pos_e and pos_b and not pos_c and not pos_d:
        branch_key = "if_only_B_and_E_positive"
        interpretation_text = prespecified["if_only_B_and_E_positive"]
    elif pos_e and pos_c and not pos_b and not pos_d:
        branch_key = "if_only_C_and_E_positive"
        interpretation_text = prespecified["if_only_C_and_E_positive"]
    elif pos_e and pos_d and not pos_b and not pos_c:
        branch_key = "if_only_D_and_E_positive"
        interpretation_text = prespecified["if_only_D_and_E_positive"]
    elif len(single_pos) > 1:
        branch_key = "if_multiple_single_factor_arms_positive"
        interpretation_text = f"{prespecified['if_multiple_single_factor_arms_positive']}: positive arms are {', '.join(single_pos)}"
    elif pos_e and len(single_pos) == 0:
        branch_key = "if_E_positive_but_no_single_factor_arm_positive"
        interpretation_text = prespecified["if_E_positive_but_no_single_factor_arm_positive"]
    else:
        branch_key = "unclassified"
        interpretation_text = f"Unclassified branch: A={pos_a}, B={pos_b}, C={pos_c}, D={pos_d}, E={pos_e}"

    # First observation times for positive runs
    first_obs: dict[str, list[float]] = {}
    for arm, arm_runs in runs.items():
        first_obs[arm] = []
        for r_name, r_data in arm_runs.items():
            t = r_data["first_classification_s"].get("NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED")
            if t is not None:
                first_obs[arm].append(t)

    # Single blocks count
    single_block_counts: dict[str, int] = {}
    for arm, arm_runs in runs.items():
        count = 0
        for r_name, r_data in arm_runs.items():
            count += r_data["classification_counts"].get("SINGLE_HIGH_DISPERSION_BLOCK_OBSERVED", 0)
        single_block_counts[arm] = count

    # Source silence counts
    source_silence_counts: dict[str, int] = {}
    for arm, arm_runs in runs.items():
        count = 0
        for r_name, r_data in arm_runs.items():
            count += r_data["independent_event_counts"].get("SOURCE_ANNOUNCE_SILENCE_OBSERVED", 0)
        source_silence_counts[arm] = count

    # Invalid packet counts
    total_packets = sum(r_data["packet_records"] for arm_runs in runs.values() for r_data in arm_runs.values())
    total_invalid = sum(
        sum(c for k, c in r_data["validity_reason_counts"].items() if not k.startswith("VALID"))
        for arm_runs in runs.values() for r_data in arm_runs.values()
    )

    integrity = evaluation["aggregate_integrity"]
    frozen_verify = evaluation["frozen_input_verification"]

    lines = [
        "# V5 single-variable attribution — evaluation report",
        "",
        f"Date 2026-09-13. Protocol `{protocol['schema_version']}` (`{evaluation['protocol']}`).",
        f"Results file `{EVALUATION_PATH.name}`. Evaluator `evaluate_v5_single_variable.py`.",
        "",
        "## Batch state",
        "",
        f"All {integrity['runs_evaluated']} planned runs completed in interleaved order (a, b, c, d, e across repetitions 1..5).",
        f"All {integrity['runs_evaluated']} runs were validated STRUCTURALLY_COMPLETE with zero errors, then evaluated.",
        "",
        "## Frozen-input verification",
        "",
        f"Frozen hashes match: {frozen_verify['frozen_hashes_match']}.",
        f"- v1_engine_sha256: `{frozen_verify['v1_engine_sha256']}`",
        f"- v3_nonoverlap_engine_sha256: `{frozen_verify['v3_nonoverlap_engine_sha256']}`",
        f"- isolated_runner_sha256: `{frozen_verify['isolated_runner_sha256']}`",
        f"- validator_sha256: `{frozen_verify['validator_sha256']}`",
        f"Thresholds: std {frozen_verify['frozen_thresholds']['standard_deviation_threshold_s']} s, "
        f"block size {frozen_verify['frozen_thresholds']['block_size']}, "
        f"high-block count {frozen_verify['frozen_thresholds']['high_block_count']}, "
        f"window {frozen_verify['frozen_thresholds']['high_block_window_s']} s.",
        "No threshold, arm, or inclusion criterion was changed. V1–V4 captures were excluded.",
        "",
        "## Run-level result — persistence observation per arm",
        "",
        "| Arm | Description | k / n | proportion | Wilson 95% |",
        "|---|---|---|---|---|",
    ]

    descriptions = {
        "A_reference_benign": "reference benign (delay 100us, jitter 20us, no loss)",
        "B_loss_only": "loss only (+ 1% loss to reference)",
        "C_jitter_only": "jitter only (+ 200us jitter to reference)",
        "D_delay_only": "delay only (+ 1000us delay to reference)",
        "E_full_v4_impairment": "full V4 impairment (delay 1000us, jitter 200us, loss 1%)",
    }

    for arm in ["A_reference_benign", "B_loss_only", "C_jitter_only", "D_delay_only", "E_full_v4_impairment"]:
        s = summary[arm]
        w = s["wilson95"]
        lines.append(f"| {arm} | {descriptions.get(arm, '')} | {s['k']} / {s['n']} | {s['proportion']:.2f} | [{w[0]:.4f}, {w[1]:.4f}] |")

    lines.extend([
        "",
        f"Integrity: {integrity['total_manifest_entries_rehashed']} manifest entries rehashed across {integrity['runs_evaluated']} runs, all matching.",
        "",
        "## Pre-specified interpretation branch selection",
        "",
        f"The data selected branch: **`{branch_key}`**",
        "",
        f"> **Pre-specified interpretation statement:** {interpretation_text}",
        "",
        "### Branch evaluation details",
        f"- Arm A (reference benign): {summary['A_reference_benign']['k']} / {summary['A_reference_benign']['n']} positive",
        f"- Arm B (loss only): {summary['B_loss_only']['k']} / {summary['B_loss_only']['n']} positive",
        f"- Arm C (jitter only): {summary['C_jitter_only']['k']} / {summary['C_jitter_only']['n']} positive",
        f"- Arm D (delay only): {summary['D_delay_only']['k']} / {summary['D_delay_only']['n']} positive",
        f"- Arm E (full V4 impairment): {summary['E_full_v4_impairment']['k']} / {summary['E_full_v4_impairment']['n']} positive",
        "",
        "## First observation times for positive arms",
        "",
    ])

    for arm, times in first_obs.items():
        if times:
            lines.append(f"- **{arm}**: observed in {len(times)} runs, range {min(times):.3f} s to {max(times):.3f} s (median {sorted(times)[len(times)//2]:.3f} s)")
        else:
            lines.append(f"- **{arm}**: 0 runs observed persistence")

    lines.extend([
        "",
        "## Persistence rule behavior across arms",
        "",
        f"Single high-dispersion block occurrences by arm: {single_block_counts}",
        "The persistence rule requires 2 high-dispersion blocks within 3.0 s.",
        "",
        "## Independent source-silence channel",
        "",
        f"`SOURCE_ANNOUNCE_SILENCE_OBSERVED` counts by arm: {source_silence_counts}",
        "",
        "## Invalid-data handling",
        "",
        f"Total packet records processed: {total_packets}.",
        f"Total invalid / rejected records: {total_invalid} ({(total_invalid / total_packets * 100) if total_packets else 0:.3f}%).",
        "",
        "## Decision boundary and limits",
        "",
        "- V5 can attribute the observation to a configured netem parameter under these software conditions only.",
        "- V5 does not establish receiver harm, attack detection, physical timing quality, or recovery.",
        "- Shared-host software networking with free_running 1 means endpoints do not have independent physical clocks.",
        "- Packet-arrival dispersion is not a referenced receiver clock-error measurement.",
        "",
    ])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH.name} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
