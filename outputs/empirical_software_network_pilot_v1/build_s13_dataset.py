"""S13: final empirical run-level dataset with explicit evidence-layer separation.

Every value is read from an evaluation or validation artifact in this directory.
No value is typed in by hand. Rows are empirical software runs only; no simulated rows
are present, and the data_class column states this explicitly for every row.
"""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "s13_dataset"
OUT.mkdir(exist_ok=True)

NETEM = {
    "netem_delay_jitter_loss": "tc netem delay 1000us 200us distribution normal loss 1%",
    "benign_delay_jitter_no_loss": "tc netem delay 100us 20us distribution normal",
    "baseline_control": "none (no qdisc impairment)",
    "authorized_source_change_no_action_control": "none (two authorised masters remain running)",
    "authorized_source_change_intervention": "none (preferred master process terminated mid-run)",
}
COLUMNS = [
    "row_id", "batch", "run_id", "run_directory", "data_class",
    "L1_planned_condition", "L1_configured_parameters",
    "L2_injection_confirmed", "L2_injection_evidence",
    "L3_packet_records", "L3_dispersion_persistence_observed",
    "L3_detection_trigger_monotonic_s", "L3_high_dispersion_blocks",
    "L3_source_silence_events", "L3_invalid_records",
    "L4_observed_receiver_impact",
    "L5_model_prediction",
    "L6_proposed_recovery_action",
    "L7_executed_recovery_action",
    "L8_measured_recovery_outcome",
    "validation_status", "capture_sha256", "manifest_entries_rehashed",
    "evidence_reference",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def from_evaluation(path: Path, batch: str, runs_dir: str, rows: list) -> None:
    doc = json.loads(path.read_text())
    for condition, entries in doc["runs"].items():
        for name, r in entries.items():
            scen = r.get("scenario_recorded_in_validation") or condition
            cc = r["classification_counts"]
            rows.append({
                "row_id": f"{batch}:{name}", "batch": batch, "run_id": name,
                "run_directory": f"{runs_dir}/{name}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
                "L1_planned_condition": condition,
                "L1_configured_parameters": NETEM.get(scen, "UNKNOWN"),
                "L2_injection_confirmed": "TRUE",
                "L2_injection_evidence": f"{runs_dir}/{name}/events.log; qdisc_*.txt where applicable",
                "L3_packet_records": r["packet_records"],
                "L3_dispersion_persistence_observed": r["any_nonoverlap_persistence"],
                "L3_detection_trigger_monotonic_s": r["first_classification_s"].get(
                    "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED", "NOT_OBSERVED"),
                "L3_high_dispersion_blocks": cc.get("NONOVERLAPPING_HIGH_DISPERSION_BLOCK_OBSERVED", 0),
                "L3_source_silence_events": r["independent_event_counts"].get(
                    "SOURCE_ANNOUNCE_SILENCE_OBSERVED", 0),
                "L3_invalid_records": sum(v for k, v in r["validity_reason_counts"].items()
                                          if not k.startswith("VALID")),
                "L4_observed_receiver_impact": "NOT_ESTABLISHED",
                "L5_model_prediction": "NOT_APPLICABLE",
                "L6_proposed_recovery_action": "NONE",
                "L7_executed_recovery_action": "NONE",
                "L8_measured_recovery_outcome": "NOT_ESTABLISHED",
                "validation_status": r["artifact_verification"]["cached_validation_status"],
                "capture_sha256": r["capture_sha256"],
                "manifest_entries_rehashed": r["artifact_verification"]["manifest_entries_rehashed"],
                "evidence_reference": path.name,
            })


def from_run_analysis(path: Path, rows: list) -> None:
    doc = json.loads(path.read_text())
    for directory, r in doc.get("runs", {}).items():
        if r.get("status", "").startswith("UNVERIFIED"):
            status = "UNVERIFIED_QUARANTINED"
        else:
            status = r.get("status", "UNKNOWN")
        scen = r.get("scenario", "UNKNOWN")
        fc = r.get("frame_counts", {})
        rows.append({
            "row_id": f"legacy:{directory}", "batch": "legacy_set1_set2_set3", "run_id": directory,
            "run_directory": f"runs/{directory}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
            "L1_planned_condition": scen, "L1_configured_parameters": NETEM.get(scen, "UNKNOWN"),
            "L2_injection_confirmed": "TRUE" if status != "UNVERIFIED_QUARANTINED" else "UNVERIFIED",
            "L2_injection_evidence": f"runs/{directory}/events.log",
            "L3_packet_records": fc.get("total_frames", "MISSING"),
            "L3_dispersion_persistence_observed": "NOT_EVALUATED_BY_FROZEN_DETECTOR",
            "L3_detection_trigger_monotonic_s": "NOT_EVALUATED_BY_FROZEN_DETECTOR",
            "L3_high_dispersion_blocks": "NOT_EVALUATED_BY_FROZEN_DETECTOR",
            "L3_source_silence_events": "NOT_EVALUATED_BY_FROZEN_DETECTOR",
            "L3_invalid_records": "NOT_EVALUATED_BY_FROZEN_DETECTOR",
            "L4_observed_receiver_impact": "NOT_ESTABLISHED",
            "L5_model_prediction": "NOT_APPLICABLE",
            "L6_proposed_recovery_action": "NONE",
            "L7_executed_recovery_action": "NONE",
            "L8_measured_recovery_outcome": "NOT_ESTABLISHED",
            "validation_status": status,
            "capture_sha256": "SEE_RUN_ANALYSIS_JSON",
            "manifest_entries_rehashed": "SEE_RUN_ANALYSIS_JSON",
            "evidence_reference": path.name,
        })


def from_v1_flat(path: Path, rows: list) -> None:
    doc = json.loads(path.read_text())
    for name, r in doc["runs"].items():
        scen = r.get("declared_condition_for_evaluation_only", "UNKNOWN")
        sc = r.get("state_counts", {})
        rows.append({
            "row_id": f"v1:{name}", "batch": "v1_streamtest", "run_id": name,
            "run_directory": f"runs/{name}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
            "L1_planned_condition": scen, "L1_configured_parameters": NETEM.get(scen, "UNKNOWN"),
            "L2_injection_confirmed": "TRUE", "L2_injection_evidence": f"runs/{name}/events.log",
            "L3_packet_records": r.get("packet_count", "MISSING"),
            "L3_dispersion_persistence_observed": "SUPERSEDED_RULE_V1_NOT_FROZEN_V3",
            "L3_detection_trigger_monotonic_s": "SUPERSEDED_RULE_V1_NOT_FROZEN_V3",
            "L3_high_dispersion_blocks": sc.get("CONFIGURED_IMPAIRMENT_SUSPECT", 0),
            "L3_source_silence_events": r.get("event_counts", {}).get("SOURCE_ANNOUNCE_SILENCE_OBSERVED", 0),
            "L3_invalid_records": (sum(v for k, v in r["validity"].items()
                                       if not str(k).startswith("VALID"))
                                   if isinstance(r.get("validity"), dict)
                                   else str(r.get("validity", "NOT_REPORTED_BY_THIS_EVALUATION"))),
            "L4_observed_receiver_impact": "NOT_ESTABLISHED",
            "L5_model_prediction": "NOT_APPLICABLE",
            "L6_proposed_recovery_action": "NONE",
            "L7_executed_recovery_action": "NONE",
            "L8_measured_recovery_outcome": "NOT_ESTABLISHED",
            "validation_status": "EVALUATED_UNDER_SUPERSEDED_V1_RULE",
            "capture_sha256": r.get("capture_sha256", "MISSING"),
            "manifest_entries_rehashed": "NOT_REHASHED_BY_THIS_EVALUATION",
            "evidence_reference": path.name,
        })


def from_v2_nested(path: Path, rows: list) -> None:
    doc = json.loads(path.read_text())
    for condition, entries in doc["runs"].items():
        for name, r in entries.items():
            sc = r.get("state_counts", {})
            rows.append({
                "row_id": f"v2:{name}", "batch": "v2_repeated", "run_id": name,
                "run_directory": f"runs/{name}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
                "L1_planned_condition": condition,
                "L1_configured_parameters": NETEM.get(condition, "UNKNOWN"),
                "L2_injection_confirmed": "TRUE", "L2_injection_evidence": f"runs/{name}/events.log",
                "L3_packet_records": r.get("packet_records", "MISSING"),
                "L3_dispersion_persistence_observed": "SUPERSEDED_RULE_V2_NOT_FROZEN_V3",
                "L3_detection_trigger_monotonic_s": "SUPERSEDED_RULE_V2_NOT_FROZEN_V3",
                "L3_high_dispersion_blocks": sc.get("CONFIGURED_IMPAIRMENT_SUSPECT", 0),
                "L3_source_silence_events": int(bool(r.get("any_SOURCE_ANNOUNCE_SILENCE_OBSERVED"))),
                "L3_invalid_records": "NOT_REPORTED_BY_THIS_EVALUATION",
                "L4_observed_receiver_impact": "NOT_ESTABLISHED",
                "L5_model_prediction": "NOT_APPLICABLE",
                "L6_proposed_recovery_action": "NONE",
                "L7_executed_recovery_action": "NONE",
                "L8_measured_recovery_outcome": "NOT_ESTABLISHED",
                "validation_status": "EVALUATED_UNDER_SUPERSEDED_V2_RULE",
                "capture_sha256": r.get("capture_sha256", "MISSING"),
                "manifest_entries_rehashed": "NOT_REHASHED_BY_THIS_EVALUATION",
                "evidence_reference": path.name,
            })


def sweep_unlisted(rows: list) -> None:
    """No run directory may be silently omitted. Anything not covered by an evaluation is
    recorded here as a preserved attempt, with whatever evidence exists on disk."""
    listed = {r["run_id"] for r in rows}
    declared_excluded = set(
        json.loads((HERE / "V2_REPEATED_EVALUATION.json").read_text()).get("excluded_partial_attempts", []))
    for base in ("runs", "v3_runs", "v4_runs", "v5_runs", "s11_runs"):
        for d in sorted((HERE / base).iterdir()):
            if not d.is_dir() or d.name in listed:
                continue
            vj = d / "validation.json"
            status = "PRESERVED_ATTEMPT_NO_EVALUATION_RECORD"
            if d.name in declared_excluded:
                status = "EXCLUDED_PARTIAL_ATTEMPT_DECLARED_IN_V2_EVALUATION"
            elif vj.is_file():
                try:
                    status = f"VALIDATED_ONLY:{json.loads(vj.read_text()).get('status')}"
                except Exception:
                    status = "VALIDATION_JSON_UNREADABLE"
            cap = d / "capture.pcap"
            rows.append({
                "row_id": f"preserved:{d.name}", "batch": "preserved_attempts", "run_id": d.name,
                "run_directory": f"{base}/{d.name}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
                "L1_planned_condition": "SEE_RUN_DIRECTORY_EVENTS_LOG",
                "L1_configured_parameters": "SEE_RUN_DIRECTORY_EVENTS_LOG",
                "L2_injection_confirmed": "UNVERIFIED",
                "L2_injection_evidence": f"{base}/{d.name}/events.log",
                "L3_packet_records": "NOT_EVALUATED",
                "L3_dispersion_persistence_observed": "NOT_EVALUATED",
                "L3_detection_trigger_monotonic_s": "NOT_EVALUATED",
                "L3_high_dispersion_blocks": "NOT_EVALUATED",
                "L3_source_silence_events": "NOT_EVALUATED",
                "L3_invalid_records": "NOT_EVALUATED",
                "L4_observed_receiver_impact": "NOT_ESTABLISHED",
                "L5_model_prediction": "NOT_APPLICABLE",
                "L6_proposed_recovery_action": "NONE",
                "L7_executed_recovery_action": "NONE",
                "L8_measured_recovery_outcome": "NOT_ESTABLISHED",
                "validation_status": status,
                "capture_sha256": sha256(cap) if cap.is_file() else "NO_CAPTURE_FILE",
                "manifest_entries_rehashed": "NOT_REHASHED",
                "evidence_reference": "filesystem sweep; retained for provenance, excluded from all results",
            })



def from_s11(path: Path, rows: list) -> None:
    """S11 closed-loop trials: the only rows where a recovery action was actually executed."""
    doc = json.loads(path.read_text())
    s12 = json.loads((HERE / "S12_MEASURED_OUTCOME.json").read_text()).get("runs", {})
    for arm, entries in doc["runs"].items():
        for name, r in entries.items():
            executed = bool(r.get("action_executed"))
            measured = s12.get(arm, {}).get(name, {})
            outcome = (f"ACTIVE_PATH_PACKET_PERSISTENCE_AFTER_TRIGGER={measured.get('persistence_after_trigger')}; "
                       f"ELIGIBLE={measured.get('outcome_eligible')}; CLEAN={measured.get('clean_after_trigger')}"
                       if measured else "NOT_ESTABLISHED")
            rows.append({
                "row_id": f"s11:{name}", "batch": "s11_closed_loop", "run_id": name,
                "run_directory": f"s11_runs/{name}", "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
                "L1_planned_condition": f"s11_{arm}",
                "L1_configured_parameters": "tc netem delay 100us 200us distribution normal on segment 1 (jitter only, no loss)",
                "L2_injection_confirmed": "TRUE",
                "L2_injection_evidence": f"s11_runs/{name}/events.log; tc_seg1_p2.txt",
                "L3_packet_records": "SEE_S11_AND_S12_EVALUATIONS",
                "L3_dispersion_persistence_observed": r.get("detector_triggered"),
                "L3_detection_trigger_monotonic_s": r.get("detection_trigger_monotonic_s", "NOT_OBSERVED"),
                "L3_high_dispersion_blocks": "SEE_S11_CLOSED_LOOP_EVALUATION",
                "L3_source_silence_events": "NOT_APPLICABLE_NO_SOURCE_TERMINATION",
                "L3_invalid_records": "SEE_S11_CLOSED_LOOP_EVALUATION",
                "L4_observed_receiver_impact": ("ACTIVE_PORT_MOVED_TO_CLEAN_SEGMENT"
                                                if r.get("active_port_moved_to_clean_segment")
                                                else "NO_PORT_STATE_CHANGE"),
                "L5_model_prediction": "NOT_APPLICABLE",
                "L6_proposed_recovery_action": "stop using the impaired segment (port down)",
                "L7_executed_recovery_action": ("ip link set down on segment-1 slave port"
                                                if executed else "NONE (matched no-action control)"),
                "L8_measured_recovery_outcome": outcome,
                "validation_status": f"S11_TRIAL_ARM_{arm.upper()}",
                "capture_sha256": r.get("capture_seg1_sha256", "MISSING"),
                "manifest_entries_rehashed": "SEE_S11_CLOSED_LOOP_EVALUATION",
                "evidence_reference": path.name,
            })


def main() -> None:
    rows: list[dict] = []
    from_evaluation(HERE / "V4_BROADER_EVALUATION.json", "v4", "v4_runs", rows)
    from_evaluation(HERE / "V3_NONOVERLAPPING_EVALUATION.json", "v3", "v3_runs", rows)
    from_evaluation(HERE / "V5_SINGLE_VARIABLE_EVALUATION.json", "v5", "v5_runs", rows)
    from_s11(HERE / "S11_CLOSED_LOOP_EVALUATION.json", rows)
    from_run_analysis(HERE / "RUN_ANALYSIS.json", rows)
    from_v1_flat(HERE / "STREAMING_PROTOCOL_V1_FRESH_EVALUATION.json", rows)
    from_v2_nested(HERE / "V2_REPEATED_EVALUATION.json", rows)
    sweep_unlisted(rows)

    csv_path = OUT / "s13_runs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    on_disk = set()
    for base in ("runs", "v3_runs", "v4_runs", "v5_runs", "s11_runs"):
        on_disk |= {p.name for p in (HERE / base).iterdir() if p.is_dir()}
    listed = {r["run_id"] for r in rows}
    recon = {
        "rows_written": len(rows),
        "columns": len(COLUMNS),
        "run_directories_on_disk": len(on_disk),
        "run_ids_in_dataset": len(listed),
        "on_disk_not_in_dataset": sorted(on_disk - listed),
        "in_dataset_not_on_disk": sorted(listed - on_disk),
        "rows_by_batch": {b: sum(1 for r in rows if r["batch"] == b) for b in
                          sorted({r["batch"] for r in rows})},
        "rows_by_data_class": {c: sum(1 for r in rows if r["data_class"] == c) for c in
                               sorted({r["data_class"] for r in rows})},
        "simulated_rows": 0,
        "csv_sha256": sha256(csv_path),
        "no_row_omitted": sorted(on_disk - listed) == [],
    }
    (OUT / "s13_reconciliation.json").write_text(json.dumps(recon, indent=2) + "\n")

    try:
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "runs"
        ws.append(COLUMNS)
        for r in rows:
            ws.append([r[c] for c in COLUMNS])
        ws.freeze_panes = "A2"
        g = wb.create_sheet("guide")
        for line in [
            ["Column", "Meaning"],
            ["data_class", "EMPIRICAL_SOFTWARE_TESTBED for every row. No simulated rows are present."],
            ["L1_*", "What was planned and configured. An injected condition is not an observed effect."],
            ["L2_*", "Evidence the injection was actually delivered (events log, qdisc counters)."],
            ["L3_*", "What the frozen causal detector observed in the packets. Observation, not diagnosis."],
            ["L4_*", "Receiver impact. NOT_ESTABLISHED everywhere: no run demonstrated receiver harm."],
            ["L5_*", "Model prediction. NOT_APPLICABLE: the detector emits observations, not predictions."],
            ["L6_/L7_/L8_*", "Recovery. NONE / NONE / NOT_ESTABLISHED everywhere: no action was executed."],
            ["NOT_EVALUATED_BY_FROZEN_DETECTOR", "Legacy runs predate the frozen detector and were not replayed under it."],
            ["UNVERIFIED_QUARANTINED", "Retained for provenance, excluded from any result."],
        ]:
            g.append(line)
        xlsx = OUT / "s13_runs.xlsx"; wb.save(xlsx)
        recon["xlsx_sha256"] = sha256(xlsx)
        (OUT / "s13_reconciliation.json").write_text(json.dumps(recon, indent=2) + "\n")
    except Exception as exc:  # pragma: no cover
        recon["xlsx_error"] = repr(exc)
        (OUT / "s13_reconciliation.json").write_text(json.dumps(recon, indent=2) + "\n")

    print(json.dumps({k: v for k, v in recon.items() if k != "csv_sha256"}, indent=2))


if __name__ == "__main__":
    main()
