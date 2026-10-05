#!/usr/bin/env python3
"""Discriminator for configured network impairment in empirical pilot runs.

Detects a CONFIGURED IMPAIRMENT (netem delay/jitter/loss), NOT an attack.
Pure standard library only.
"""

import json
import math
import random
import re
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "outputs" / "empirical_software_network_pilot_v1" / "runs"
OUTPUT_DIR = REPO_ROOT / "outputs" / "empirical_software_network_pilot_v1"

PROHIBITED_LEAKAGE_TOKENS = [
    "netem",
    "baseline",
    "control",
    "intervention",
    "set2",
    "set3",
    "r1",
    "r2",
    "r3",
    "r4",
    "r5",
    "r6",
    "r7",
    "r8",
]

def extract_features_from_pcap(file_obj, *prohibited_args, **prohibited_kwargs):
    """Extract packet timing features from an open binary file object.
    
    Leakage guard:
    - Rejects any argument that contains directory or condition tokens.
    - Operates strictly on raw file bytes from file_obj.
    """
    assert len(prohibited_args) == 0, "No positional arguments beyond file_obj permitted"
    assert len(prohibited_kwargs) == 0, "No keyword arguments permitted"
    
    # Assert string representation of file_obj does not leak condition or run identifiers
    arg_str = str(file_obj).lower()
    for token in PROHIBITED_LEAKAGE_TOKENS:
        assert token not in arg_str, f"LEAKAGE GUARD FAILURE: token '{token}' found in argument string representation: {arg_str}"

    if hasattr(file_obj, "read"):
        data = file_obj.read()
    else:
        raise TypeError(f"file_obj must be an open binary file object, got {type(file_obj)}")

    assert len(data) >= 24, "PCAP data too short"
    magic = struct.unpack("<I", data[:4])[0]
    endian = "<" if magic in (0xA1B2C3D4, 0xA1B23C4D) else ">"
    ts_factor = 1e6 if magic in (0xA1B2C3D4, 0xD4C3B2A1) else 1e9

    offset = 24
    pkts = []
    while offset + 16 <= len(data):
        hdr = data[offset : offset + 16]
        ts_sec, ts_sub, incl_len, orig_len = struct.unpack(f"{endian}IIII", hdr)
        ts = ts_sec + (ts_sub / ts_factor)
        offset += 16
        pkt_data = data[offset : offset + incl_len]
        offset += incl_len
        if len(pkt_data) < 14:
            continue
        if struct.unpack(">H", pkt_data[12:14])[0] != 0x88F7:
            continue
        ptp = pkt_data[14:]
        if len(ptp) < 34:
            continue
        msg_type_code = ptp[0] & 0x0F
        seq_id = struct.unpack(">H", ptp[30:32])[0]
        src_mac = ":".join(f"{b:02x}" for b in pkt_data[6:12])
        pkts.append({
            "ts": ts,
            "msg_type_code": msg_type_code,
            "seq_id": seq_id,
            "src_mac": src_mac,
        })

    # Manipulation check: missing_master_to_slave_seq_count
    streams = {}
    for pkt in pkts:
        streams.setdefault((pkt["src_mac"], pkt["msg_type_code"]), []).append(pkt["seq_id"])
    
    missing_seq_count = 0
    for (src, msg), seqs in streams.items():
        if msg == 1:  # Delay_Req (slave to bridge)
            continue
        first_seq = seqs[0]
        last_seq = seqs[-1]
        span = (last_seq - first_seq) % 65536 + 1
        observed_set = set(seqs)
        missing = [s for s in [(first_seq + i) % 65536 for i in range(span)] if s not in observed_set]
        missing_seq_count += len(missing)

    # Detection Feature 1: sync_fu_paired_delay_std_s
    sync_pkts = [pkt for pkt in pkts if pkt["msg_type_code"] == 0]
    fu_pkts = [pkt for pkt in pkts if pkt["msg_type_code"] == 8]
    fu_map = {(pkt["src_mac"], pkt["seq_id"]): pkt["ts"] for pkt in fu_pkts}
    delays = [fu_map[k] - sp["ts"] for sp in sync_pkts if (k := (sp["src_mac"], sp["seq_id"])) in fu_map]
    if delays:
        mean_d = sum(delays) / len(delays)
        sync_fu_delay_std = math.sqrt(sum((d - mean_d) ** 2 for d in delays) / len(delays))
    else:
        sync_fu_delay_std = 0.0

    # Detection Feature 2: sync_interarrival_jitter_s
    sync_by_mac = {}
    for pkt in sync_pkts:
        sync_by_mac.setdefault(pkt["src_mac"], []).append(pkt["ts"])
    max_src_mean_jitter = 0.0
    for ts_list in sync_by_mac.values():
        if len(ts_list) > 1:
            gaps = [ts_list[i] - ts_list[i-1] for i in range(1, len(ts_list))]
            jitter = [abs(g - 0.125) for g in gaps if g < 0.2]
            if jitter:
                m_jit = sum(jitter) / len(jitter)
                if m_jit > max_src_mean_jitter:
                    max_src_mean_jitter = m_jit

    return {
        "missing_master_to_slave_seq_count": missing_seq_count,
        "sync_fu_paired_delay_std_s": round(sync_fu_delay_std, 8),
        "sync_interarrival_jitter_s": round(max_src_mean_jitter, 8),
    }

