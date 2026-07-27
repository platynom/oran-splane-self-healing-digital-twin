from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def main() -> None:
    parser = argparse.ArgumentParser(description="Import compact Open RAN KPM auxiliary summaries from mgen.csv and enb_metrics.csv.")
    parser.add_argument("--dataset-root", required=True, help="Path to extracted dataset-kpm folder, e.g. E:\\dataset-kpm")
    parser.add_argument("--output-dir", default="data/training")
    parser.add_argument("--max-files", type=int, default=240)
    parser.add_argument("--max-rows-per-file", type=int, default=5000)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    app_rows = import_mgen(dataset_root, args.max_files, args.max_rows_per_file)
    cell_rows = import_enb(dataset_root, args.max_files, args.max_rows_per_file)

    app_path = output_dir / "open_ran_app_qos_summary.csv"
    cell_path = output_dir / "open_ran_cell_load_summary.csv"
    write_rows(app_path, app_rows)
    write_rows(cell_path, cell_rows)

    summary = {
        "dataset_root": str(dataset_root),
        "application_qos_output": str(app_path),
        "cell_load_output": str(cell_path),
        "application_qos_rows": len(app_rows),
        "cell_load_rows": len(cell_rows),
        "application_service_counts": dict(Counter(row["service_class"] for row in app_rows)),
        "cell_context_counts": dict(Counter(f"{row['cluster']}/{row['slicing']}/{row['scheduling']}" for row in cell_rows)),
        "notes": [
            "mgen.csv gives application-layer packet timing and payload information.",
            "enb_metrics.csv gives aggregate base-station UE count and downlink/uplink bitrate.",
            "These summaries are intentionally compact so the dashboard and reports do not need to scan the full external SSD dataset.",
        ],
    }
    summary_path = output_dir / "open_ran_aux_metrics_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def import_mgen(dataset_root: Path, max_files: int, max_rows_per_file: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in select_balanced_mgen_files(dataset_root, max_files):
        context = parse_path_context(path)
        delays: list[float] = []
        payloads: list[float] = []
        protocols: Counter[str] = Counter()
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            for index, raw in enumerate(reader):
                if index >= max_rows_per_file:
                    break
                recv = to_float(raw.get("Received Time"))
                sent = to_float(raw.get("Sent Time"))
                if recv is not None and sent is not None and recv >= sent:
                    delays.append((recv - sent) * 1000)
                payload = to_float(raw.get("Protocol Payload Size"))
                if payload is not None:
                    payloads.append(payload)
                protocol = str(raw.get("Protocol") or "unknown")
                protocols[protocol] += 1
        if not delays and not payloads:
            continue
        ue_id = extract_ue_id(path)
        rows.append(
            {
                **context,
                "ue_id": ue_id,
                "service_class": service_class_for(ue_id),
                "packets_sampled": sum(protocols.values()),
                "mean_app_delay_ms": round(mean(delays), 4) if delays else 0.0,
                "max_app_delay_ms": round(max(delays), 4) if delays else 0.0,
                "mean_payload_bytes": round(mean(payloads), 4) if payloads else 0.0,
                "protocols": ";".join(f"{key}:{value}" for key, value in sorted(protocols.items())),
                "source_file": str(path),
            }
        )
    return rows


def import_enb(dataset_root: Path, max_files: int, max_rows_per_file: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in select_balanced_enb_files(dataset_root, max_files):
        context = parse_path_context(path)
        ue_counts: list[float] = []
        dl_rates: list[float] = []
        ul_rates: list[float] = []
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle)
            for index, raw in enumerate(reader):
                if index >= max_rows_per_file:
                    break
                add_if_number(ue_counts, raw.get("nof_ue"))
                add_if_number(dl_rates, raw.get("dl_brate"))
                add_if_number(ul_rates, raw.get("ul_brate"))
        if not ue_counts and not dl_rates and not ul_rates:
            continue
        rows.append(
            {
                **context,
                "records_sampled": max(len(ue_counts), len(dl_rates), len(ul_rates)),
                "mean_connected_ues": round(mean(ue_counts), 4) if ue_counts else 0.0,
                "max_connected_ues": round(max(ue_counts), 4) if ue_counts else 0.0,
                "mean_dl_brate_mbps": round(mean(dl_rates), 6) if dl_rates else 0.0,
                "mean_ul_brate_mbps": round(mean(ul_rates), 6) if ul_rates else 0.0,
                "max_dl_brate_mbps": round(max(dl_rates), 6) if dl_rates else 0.0,
                "max_ul_brate_mbps": round(max(ul_rates), 6) if ul_rates else 0.0,
                "source_file": str(path),
            }
        )
    return rows


def select_balanced_mgen_files(dataset_root: Path, max_files: int) -> list[Path]:
    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for path in dataset_root.rglob("mgen.csv"):
        context = parse_path_context(path)
        context_id = f"{context['cluster']}/{context['slicing']}/{context['scheduling']}"
        grouped[context_id][extract_ue_id(path)].append(path)
    for by_ue in grouped.values():
        for paths in by_ue.values():
            paths.sort(key=lambda item: str(item))
    return round_robin_nested(grouped, max_files)


def select_balanced_enb_files(dataset_root: Path, max_files: int) -> list[Path]:
    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    for path in dataset_root.rglob("enb_metrics.csv"):
        context = parse_path_context(path)
        context_id = f"{context['cluster']}/{context['slicing']}/{context['scheduling']}"
        grouped[context_id]["enb"].append(path)
    for by_type in grouped.values():
        for paths in by_type.values():
            paths.sort(key=lambda item: str(item))
    return round_robin_nested(grouped, max_files)


def round_robin_nested(grouped: dict[str, dict[str, list[Path]]], max_files: int) -> list[Path]:
    ordered: list[Path] = []
    contexts = sorted(grouped)
    index = 0
    while len(ordered) < max_files:
        added = False
        for context_id in contexts:
            inner_keys = sorted(grouped[context_id])
            for inner_key in inner_keys:
                if index < len(grouped[context_id][inner_key]):
                    ordered.append(grouped[context_id][inner_key][index])
                    added = True
                    if len(ordered) >= max_files:
                        break
            if len(ordered) >= max_files:
                break
        if not added:
            break
        index += 1
    return ordered


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


def extract_ue_id(path: Path) -> str:
    for part in path.parts:
        if part.startswith("ue_"):
            return part.replace("ue_00", "").replace("ue_", "")
    return "unknown"


def service_class_for(ue_id: str) -> str:
    return "eMBB" if ue_id in {"1010123456002", "1010123456003", "1010123456004", "1010123456005"} else "URLLC"


def add_if_number(values: list[float], value: object) -> None:
    number = to_float(value)
    if number is not None:
        values.append(number)


def to_float(value: object) -> float | None:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return None


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
