from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUTPUT_FIELDS = [
    "t",
    "cell_id",
    "ue_id",
    "service_class",
    "fault_active",
    "fault_type",
    "aml_attack_active",
    "aml_attack_type",
    "latency_ms",
    "jitter_ms",
    "throughput_mbps",
    "packet_loss_pct",
    "prb_util_pct",
    "handover_fail_pct",
    "edge_delay_ms",
    "backhaul_delay_ms",
    "sinr_db",
    "bler_pct",
    "slice_id",
    "slice_prb",
    "scheduling_policy",
    "dl_cqi",
    "dl_mcs",
    "ul_mcs",
    "dl_buffer_bytes",
    "ul_buffer_bytes",
    "sum_requested_prbs",
    "sum_granted_prbs",
    "prb_grant_ratio",
    "cluster",
    "slicing",
    "scheduling",
    "reservation",
    "source_file",
    "label_quality",
]

UE_SERVICE_BY_IMSI = {
    "1010123456002": "eMBB",
    "1010123456003": "eMBB",
    "1010123456004": "eMBB",
    "1010123456005": "eMBB",
    "1010123456006": "URLLC",
    "1010123456007": "URLLC",
    "1010123456008": "URLLC",
    "1010123456009": "URLLC",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Open RAN commercial traffic twinning KPM CSVs into the project training schema.")
    parser.add_argument("--dataset-root", required=True, help="Path to extracted dataset-kpm folder, e.g. E:\\dataset-kpm")
    parser.add_argument("--output", default="data/training/open_ran_kpm_training_dataset.csv")
    parser.add_argument("--summary-output", default="")
    parser.add_argument("--max-files", type=int, default=120, help="Maximum per-UE BS metric files to import.")
    parser.add_argument("--sample-every", type=int, default=10, help="Keep every Nth source row to keep local training practical.")
    parser.add_argument("--max-rows", type=int, default=50000)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    if not dataset_root.exists():
        raise SystemExit(f"Dataset root not found: {dataset_root}")

    metric_files = find_bs_ue_metric_files(dataset_root, args.max_files)
    rows, source_counts = import_metric_files(metric_files, sample_every=max(1, args.sample_every), max_rows=args.max_rows)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rows(output_path, rows)

    summary = {
        "dataset_root": str(dataset_root),
        "output": str(output_path),
        "source_files_seen": len(metric_files),
        "rows_written": len(rows),
        "sample_every": args.sample_every,
        "max_rows": args.max_rows,
        "service_class_counts": dict(Counter(row["service_class"] for row in rows)),
        "fault_type_counts": dict(Counter(row["fault_type"] for row in rows)),
        "label_quality_counts": dict(Counter(row["label_quality"] for row in rows)),
        "source_group_counts": dict(source_counts),
        "notes": [
            "This importer uses BS-side per-UE KPM files because they expose IMSI, slice_id, slice_prb, scheduling policy, bitrate, CQI, SINR, packet error, buffers, and requested/granted PRBs.",
            "Fault labels are weak labels derived from KPI stress patterns because the source dataset is traffic/slicing oriented, not a fault-labelled anomaly dataset.",
        ],
    }
    summary_path = Path(args.summary_output) if args.summary_output else output_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def find_bs_ue_metric_files(dataset_root: Path, max_files: int) -> list[Path]:
    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for path in dataset_root.rglob("*_metrics.csv"):
        if path.name == "enb_metrics.csv":
            continue
        if path.parent.name != "bs":
            continue
        context = parse_path_context(path)
        context_id = f"{context['cluster']}/{context['slicing']}/{context['scheduling']}"
        grouped[context_id][path.stem.replace("_metrics", "")].append(path)
    for by_imsi in grouped.values():
        for paths in by_imsi.values():
            paths.sort(key=lambda item: str(item))

    ordered: list[Path] = []
    contexts = sorted(grouped)
    index = 0
    while len(ordered) < max_files:
        added = False
        for context_id in contexts:
            imsies = sorted(grouped[context_id])
            for imsi in imsies:
                if index < len(grouped[context_id][imsi]):
                    ordered.append(grouped[context_id][imsi][index])
                    added = True
                    if len(ordered) >= max_files:
                        break
            if len(ordered) >= max_files:
                break
        if not added:
            break
        index += 1
    return ordered


def import_metric_files(paths: list[Path], *, sample_every: int, max_rows: int) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    for path in paths:
        context = parse_path_context(path)
        source_counts[f"{context['cluster']}/{context['slicing']}/{context['scheduling']}"] += 1
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            for source_index, raw in enumerate(reader):
                if source_index % sample_every != 0:
                    continue
                row = convert_bs_ue_row(raw, path, context, source_index)
                if row is None:
                    continue
                rows.append(row)
                if len(rows) >= max_rows:
                    return rows, source_counts
    return rows, source_counts


def convert_bs_ue_row(raw: dict[str, str], path: Path, context: dict[str, str], source_index: int) -> dict[str, Any] | None:
    imsi = clean(raw.get("IMSI")) or path.stem.replace("_metrics", "")
    if not imsi:
        return None

    dl_brate = num(raw, "tx_brate downlink [Mbps]")
    ul_brate = num(raw, "rx_brate uplink [Mbps]")
    throughput = max(0.0, dl_brate) + max(0.0, ul_brate)
    tx_error = clamp(num(raw, "tx_errors downlink (%)"), 0.0, 100.0)
    rx_error = clamp(num(raw, "rx_errors uplink (%)"), 0.0, 100.0)
    packet_loss = max(tx_error, rx_error)
    sinr = num(raw, "ul_sinr")
    dl_cqi = num(raw, "dl_cqi")
    dl_mcs = num(raw, "dl_mcs")
    ul_mcs = num(raw, "ul_mcs")
    dl_buffer = max(0.0, num(raw, "dl_buffer [bytes]"))
    ul_buffer = max(0.0, num(raw, "ul_buffer [bytes]"))
    requested_prbs = max(0.0, num(raw, "sum_requested_prbs"))
    granted_prbs = max(0.0, num(raw, "sum_granted_prbs"))
    slice_prb = max(0.0, num(raw, "slice_prb"))
    grant_ratio = granted_prbs / requested_prbs if requested_prbs > 0 else 1.0

    prb_alloc_pct = clamp((slice_prb / 50.0) * 100.0 if slice_prb else 0.0, 0.0, 100.0)
    buffer_pressure = clamp((dl_buffer + ul_buffer) / 250000.0 * 45.0, 0.0, 45.0)
    request_pressure = clamp((1.0 - grant_ratio) * 45.0 if requested_prbs > 0 else 0.0, 0.0, 45.0)
    prb_util = clamp(prb_alloc_pct + buffer_pressure + request_pressure, 0.0, 100.0)

    latency = estimate_latency_ms(service_class_for(imsi), packet_loss, sinr, dl_buffer, grant_ratio)
    jitter = round(max(0.5, latency * 0.15 + packet_loss * 0.4), 4)
    bler = packet_loss
    fault_type = infer_fault_type(prb_util, sinr, packet_loss, dl_buffer, grant_ratio)

    return {
        "t": clean(raw.get("Timestamp")) or source_index,
        "cell_id": "BS_CLUSTER_" + context["cluster"].replace("cluster_", ""),
        "ue_id": imsi,
        "service_class": service_class_for(imsi),
        "fault_active": fault_type != "normal",
        "fault_type": fault_type,
        "aml_attack_active": False,
        "aml_attack_type": "none",
        "latency_ms": latency,
        "jitter_ms": jitter,
        "throughput_mbps": round(throughput, 6),
        "packet_loss_pct": round(packet_loss, 4),
        "prb_util_pct": round(prb_util, 4),
        "handover_fail_pct": 0.0,
        "edge_delay_ms": 2.5,
        "backhaul_delay_ms": 4.0,
        "sinr_db": round(sinr, 4),
        "bler_pct": round(bler, 4),
        "slice_id": clean(raw.get("slice_id")),
        "slice_prb": round(slice_prb, 4),
        "scheduling_policy": clean(raw.get("scheduling_policy")),
        "dl_cqi": round(dl_cqi, 4),
        "dl_mcs": round(dl_mcs, 4),
        "ul_mcs": round(ul_mcs, 4),
        "dl_buffer_bytes": round(dl_buffer, 4),
        "ul_buffer_bytes": round(ul_buffer, 4),
        "sum_requested_prbs": round(requested_prbs, 4),
        "sum_granted_prbs": round(granted_prbs, 4),
        "prb_grant_ratio": round(grant_ratio, 6),
        "cluster": context["cluster"],
        "slicing": context["slicing"],
        "scheduling": context["scheduling"],
        "reservation": context["reservation"],
        "source_file": str(path),
        "label_quality": "weak_rule_label" if fault_type != "normal" else "unlabeled_assumed_normal",
    }


def infer_fault_type(prb_util: float, sinr: float, packet_loss: float, dl_buffer: float, grant_ratio: float) -> str:
    if sinr <= 5 and packet_loss >= 5:
        return "radio_link_degradation"
    if prb_util >= 88 or (dl_buffer >= 150000 and grant_ratio <= 0.35):
        return "cell_congestion"
    if packet_loss >= 8:
        return "packet_loss_degradation"
    if sinr <= 2:
        return "radio_quality_degradation"
    return "normal"


def estimate_latency_ms(service: str, packet_loss: float, sinr: float, dl_buffer: float, grant_ratio: float) -> float:
    base = 12.0 if service == "URLLC" else 24.0
    buffer_term = min(60.0, dl_buffer / 12000.0)
    grant_term = max(0.0, 1.0 - grant_ratio) * 28.0
    loss_term = packet_loss * 1.2
    radio_term = max(0.0, 10.0 - sinr) * 1.8
    return round(base + buffer_term + grant_term + loss_term + radio_term, 4)


def service_class_for(imsi: str) -> str:
    return UE_SERVICE_BY_IMSI.get(imsi, "eMBB")


def parse_path_context(path: Path) -> dict[str, str]:
    parts = list(path.parts)
    return {
        "cluster": find_part(parts, "cluster_"),
        "slicing": find_part(parts, "slicing_"),
        "scheduling": find_part(parts, "scheduling_"),
        "reservation": find_part(parts, "RESERVATION-"),
    }


def find_part(parts: list[str], prefix: str) -> str:
    for part in parts:
        if part.startswith(prefix):
            return part
    return "unknown"


def num(row: dict[str, str], key: str) -> float:
    value = clean(row.get(key))
    if value == "":
        return 0.0
    try:
        number = float(value)
    except ValueError:
        return 0.0
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return number


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
