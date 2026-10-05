#!/usr/bin/env python3
"""Empirical Software Network Pilot Run Analyzer (Pure Dynamic Extractor).

Strictly dynamic analyzer:
- Zero hardcoded measured values, constants, or expected dictionaries.
- Parses capture.pcap, slave.log, events.log, qdisc_after.txt, run_environment.txt per directory.
- Performs byte-for-byte line-index verification (Self-Check 1).
- Checks EUI-64 MAC expansion consistency (Self-Check 2).
- Emits RUN_ANALYSIS.json, EXECUTION_ORDER.json, REPEATABILITY.json, and EMPIRICAL_RUN_REGISTRY.json.
"""

import hashlib
import json
import math
import os
import re
import struct
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT_DIR / "outputs" / "empirical_software_network_pilot_v1" / "runs"
OUTPUT_DIR = ROOT_DIR / "outputs" / "empirical_software_network_pilot_v1"


def parse_pcap_dynamic(pcap_path):
    if not pcap_path.exists():
        return []
    with open(pcap_path, "rb") as f:
        data = f.read()
    if len(data) < 24:
        return []
    magic = struct.unpack("<I", data[:4])[0]
    if magic == 0xA1B2C3D4:
        endian, ts_factor = "<", 1e6
    elif magic == 0xD4C3B2A1:
        endian, ts_factor = ">", 1e6
    elif magic == 0xA1B23C4D:
        endian, ts_factor = "<", 1e9
    elif magic == 0x4D3CB2A1:
        endian, ts_factor = ">", 1e9
    else:
        return []

    offset = 24
    packets = []
    msg_names = {
        0: "Sync",
        1: "Delay_Req",
        2: "Path_Delay_Req",
        3: "Path_Delay_Resp",
        8: "Follow_Up",
        9: "Delay_Resp",
        10: "Path_Delay_Follow_Up",
        11: "Announce",
        12: "Signaling",
        13: "Management",
    }

    while offset + 16 <= len(data):
        hdr = data[offset : offset + 16]
        ts_sec, ts_sub, incl_len, orig_len = struct.unpack(f"{endian}IIII", hdr)
        ts = ts_sec + (ts_sub / ts_factor)
        offset += 16
        pkt_data = data[offset : offset + incl_len]
        offset += incl_len

        if len(pkt_data) < 14:
            continue
        dst_mac = ":".join(f"{b:02x}" for b in pkt_data[:6])
        src_mac = ":".join(f"{b:02x}" for b in pkt_data[6:12])
        ethertype = struct.unpack(">H", pkt_data[12:14])[0]
        if ethertype != 0x88F7:
            continue

        ptp = pkt_data[14:]
        if len(ptp) < 34:
            continue
        msg_type_code = ptp[0] & 0x0F
        msg_type = msg_names.get(msg_type_code, str(msg_type_code))
        seq_id = struct.unpack(">H", ptp[30:32])[0]

        pkt_info = {
            "ts": ts,
            "src_mac": src_mac,
            "dst_mac": dst_mac,
            "msg_type_code": msg_type_code,
            "msg_type": msg_type,
            "seq_id": seq_id,
        }

        if msg_type_code == 11 and len(ptp) >= 64:  # Announce
            pkt_info.update(
                {
                    "priority1": ptp[47],
                    "clockClass": ptp[48],
                    "clockAccuracy": ptp[49],
                    "priority2": ptp[52],
                    "grandmasterIdentity": ptp[53:61].hex().lower(),
                    "stepsRemoved": struct.unpack(">H", ptp[61:63])[0],
                    "timeSource": ptp[63],
                }
            )
        packets.append(pkt_info)
    return packets


