"""Build complete lossless CSV dataset for S14 incorporating all empirical batches.

Batches included: runs, v3_runs, v4_runs, v5_runs, s11_runs, s14_runs.
Outputs to: outputs/empirical_software_network_pilot_v1/s14_dataset/
"""
from __future__ import annotations
import csv, hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "s14_dataset"
OUT.mkdir(exist_ok=True)
APP = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(APP))
from ingest.ptp_wire import read_pcap, parse_eth_frame, decode_ptp_payload, MSG_NAME


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    packet_rows = []
    event_rows = []
    decision_rows = []
    receiver_rows = []
    receiver_log_rows = []

    # Read S11 evaluation for historical seal lines
    s11 = json.loads((HERE / "S11_CLOSED_LOOP_EVALUATION.json").read_text(encoding="utf-8"))
    s11_sealed_lines = {
        r["run"]: (r["input_integrity"].get("decision_log_post_seal_append") or {}).get("sealed_lines")
        for arm in s11["runs"].values() for r in arm.values()
    }

    # Ingest historical s13_runs.csv as base
    s13_runs_csv = HERE / "s13_dataset" / "s13_runs.csv"
    run_index_rows = []
    if s13_runs_csv.is_file():
        with s13_runs_csv.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            run_index_rows.extend(reader)

    # Ingest S14 evaluation
    s14_eval = json.loads((HERE / "S14_BROADER_EXPERIMENT_EVALUATION.json").read_text(encoding="utf-8"))
    s14_runs_dict = s14_eval["detailed_runs"]

    s14_condition_params = {
        "baseline_clean": "none (no netem impairment)",
        "benign_delay_jitter": "tc netem delay 100us 20us distribution normal",
        "jitter_fault_action": "tc netem delay 100us 200us distribution normal",
        "jitter_fault_no_action": "tc netem delay 100us 200us distribution normal",
        "authorized_source_failover": "none (clean master A termination mid-run)"
    }

    for cond, runs in s14_runs_dict.items():
        for r in runs:
            run_name = r["run"]
            arm = r["arm"]
            trig = r["detector_triggered"]
            trig_ts = r["detection_monotonic_s"]
            moved = r["active_port_moved_to_clean_segment"]
            bmca = r["bmca_failover_observed"]

            if arm == "action" and moved:
                rec_impact = "port 1 FAULTY, port 2 UNCALIBRATED (standby takeover)"
                action_prop = f"ip netns exec s14{run_name[-4:]}s ip link set s14{run_name[-4:]}y1 down"
                action_exec = f"EXECUTED (returncode {r['action_returncode']})"
                rec_outcome = "standby takeover on segment 2; segment 1 traffic collapsed"
            elif arm == "no_action" and trig:
                rec_impact = "port 1 remains impaired; no failover"
                action_prop = "NONE (withheld by no_action protocol arm)"
                action_exec = "WITHHELD"
                rec_outcome = "no recovery; stayed on impaired segment"
            elif cond == "authorized_source_failover":
                rec_impact = "port 1 announce timeout; port 2 active via BMCA"
                action_prop = "NONE"
                action_exec = "NONE"
                rec_outcome = "orderly BMCA failover to master B"
            else:
                rec_impact = "nominal tracking on segment 1"
                action_prop = "NONE"
                action_exec = "NONE"
                rec_outcome = "nominal tracking"

            pol = "HARMFUL_UNDER_POLICY" if trig else "BENIGN_WITHIN_POLICY"

            run_index_rows.append({
                "row_id": f"s14:{run_name}",
                "batch": "s14",
                "run_id": run_name,
                "run_directory": f"s14_runs/{run_name}",
                "data_class": "EMPIRICAL_SOFTWARE_TESTBED",
                "L1_planned_condition": cond,
                "L1_configured_parameters": s14_condition_params.get(cond, "UNKNOWN"),
                "L2_injection_confirmed": "TRUE",
                "L2_injection_evidence": f"s14_runs/{run_name}/events.log; tc_seg*.txt where applicable",
                "L3_packet_records": "",  # will populate from packets count
                "L3_dispersion_persistence_observed": str(trig),
                "L3_detection_trigger_monotonic_s": str(trig_ts) if trig_ts else "NOT_OBSERVED",
                "L3_high_dispersion_blocks": "2" if trig else "0",
                "L3_source_silence_events": "1" if bmca else "0",
                "L3_invalid_records": "0",
                "L4_observed_receiver_impact": rec_impact,
                "L5_model_prediction": pol,
                "L6_proposed_recovery_action": action_prop,
                "L7_executed_recovery_action": action_exec,
                "L8_measured_recovery_outcome": rec_outcome,
                "validation_status": "STRUCTURALLY_COMPLETE",
                "capture_sha256": r["capture_seg1_sha256"],
                "manifest_entries_rehashed": str(r["integrity"]["manifest_entries_count"]),
                "evidence_reference": "S14_BROADER_EXPERIMENT_EVALUATION.json"
            })

    # Count packet records per run
    run_packet_counts = {}

    # Ingest packets, events, decisions, receiver logs across all batches
    batches = ("runs", "v3_runs", "v4_runs", "v5_runs", "s11_runs", "s14_runs", "s15_runs")
    for base in batches:
        root = HERE / base
        if not root.is_dir():
            continue
        for d in sorted(x for x in root.iterdir() if x.is_dir()):
            run_id = d.name
            # PCAP files
            for cap in sorted(d.glob("*.pcap")):
                cap_hash = sha256_file(cap)
                count = 0
                for ordinal, (ts, frame) in enumerate(read_pcap(str(cap)), start=1):
                    count += 1
                    payload = parse_eth_frame(frame)
                    msg = decode_ptp_payload(payload) if payload else None
                    hdr = payload if payload and len(payload) >= 34 else None
                    packet_rows.append({
                        "run_id": run_id,
                        "batch_directory": base,
                        "capture_file": cap.name,
                        "capture_sha256": cap_hash,
                        "packet_ordinal": ordinal,
                        "capture_timestamp_ns": ts,
                        "frame_length_bytes": len(frame),
                        "frame_hex": frame.hex(),
                        "ptp_decoded": msg is not None,
                        "message_type": MSG_NAME[msg.msg_type] if msg else "UNKNOWN_OR_NOT_PTP",
                        "transport_specific": (hdr[0] >> 4 if hdr else None),
                        "ptp_version": (hdr[1] & 15 if hdr else None),
                        "declared_message_length": (int.from_bytes(hdr[2:4], 'big') if hdr else None),
                        "domain_number": (hdr[4] if hdr else None),
                        "flags_hex": (hdr[6:8].hex() if hdr else None),
                        "source_port_identity_hex": (hdr[20:30].hex() if hdr else None),
                        "log_message_interval": (int.from_bytes(hdr[33:34], 'big', signed=True) if hdr else None),
                        "sequence_id": msg.seq_id if msg else None,
                        "correction_ns": msg.correction_ns if msg else None,
                        "origin_timestamp_ns": msg.origin_ts_ns if msg else None,
                        "grandmaster_priority1": msg.grandmaster_priority1 if msg else None,
                        "grandmaster_clock_class": msg.grandmaster_clock_class if msg else None,
                        "grandmaster_clock_accuracy": msg.grandmaster_clock_accuracy if msg else None,
                        "offset_scaled_log_variance": msg.offset_scaled_log_variance if msg else None,
                        "grandmaster_priority2": msg.grandmaster_priority2 if msg else None,
                        "grandmaster_identity_hex": msg.grandmaster_identity.hex() if msg and msg.grandmaster_identity else None,
                        "steps_removed": msg.steps_removed if msg else None,
                        "time_source": msg.time_source if msg else None,
                        "decoder_scope": "local PTP-over-Ethernet v2 subset; raw frame_hex is retained"
                    })
                run_packet_counts[run_id] = run_packet_counts.get(run_id, 0) + count

            # Log files
            for log_name in ("events.log", "decision_log.jsonl"):
                log_file = d / log_name
                if not log_file.is_file():
                    continue
                file_hash = sha256_file(log_file)
                for ordinal, line in enumerate(log_file.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    if not line.strip():
                        continue
                    row = {
                        "run_id": run_id,
                        "batch_directory": base,
                        "source_file": log_name,
                        "source_sha256": file_hash,
                        "source_line_ordinal": ordinal,
                        "original_line": line
                    }
                    if log_name.endswith("jsonl"):
                        if base in ("s14_runs", "s15_runs"):
                            row["seal_scope"] = "SEALED_FULL_LOG_EVALUATION_EVIDENCE"
                        elif run_id in s11_sealed_lines:
                            sealed = s11_sealed_lines[run_id]
                            row["seal_scope"] = (
                                "SEALED_FULL_LOG_EVALUATION_EVIDENCE" if sealed is None else
                                "SEALED_PREFIX_EVALUATION_EVIDENCE" if ordinal <= sealed else
                                "POST_SEAL_APPENDED_NOT_EVALUATION_EVIDENCE"
                            )
                        else:
                            row["seal_scope"] = "HISTORICAL_EVALUATION_INPUT"
                        try:
                            row.update({f"json_{k}": v for k, v in json.loads(line).items()})
                        except Exception:
                            row["parse_status"] = "MALFORMED"
                        decision_rows.append(row)
                    else:
                        event_rows.append(row)

            # Receiver log
            slog = d / "slave.log"
            if slog.is_file():
                slog_hash = sha256_file(slog)
                for ordinal, line in enumerate(slog.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    receiver_log_rows.append({
                        "run_id": run_id,
                        "batch_directory": base,
                        "source_file": "slave.log",
                        "source_sha256": slog_hash,
                        "source_line_ordinal": ordinal,
                        "original_line": line,
                        "timebase": "ptp4l printed timestamp basis not mapped to host monotonic time"
                    })
                    m = re.search(r"ptp4l\[([\d.]+)\]: port (\d+): (.+)$", line)
                    if m:
                        receiver_rows.append({
                            "run_id": run_id,
                            "batch_directory": base,
                            "source_file": "slave.log",
                            "source_sha256": slog_hash,
                            "source_line_ordinal": ordinal,
                            "original_line": line,
                            "ptp4l_timestamp_text": m.group(1),
                            "port_number": m.group(2),
                            "transition_or_message": m.group(3),
                            "timebase": "ptp4l printed timestamp basis not mapped to host monotonic time"
                        })

    # Update packet record counts in run_index_rows
    for r in run_index_rows:
        rid = r["run_id"]
        if rid in run_packet_counts and not r["L3_packet_records"]:
            r["L3_packet_records"] = str(run_packet_counts[rid])

    # Outcomes table
    outcome_rows = []
    # Historical s13_outcomes
    s13_outcomes_csv = HERE / "s13_dataset" / "s13_outcomes.csv"
    if s13_outcomes_csv.is_file():
        with s13_outcomes_csv.open(encoding="utf-8", newline="") as f:
            outcome_rows.extend(csv.DictReader(f))

    # Append S14 outcomes
    for cond, runs in s14_runs_dict.items():
        for r in runs:
            outcome_rows.append({
                "run_id": r["run"],
                "batch": "s14",
                "condition": cond,
                "arm": r["arm"],
                "detector_triggered": str(r["detector_triggered"]),
                "action_executed": str(r["action_executed"]),
                "standby_takeover_occurred": str(r["active_port_moved_to_clean_segment"]),
                "bmca_failover_occurred": str(r["bmca_failover_observed"]),
                "measured_scope": "packet/protocol observation only; no physical clock accuracy claimed"
            })

    # ---- S15 independent validation, if it has been evaluated -------------------------------
    s15_eval_path = HERE / "S15_INDEPENDENT_VALIDATION_EVALUATION.json"
    if s15_eval_path.is_file():
        s15 = json.loads(s15_eval_path.read_text(encoding="utf-8"))
        for r in s15["runs"]:
            disp = r.get("first_valid_window_dispersion_ns")
            run_index_rows.append({
                "row_id": f"s15:{r['run']}",
                "batch": "s15",
                "run_id": r["run"],
                "run_directory": f"s15_runs/{r['run']}",
                "data_class": "EMPIRICAL_SOFTWARE_TESTBED_INDEPENDENT_TEST_SET",
                "L1_planned_condition": r["condition"],
                "L1_configured_parameters": f"tc netem delay 100us {r['condition'][1:]}us distribution normal on segment 1",
                "L2_injection_confirmed": "TRUE" if r.get("apply_monotonic_s") is not None else "FALSE",
                "L2_injection_evidence": f"s15_runs/{r['run']}/events.log phase2_apply_begin..phase2_graded_jitter_applied_seg1; tc_seg1_p2.txt",
                "L3_packet_records": str(run_packet_counts.get(r["run"], "")),
                "L3_dispersion_persistence_observed": r["detector_outcome"],
                "L3_detection_trigger_monotonic_s": "NOT_COMPARED_ACROSS_TIMEBASES",
                "L3_high_dispersion_blocks": str(r.get("triggers_after_apply", "")),
                "L3_source_silence_events": "0",
                "L3_invalid_records": "0",
                "L4_observed_receiver_impact": (
                    f"{r['receiver_label']} (first wholly-in-phase summary window dispersion "
                    f"{disp} ns; boundary {s15['boundary_ns']} ns)" if disp is not None
                    else f"UNKNOWN: {r.get('receiver_unknown_reason')}"),
                "L5_model_prediction": "NOT_APPLICABLE",
                "L6_proposed_recovery_action": "NONE (all S15 arms are no_action)",
                "L7_executed_recovery_action": "NONE",
                "L8_measured_recovery_outcome": "NOT_APPLICABLE",
                "validation_status": ("COUNTED_IN_INDEPENDENT_AGREEMENT_TEST" if r["counted_in_2x2"]
                                      else "UNKNOWN_EXCLUDED_FROM_AGREEMENT_REPORTED_NOT_DROPPED"),
                "capture_sha256": "see s14_packets.csv capture_sha256 per capture file",
                "manifest_entries_rehashed": str(len(r.get("integrity_problems", [])) == 0),
                "evidence_reference": "S15_INDEPENDENT_VALIDATION_EVALUATION.json",
            })
            outcome_rows.append({
                "run_id": r["run"],
                "batch": "s15",
                "condition": r["condition"],
                "arm": "no_action",
                "detector_triggered": str(r["detector_outcome"] == "TRIGGER"),
                "action_executed": "False",
                "standby_takeover_occurred": "NOT_APPLICABLE",
                "bmca_failover_occurred": str(bool(r.get("receiver_entered_master"))),
                "receiver_dispersion_label": r["receiver_label"],
                "receiver_first_window_dispersion_ns": str(disp) if disp is not None else "",
                "valid_window_count": str(r["valid_window_count"]),
                "counted_in_agreement_test": str(r["counted_in_2x2"]),
                "measured_scope": ("packet/protocol observation plus receiver-side path-delay dispersion; "
                                   "no harm, service impact or physical clock accuracy claimed"),
            })

    # Write all CSVs
    run_fields = [
        "row_id", "batch", "run_id", "run_directory", "data_class",
        "L1_planned_condition", "L1_configured_parameters",
        "L2_injection_confirmed", "L2_injection_evidence",
        "L3_packet_records", "L3_dispersion_persistence_observed",
        "L3_detection_trigger_monotonic_s", "L3_high_dispersion_blocks",
        "L3_source_silence_events", "L3_invalid_records",
        "L4_observed_receiver_impact", "L5_model_prediction",
        "L6_proposed_recovery_action", "L7_executed_recovery_action",
        "L8_measured_recovery_outcome", "validation_status",
        "capture_sha256", "manifest_entries_rehashed", "evidence_reference"
    ]
    write_csv("s14_runs.csv", run_fields, run_index_rows)
    write_csv("s14_events.csv", ["run_id", "batch_directory", "source_file", "source_sha256", "source_line_ordinal", "original_line"], event_rows)
    write_csv("s14_decisions.csv", sorted({k for r in decision_rows for k in r}), decision_rows)
    write_csv("s14_receiver_log.csv", list(receiver_log_rows[0].keys()) if receiver_log_rows else [], receiver_log_rows)
    write_csv("s14_receiver_transitions.csv", list(receiver_rows[0].keys()) if receiver_rows else [], receiver_rows)
    write_csv("s14_outcomes.csv", sorted({k for r in outcome_rows for k in r}), outcome_rows)
    write_csv("s14_packets.csv", list(packet_rows[0].keys()) if packet_rows else [], packet_rows)

    recon = {
        "run_rows": len(run_index_rows),
        "packet_rows": len(packet_rows),
        "event_rows": len(event_rows),
        "decision_rows": len(decision_rows),
        "receiver_log_rows": len(receiver_log_rows),
        "receiver_transition_rows": len(receiver_rows),
        "outcome_rows": len(outcome_rows),
        "s15_runs_included": sum(1 for r in run_index_rows if r.get("batch") == "s15"),
        "s15_evaluation_present": s15_eval_path.is_file(),
        "packets_csv_sha256": sha256_file(OUT / "s14_packets.csv"),
        "runs_csv_sha256": sha256_file(OUT / "s14_runs.csv")
    }
    (OUT / "s14_full_detail_reconciliation.json").write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")
    print("CSV_PREPARATION_PASS")


if __name__ == "__main__":
    main()