def run_leave_one_out(dataset, feature_name):
    n = len(dataset)
    predictions = []
    
    for i in range(n):
        test_item = dataset[i]
        train_items = [dataset[j] for j in range(n) if j != i]
        
        train_pos = [item["features"][feature_name] for item in train_items if item["y"] == 1]
        train_neg = [item["features"][feature_name] for item in train_items if item["y"] == 0]
        
        all_train_vals = sorted(list(set(train_pos + train_neg)))
        candidate_thresholds = []
        if all_train_vals:
            candidate_thresholds.append(all_train_vals[0] - 1.0)
            for k in range(len(all_train_vals) - 1):
                candidate_thresholds.append((all_train_vals[k] + all_train_vals[k+1]) / 2.0)
            candidate_thresholds.append(all_train_vals[-1] + 1.0)
            
        best_th = candidate_thresholds[0]
        best_train_acc = -1
        
        for th in candidate_thresholds:
            correct = sum(
                1 for item in train_items
                if ((item["features"][feature_name] >= th) == (item["y"] == 1))
            )
            if correct > best_train_acc:
                best_train_acc = correct
                best_th = th
                
        test_feat = test_item["features"][feature_name]
        pred_y = 1 if test_feat >= best_th else 0
        predictions.append({
            "run": test_item["run"],
            "actual": test_item["y"],
            "predicted": pred_y,
            "threshold_chosen_on_train": best_th,
            "test_feature_value": test_feat,
        })
        
    correct_count = sum(1 for p in predictions if p["actual"] == p["predicted"])
    tp = sum(1 for p in predictions if p["actual"] == 1 and p["predicted"] == 1)
    tn = sum(1 for p in predictions if p["actual"] == 0 and p["predicted"] == 0)
    fp = sum(1 for p in predictions if p["actual"] == 0 and p["predicted"] == 1)
    fn = sum(1 for p in predictions if p["actual"] == 1 and p["predicted"] == 0)
    
    accuracy = correct_count / n if n > 0 else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    return {
        "feature": feature_name,
        "accuracy": round(accuracy, 6),
        "sensitivity": round(sensitivity, 6),
        "specificity": round(specificity, 6),
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "predictions": predictions,
    }

def run_permutation_test(dataset, feature_name, num_permutations=1000, seed=42):
    rng = random.Random(seed)
    actual_res = run_leave_one_out(dataset, feature_name)
    actual_acc = actual_res["accuracy"]
    
    labels = [item["y"] for item in dataset]
    count_equal_or_better = 0
    perm_accuracies = []
    
    for _ in range(num_permutations):
        shuffled_labels = list(labels)
        rng.shuffle(shuffled_labels)
        perm_dataset = [
            {"run": dataset[i]["run"], "y": shuffled_labels[i], "features": dataset[i]["features"]}
            for i in range(len(dataset))
        ]
        res = run_leave_one_out(perm_dataset, feature_name)
        perm_accuracies.append(res["accuracy"])
        if res["accuracy"] >= actual_acc:
            count_equal_or_better += 1
            
    p_value = count_equal_or_better / num_permutations
    return {
        "num_permutations": num_permutations,
        "seed": seed,
        "actual_accuracy": actual_acc,
        "permutation_p_value": round(p_value, 6),
        "perm_accuracy_max": max(perm_accuracies),
        "perm_accuracy_mean": round(sum(perm_accuracies) / len(perm_accuracies), 6),
    }