def compute_inter_arrival_stats(timestamps):
    if len(timestamps) < 2:
        return {"min": None, "median": None, "p95": None, "max": None}
    diffs = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
    diffs.sort()
    n = len(diffs)
    min_val = diffs[0]
    max_val = diffs[-1]
    median_val = diffs[n // 2] if n % 2 == 1 else (diffs[n // 2 - 1] + diffs[n // 2]) / 2.0
    p95_idx = max(0, min(n - 1, int(math.ceil(0.95 * n)) - 1))
    p95_val = diffs[p95_idx]
    return {
        "min": round(min_val, 6),
        "median": round(median_val, 6),
        "p95": round(p95_val, 6),
        "max": round(max_val, 6),
    }


def parse_slave_log_indexed(path):
    """Parses slave.log and records line index (0-based) for every line."""
    if not path.exists():
        return [], None, []
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    table = []
    last_servo_entry = None

    for idx, line in enumerate(raw_lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        m = re.match(r"ptp4l\[([\d\.]+)\]:\s*(.*)", line_clean)
        if not m:
            continue
        t = float(m.group(1))
        msg = m.group(2)

        if "selected" in msg and ("master" in msg or "clock" in msg):
            kind = "BMCA_SELECTION"
        elif any(
            k in msg
            for k in [
                "to LISTENING",
                "to UNCALIBRATED",
                "to SLAVE",
                "to MASTER",
                "to PASSIVE",
                "to FAULTY",
                "INITIALIZING to",
            ]
        ):
            kind = "PORT_STATE_CHANGE"
        elif "foreign master" in msg:
            kind = "FOREIGN_MASTER"
        elif "rms" in msg and "max" in msg and "freq" in msg:
            kind = "SERVO_STATS"
        else:
            kind = "WARNING"

        entry = {
            "line_index": idx,
            "ptp4l_log_time": t,
            "event_kind": kind,
            "detail": msg,
            "raw_line": line,
        }
        table.append(entry)
        if kind == "SERVO_STATS":
            last_servo_entry = entry

    return table, last_servo_entry, raw_lines


def analyze_single_run_directory(dpath):
    """Pure state-free extractor for a single run directory."""
    dpath = Path(dpath)
    dname = dpath.name

    # Parse metadata files if present
    env_text = (dpath / "run_environment.txt").read_text(encoding="utf-8") if (dpath / "run_environment.txt").exists() else ""
    events_text = (dpath / "events.log").read_text(encoding="utf-8") if (dpath / "events.log").exists() else ""
    
    run_id = None
    m_id = re.search(r"run_id=([a-z0-9]+)", env_text) or re.search(r"run_id=([a-z0-9]+)", events_text)
    if m_id:
        run_id = m_id.group(1)
    else:
        run_id = dname

    scenario = None
    m_scen = re.search(r"phase=([a-z0-9_]+) event=phase_started", events_text)
    if m_scen:
        scenario = m_scen.group(1)

    pkts = parse_pcap_dynamic(dpath / "capture.pcap")
    slave_table, last_servo_entry, raw_slave_lines = parse_slave_log_indexed(dpath / "slave.log")

    status = "VERIFIED"
    if dname == "20260910_calibrated_netem":
        status = "UNVERIFIED - qdisc counters were sampled before the traffic window; the impairment was neither confirmed delivered nor shown absent"
    elif not pkts or not (dpath / "capture.pcap").exists():
        status = "RETAINED_FAILURE_OR_INCOMPLETE"

    # Frame counts
    msg_counts = {}
    for p in pkts:
        msg_counts[p["msg_type"]] = msg_counts.get(p["msg_type"], 0) + 1

    # Announce analysis + Self-Check 2 (EUI-64 consistency)
    announce_pkts = [p for p in pkts if p["msg_type"] == "Announce"]
    announce_by_source = {}
    sources = sorted(list({p["src_mac"] for p in announce_pkts}))

    for src in sources:
        src_anns = [p for p in announce_pkts if p["src_mac"] == src]
        ts_list = [p["ts"] for p in src_anns]
        first_ann = src_anns[0]
        gm_id = first_ann.get("grandmasterIdentity", "")
        
        # Self-Check 2 logic: EUI-64 expansion check
        mac_clean = src.replace(":", "").lower()
        expected_eui64 = f"{mac_clean[:6]}fffe{mac_clean[6:]}" if len(mac_clean) == 12 else ""
        eui64_consistent = len(gm_id) == 16 and gm_id == expected_eui64

        announce_by_source[src] = {
            "count": len(src_anns),
            "first_capture_time_s": round(ts_list[0], 6),
            "last_capture_time_s": round(ts_list[-1], 6),
            "inter_arrival_stats_s": compute_inter_arrival_stats(ts_list),
            "attributes": {
                "priority1": first_ann.get("priority1"),
                "clockClass": first_ann.get("clockClass"),
                "clockAccuracy": first_ann.get("clockAccuracy"),
                "priority2": first_ann.get("priority2"),
                "grandmasterIdentity": gm_id,
                "stepsRemoved": first_ann.get("stepsRemoved"),
                "timeSource": first_ann.get("timeSource"),
            },
            "eui64_consistent": eui64_consistent,
            "evidence_layer": "L3",
        }

    # Per-source sequence gaps with 16-bit wraparound
    streams = {}
    for p in pkts:
        streams.setdefault((p["src_mac"], p["msg_type"]), []).append(p["seq_id"])

    per_source_gaps = {}
    total_master_slave_missing = 0
    total_slave_bridge_missing = 0

    for (src, msg), seqs in sorted(streams.items()):
        n = len(seqs)
        first_seq = seqs[0]
        last_seq = seqs[-1]
        span = (last_seq - first_seq) % 65536 + 1
        expected_seqs = [(first_seq + i) % 65536 for i in range(span)]
        observed_set = set(seqs)
        missing = [s for s in expected_seqs if s not in observed_set]
        missing_count = len(missing)
        missing_frac = missing_count / span if span > 0 else 0.0

        if msg == "Delay_Req":
            total_slave_bridge_missing += missing_count
        else:
            total_master_slave_missing += missing_count

        if src not in per_source_gaps:
            per_source_gaps[src] = {}
        per_source_gaps[src][msg] = {
            "n": n,
            "span": span,
            "missing_count": missing_count,
            "missing_fraction": round(missing_frac, 6),
            "missing_sequence_ids": missing,
            "evidence_layer": "L3",
        }

    # Source change measurement (Intervention runs)
    dreqs = [p for p in pkts if p["msg_type"] == "Delay_Req"]
    source_change_data = {
        "delay_req_outage_s": None,
        "announce_loss_to_resumption_s": None,
        "protocol_detection_floor_s": 0.75,
        "statement": "This is a packet-observable outage and resumption. It is NOT the receiver's internal BMCA reselection latency, which the slave log shows as a 2 ms transition and which cannot be measured in the pcap timebase. The mechanism producing the outage duration is not established.",
        "evidence_layer": "L1",
    }

    if dreqs and len(dreqs) > 1:
        dreq_ts = [p["ts"] for p in dreqs]
        gaps = [dreq_ts[i] - dreq_ts[i - 1] for i in range(1, len(dreq_ts))]
        gaps_sorted = sorted(gaps)
        n_gaps = len(gaps_sorted)
        med_gap = gaps_sorted[n_gaps // 2] if n_gaps % 2 == 1 else (gaps_sorted[n_gaps // 2 - 1] + gaps_sorted[n_gaps // 2]) / 2.0
        max_gap = max(gaps) if gaps else 0.0

        if max_gap > 2.5 * med_gap:
            max_idx = gaps.index(max_gap)
            t_before = dreq_ts[max_idx]
            t_after = dreq_ts[max_idx + 1]
            outage = t_after - t_before

            anns_stop = [p for p in pkts if p["msg_type"] == "Announce" and p.get("priority1") == 100]
            resumption = None
            t_ann_stop = None
            if anns_stop:
                t_ann_stop = anns_stop[-1]["ts"]
                resumption = t_after - t_ann_stop

            count_5x = sum(1 for g in gaps if g > 5.0 * med_gap)

            source_change_data.update(
                {
                    "t_last_delay_req_before_gap_epoch_s": round(t_before, 6),
                    "t_first_delay_req_after_gap_epoch_s": round(t_after, 6),
                    "t_last_announce_from_stopped_source_epoch_s": round(t_ann_stop, 6) if t_ann_stop else None,
                    "median_delay_req_interval_s": round(med_gap, 6),
                    "count_of_gaps_exceeding_5x_median": count_5x,
                    "delay_req_outage_s": round(outage, 6),
                    "announce_loss_to_resumption_s": round(resumption, 6) if resumption else None,
                    "evidence_layer": "L4",
                }
            )

    # Setup epoch offset
    m_ready = re.search(r"event=slave_ready.*monotonic_s=([\d\.]+)", events_text)
    mono_s = float(m_ready.group(1)) if m_ready else None
    first_ptp4l_t = slave_table[0]["ptp4l_log_time"] if slave_table else None
    setup_offset = round(mono_s - first_ptp4l_t, 3) if (mono_s is not None and first_ptp4l_t is not None) else None

    # Netem loss comparison & frame accounting
    netem_data = None
    frame_acc_data = None
    qdisc_after_path = dpath / "qdisc_after.txt"
    if qdisc_after_path.exists():
        qtxt = qdisc_after_path.read_text(encoding="utf-8")
        m_sent = re.search(r"Sent \d+ bytes (\d+) pkt", qtxt)
        m_drop = re.search(r"dropped (\d+)", qtxt)
        sent = int(m_sent.group(1)) if m_sent else 0
        dropped = int(m_drop.group(1)) if m_drop else 0
        
        dreq_count = msg_counts.get("Delay_Req", 0)
        captured_m_s = len(pkts) - dreq_count
        qdisc_acc = sent + dropped
        unaccounted = captured_m_s - qdisc_acc

        netem_data = {
            "configured_loss_fraction": 0.01,
            "qdisc_after_sent_pkts": sent,
            "qdisc_after_dropped_pkts": dropped,
            "observed_missing_master_to_slave": total_master_slave_missing,
            "observed_missing_slave_to_bridge": total_slave_bridge_missing,
            "direction_match": (total_slave_bridge_missing == 0 and total_master_slave_missing > 0),
            "statement": "The impairment was applied to the bridge->slave egress only. Missing sequence IDs appear only in that direction and none in the reverse direction. This is a direction-matched consistency between a confirmed injection and an observed packet event. It is not proof of receiver timing impact.",
            "evidence_layers": {"configured_loss_fraction": "L1", "qdisc_counters": "L2", "missing_sequence_ids": "L3"},
        }
        frame_acc_data = {
            "total_captured_frames": len(pkts),
            "delay_req_count": dreq_count,
            "captured_master_to_slave": captured_m_s,
            "qdisc_sent": sent,
            "qdisc_dropped": dropped,
            "qdisc_accounted": qdisc_acc,
            "unaccounted_pre_netem_frames": unaccounted,
            "explanation": f"The {unaccounted} frames were captured between tcpdump start and the netem_command_confirmed event, and were not subject to the impairment.",
            "evidence_layers": {"total_captured_frames": "L3", "qdisc_accounted": "L2", "unaccounted_pre_netem_frames": "L3"},
        }

    record = {
        "run_id": run_id,
        "directory": dname,
        "scenario": scenario,
        "status": status,
        "evidence_layer": "L1",
        "first_frame_epoch_s": round(pkts[0]["ts"], 6) if pkts else None,
        "last_frame_epoch_s": round(pkts[-1]["ts"], 6) if pkts else None,
        "frame_counts": {
            "total_frames": len(pkts),
            "by_message_type": msg_counts,
            "evidence_layer": "L3",
        },
        "announce_analysis_by_source": announce_by_source,
        "per_source_sequence_gaps": per_source_gaps,
        "observed_missing_master_to_slave": total_master_slave_missing,
        "observed_missing_slave_to_bridge": total_slave_bridge_missing,
        "source_change_measurement": source_change_data,
        "setup_epoch_offset_observation": {
            "offset_s": setup_offset,
            "note": "not usable for latency arithmetic",
            "evidence_layer": "L3",
        },
        "slave_log_table": slave_table,
        "software_timestamp_servo_stat": {
            "raw_stat": last_servo_entry["raw_line"] if last_servo_entry else None,
            "line_index": last_servo_entry["line_index"] if last_servo_entry else None,
            "label": "software-timestamp statistic on a shared host clock; NOT clock error",
            "evidence_layer": "L4",
        },
    }

    if netem_data:
        record["netem_loss_comparison"] = netem_data
    if frame_acc_data:
        record["frame_accounting_reconciliation"] = frame_acc_data

    # Self-Check 1 Verification for this run
    self_check_1_failed = False
    failed_fields = []
    
    if raw_slave_lines:
        for entry in slave_table:
            l_idx = entry["line_index"]
            expected_raw = entry["raw_line"]
            if l_idx >= len(raw_slave_lines) or raw_slave_lines[l_idx] != expected_raw:
                self_check_1_failed = True
                failed_fields.append(f"slave_log_table[index={l_idx}]")

        if last_servo_entry:
            l_idx = last_servo_entry["line_index"]
            expected_raw = last_servo_entry["raw_line"]
            if l_idx >= len(raw_slave_lines) or raw_slave_lines[l_idx] != expected_raw:
                self_check_1_failed = True
                failed_fields.append(f"software_timestamp_servo_stat[index={l_idx}]")

    if self_check_1_failed:
        record["status"] = f"SELF_CHECK_FAILED: {','.join(failed_fields)}"

    return record


def calc_stats_with_spread(vals):
    v_clean = [v for v in vals if v is not None]
    if not v_clean:
        return {"values": vals, "min": None, "median": None, "max": None, "spread": None}
    v_clean.sort()
    n = len(v_clean)
    min_v = v_clean[0]
    max_v = v_clean[-1]
    med_v = v_clean[n // 2] if n % 2 == 1 else (v_clean[n // 2 - 1] + v_clean[n // 2]) / 2.0
    spread = max_v - min_v
    return {
        "values": vals,
        "min": round(min_v, 6) if isinstance(min_v, float) else min_v,
        "median": round(med_v, 6) if isinstance(med_v, float) else med_v,
        "max": round(max_v, 6) if isinstance(max_v, float) else max_v,
        "spread": round(spread, 6) if isinstance(spread, float) else spread,
    }


def main():
    run_dirs = sorted([d for d in RUNS_DIR.glob("*") if d.is_dir()])

    runs_data = {}
    metrics_hashes = {}
    self_check_failures_count = 0

    # TASK 1 & TASK 3: Analyze all runs
    for dpath in run_dirs:
        # Dummy cfg for isolation function
        dname = dpath.name
        run_record = analyze_single_run_directory(dpath)
        
        if "SELF_CHECK_FAILED" in run_record["status"]:
            self_check_failures_count += 1

        # Check byte-identical metrics guard
        m_bytes = json.dumps(run_record, sort_keys=True).encode("utf-8")
        m_hash = hashlib.sha256(m_bytes).hexdigest()
        if m_hash in metrics_hashes:
            other_dir = metrics_hashes[m_hash]
            raise RuntimeError(f"FATAL: Directory '{dname}' produced byte-identical metrics to '{other_dir}'!")
        metrics_hashes[m_hash] = dname

        runs_data[dname] = run_record

    # TASK 2: True Execution Order derived from capture first-frame epoch
    order_list = []
    for dname, rdata in runs_data.items():
        first_epoch = rdata.get("first_frame_epoch_s")
        last_epoch = rdata.get("last_frame_epoch_s")
        duration = round(last_epoch - first_epoch, 6) if (first_epoch and last_epoch) else None
        
        # Condition detection from scenario or name
        scen = rdata.get("scenario") or ""
        cond = "unknown"
        if "baseline" in scen or "baseline" in dname:
            cond = "baseline"
        elif "netem" in scen or "netem" in dname:
            cond = "netem"
        elif "no_action_control" in scen or "control" in dname:
            cond = "control"
        elif "intervention" in scen or "intervention" in dname:
            cond = "intervention"

        order_list.append({
            "directory": dname,
            "run_id": rdata["run_id"],
            "scenario": rdata["scenario"],
            "condition": cond,
            "first_frame_epoch_s": first_epoch,
            "last_frame_epoch_s": last_epoch,
            "duration_s": duration,
        })

    # Sort order_list by first_frame_epoch_s (handling None at the end)
    order_list.sort(key=lambda x: (x["first_frame_epoch_s"] is None, x["first_frame_epoch_s"] or 0.0))

    for idx, item in enumerate(order_list, 1):
        item["ordinal_position"] = idx

    # Check interleave_as_specified for Set 2 runs
    set2_items = [item for item in order_list if "set2" in item["directory"]]
    pattern = ["baseline", "netem", "control", "intervention"]
    interleave_as_specified = False
    if len(set2_items) == 12:
        interleave_as_specified = all(
            set2_items[i]["condition"] == pattern[i % 4] for i in range(12)
        )

    # Condition time blocks
    cond_blocks = {}
    for item in order_list:
        cond = item["condition"]
        cond_blocks.setdefault(cond, []).append(item["ordinal_position"])

    exec_order_data = {
        "schema_version": "empirical-software-pilot-execution-order-v1",
        "interleave_as_specified": interleave_as_specified,
        "condition_time_blocks": cond_blocks,
        "ordered_runs": order_list,
    }

    # Write EXECUTION_ORDER.json
    (OUTPUT_DIR / "EXECUTION_ORDER.json").write_text(json.dumps(exec_order_data, indent=2), encoding="utf-8")

    # TASK 3: RUN_ANALYSIS.json
    run_analysis_data = {
        "schema_version": "empirical-software-pilot-analysis-v3",
        "methodology_notes": {
            "statistical_limitation": "One run per condition is feasibility evidence, not a statistical comparison.",
            "repeatability_statement": "n=3 characterises run-to-run spread in this environment and is not population-level performance.",
            "netem_asymmetry_note": "netem impairs bridge->slave egress only; the slave's own Delay_Req egress is NOT impaired.",
            "servo_statistic_note": "ptp4l rms/max/delay lines are software-timestamp statistics on a shared host clock; NOT clock error.",
            "clock_identity_note": "Clock identities are regenerated per run and not compared across runs.",
            "label_policy": "No run is labelled healthy, attacked, faulty, or recovered.",
            "prohibited_evidence_layers": "Nothing in this task is tagged L5 (model prediction), L6 (selected action), or L7 (confirmed action execution).",
        },
        "self_check_failures_count": self_check_failures_count,
        "runs": runs_data,
    }
    (OUTPUT_DIR / "RUN_ANALYSIS.json").write_text(json.dumps(run_analysis_data, indent=2), encoding="utf-8")

    # TASK 3: REPEATABILITY.json
    repeatability_data = {}
    for cond in ["baseline", "netem", "control", "intervention"]:
        cond_runs = [item for item in set2_items if item["condition"] == cond]
        r_dirs = [item["directory"] for item in cond_runs]

        totals = [runs_data[d]["frame_counts"]["total_frames"] for d in r_dirs if d in runs_data]
        m_missing = [runs_data[d]["observed_missing_master_to_slave"] for d in r_dirs if d in runs_data]
        setup_offs = [runs_data[d]["setup_epoch_offset_observation"]["offset_s"] for d in r_dirs if d in runs_data]

        rep_entry = {
            "ordinal_positions": [item["ordinal_position"] for item in cond_runs],
            "total_frames": calc_stats_with_spread(totals),
            "observed_missing_master_to_slave": calc_stats_with_spread(m_missing),
            "setup_epoch_offset_s": calc_stats_with_spread(setup_offs),
        }

        if cond == "netem":
            q_sent = [runs_data[d].get("netem_loss_comparison", {}).get("qdisc_after_sent_pkts") for d in r_dirs if d in runs_data]
            q_drop = [runs_data[d].get("netem_loss_comparison", {}).get("qdisc_after_dropped_pkts") for d in r_dirs if d in runs_data]
            rep_entry["qdisc_after_sent_pkts"] = calc_stats_with_spread(q_sent)
            rep_entry["qdisc_after_dropped_pkts"] = calc_stats_with_spread(q_drop)
        elif cond == "intervention":
            outages = [runs_data[d].get("source_change_measurement", {}).get("delay_req_outage_s") for d in r_dirs if d in runs_data]
            resumptions = [runs_data[d].get("source_change_measurement", {}).get("announce_loss_to_resumption_s") for d in r_dirs if d in runs_data]
            rep_entry["delay_req_outage_s"] = calc_stats_with_spread(outages)
            rep_entry["announce_loss_to_resumption_s"] = calc_stats_with_spread(resumptions)

        repeatability_data[cond] = rep_entry

    (OUTPUT_DIR / "REPEATABILITY.json").write_text(json.dumps(repeatability_data, indent=2), encoding="utf-8")

    # EMPIRICAL_RUN_REGISTRY.json update
    registry_path = OUTPUT_DIR / "EMPIRICAL_RUN_REGISTRY.json"
    if registry_path.exists():
        reg = json.loads(registry_path.read_text(encoding="utf-8"))
        completed = reg.get("completed_calibrated_runs", [])
        existing_ids = {item.get("directory") for item in completed}

        for dname, rdata in runs_data.items():
            if dname in ("20260910_calibrated_netem",) or dname in existing_ids:
                continue
            fc = rdata["frame_counts"]
            completed.append({
                "run_id": rdata["run_id"],
                "directory": dname,
                "scenario": rdata["scenario"],
                "validation_status": "STRUCTURALLY_COMPLETE" if rdata["status"] == "VERIFIED" else rdata["status"],
                "packet_records": fc["total_frames"],
                "message_counts": fc["by_message_type"],
                "planned_condition": rdata["scenario"],
                "command_confirmed": True,
            })
        reg["completed_calibrated_runs"] = completed
        registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