def compute_class_distribution_stats(dataset, feat):
    pos = [item["features"][feat] for item in dataset if item["y"] == 1]
    neg = [item["features"][feat] for item in dataset if item["y"] == 0]
    pos.sort()
    neg.sort()
    pos_med = pos[len(pos) // 2] if len(pos) % 2 == 1 else (pos[len(pos) // 2 - 1] + pos[len(pos) // 2]) / 2.0
    neg_med = neg[len(neg) // 2] if len(neg) % 2 == 1 else (neg[len(neg) // 2 - 1] + neg[len(neg) // 2]) / 2.0
    margin = pos[0] - neg[-1]
    ratio = pos_med / neg_med if neg_med > 0 else 0.0
    return {
        "positive_class_netem": {
            "n": len(pos),
            "min": round(pos[0], 8),
            "median": round(pos_med, 8),
            "max": round(pos[-1], 8),
        },
        "negative_class_unimpaired": {
            "n": len(neg),
            "min": round(neg[0], 8),
            "median": round(neg_med, 8),
            "max": round(neg[-1], 8),
        },
        "separation_margin_lowest_pos_minus_highest_neg": round(margin, 8),
        "ratio_of_class_medians": round(ratio, 6),
    }

def main():
    candidate_dirs = sorted([d for d in RUNS_DIR.glob("*") if d.is_dir()])
    dataset = []
    
    for d in candidate_dirs:
        dname = d.name
        if not ("set2" in dname or "set3" in dname):
            continue
        if "intervention" in dname:
            continue
            
        pcap_path = d / "capture.pcap"
        if not pcap_path.exists():
            continue
            
        is_netem = 1 if "netem" in dname else 0
        
        # Leakage guard: read bytes into an anonymous BytesIO object so no path or directory string is visible
        import io
        with open(pcap_path, "rb") as pf:
            pcap_bytes = pf.read()
        file_obj = io.BytesIO(pcap_bytes)
        
        feats = extract_features_from_pcap(file_obj)
        dataset.append({
            "run": dname,
            "y": is_netem,
            "condition": "netem_delay_jitter_loss" if is_netem == 1 else ("baseline_control" if "baseline" in dname else "authorized_source_change_no_action_control"),
            "features": feats,
        })
        
    # Separate manipulation check from detection features
    manipulation_check_feat = "missing_master_to_slave_seq_count"
    detection_feats = [
        "sync_fu_paired_delay_std_s",
        "sync_interarrival_jitter_s",
    ]
    
    # 1. Evaluate manipulation check
    loo_man = run_leave_one_out(dataset, manipulation_check_feat)
    perm_man = run_permutation_test(dataset, manipulation_check_feat, num_permutations=1000, seed=42)
    stats_man = compute_class_distribution_stats(dataset, manipulation_check_feat)
    
    manipulation_check_result = {
        "role": "MANIPULATION_CHECK",
        "statement": "missing_master_to_slave_seq_count directly counts the frames the configured loss removed. It confirms the impairment was delivered to the bridge-to-slave queue. Separating runs by counting the packets the injection removed is a delivery validation, NOT evidence of a detection capability.",
        "distribution_and_margins": stats_man,
        "leave_one_out": loo_man,
        "permutation_control": perm_man,
    }
    
    # 2. Evaluate detection features
    detection_results = {}
    for feat in detection_feats:
        loo_det = run_leave_one_out(dataset, feat)
        perm_det = run_permutation_test(dataset, feat, num_permutations=1000, seed=42)
        stats_det = compute_class_distribution_stats(dataset, feat)
        detection_results[feat] = {
            "role": "DETECTION_FEATURE",
            "distribution_and_margins": stats_det,
            "leave_one_out": loo_det,
            "permutation_control": perm_det,
        }
        
    output_data = {
        "schema_version": "empirical-configured-impairment-discriminator-v2",
        "evaluation_scope": {
            "target": "CONFIGURED IMPAIRMENT",
            "mandatory_disclaimer": "Detects a CONFIGURED IMPAIRMENT (netem delay/jitter/loss), NOT an attack.",
            "unit_of_analysis": "1 run",
            "positive_class": "netem_delay_jitter_loss",
            "negative_class": ["baseline_control", "authorized_source_change_no_action_control"],
            "excluded_conditions": {
                "authorized_source_change_intervention": "Excluded because intervention is an intentional grandmaster termination / source change rather than an in-path link impairment."
            },
            "sample_counts": {
                "total_runs_evaluated": len(dataset),
                "positive_runs": sum(1 for item in dataset if item["y"] == 1),
                "negative_runs": sum(1 for item in dataset if item["y"] == 0),
                "class_ratio_neg_to_pos": f"{sum(1 for item in dataset if item['y'] == 0)}:{sum(1 for item in dataset if item['y'] == 1)}",
            },
            "anti_circularity_design": "Run class assignment is fixed by the experiment configuration and confirmed by physical qdisc counters, completely independent of packet timing features.",
            "leakage_guard": "extract_features_from_pcap accepts an anonymous binary stream with assertions failing loudly if directory or scenario names are passed.",
        },
        "feature_selection_provenance": {
            "feature_set_status": "POST_SPECIFIED_SUBSTITUTION",
            "features_originally_specified": [
                "per-source Announce inter-arrival median, p95, max, and standard deviation",
                "per-source missing sequence fraction by messageType",
                "total frame count normalised by capture duration",
                "Delay_Req inter-arrival median and p95"
            ],
            "features_explored_before_selection": [
                "raw_all_source_sync_interarrival_std",
                "slave_delay_req_outage_for_netem",
                "sync_fu_paired_delay_std_s",
                "sync_interarrival_jitter_s",
                "missing_master_to_slave_seq_count"
            ],
            "selection_note": "The two detection features (sync_fu_paired_delay_std_s and sync_interarrival_jitter_s) were chosen after exploring candidate wire-level metrics and observing their empirical separation between impaired and unimpaired runs.",
            "features_actually_evaluated": [
                "missing_master_to_slave_seq_count (reclassified as MANIPULATION_CHECK)",
                "sync_fu_paired_delay_std_s (DETECTION_FEATURE: paired transmit latency dispersion under two-step profile)",
                "sync_interarrival_jitter_s (DETECTION_FEATURE: nominal 125 ms interval mean absolute deviation)"
            ],
            "substitution_rationale": "Historical session features relied on window-level packet projections that were circular with session labels. The empirical pilot provides an independent run-level ground truth (netem injection confirmed by qdisc drop telemetry). Features were designed directly from the physical IEEE 1588 protocol mechanics present on the wire (sequence ID increments, two-step Sync-Follow_Up pairing, and nominal 8 Hz message pacing).",
            "features_tried_and_discarded": [
                {
                    "feature": "raw_all_source_sync_interarrival_std",
                    "reason_discarded": "Aggregated Sync arrival timestamps across both Master A and Master B, conflating multi-source scheduling offsets with link jitter. Replaced by per-source deviation from the nominal 125 ms cadence (sync_interarrival_jitter_s)."
                },
                {
                    "feature": "slave_delay_req_outage_for_netem",
                    "reason_discarded": "Delay_Req frames traverse slave->bridge egress where netem was not configured. As established by netem direction-match, netem impairs only bridge->slave egress. Packet outage metrics are relevant to master termination (intervention), not link delay/loss impairment."
                }
            ]
        },
        "dataset_inventory": dataset,
        "manipulation_check": manipulation_check_result,
        "detection_features": detection_results,
    }
    
    out_file = OUTPUT_DIR / "DISCRIMINATOR_RESULTS.json"
    out_file.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    print(f"Wrote discriminator results to {out_file}")

if __name__ == "__main__":
    main()
