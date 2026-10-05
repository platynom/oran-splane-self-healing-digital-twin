from __future__ import annotations

import argparse
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any


CANONICAL_KEYS = [
    "dl_prb_usage_pct",
    "ul_prb_usage_pct",
    "dl_bler_pct",
    "ul_bler_pct",
    "sinr_db",
    "pdcp_throughput_mbps",
    "gnb_to_upf_rtt_ms",
    "handover_fail_pct",
    "ping_rtt_ms",
    "iperf_udp_jitter_ms",
    "packet_loss_pct",
    "cqi",
    "mcs",
    "rsrp_dbm",
    "rsrq_db",
    "ue_count",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge raw OAI/srsRAN/RF-sim logs into canonical metric lines.")
    parser.add_argument("--input", default="data/telemetry/raw/oai_runtime.log")
    parser.add_argument("--output", default="data/telemetry/raw/live_oai_metrics.log")
    parser.add_argument("--cell-id", default="CELL_A")
    parser.add_argument("--poll", type=float, default=1.0)
    parser.add_argument("--from-start", action="store_true")
    parser.add_argument("--once", action="store_true", help="Process available input once and exit.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.touch(exist_ok=True)

    offset = 0 if args.from_start else input_path.stat().st_size
    print(f"Bridging {input_path} -> {output_path}")
    while True:
        offset, count = bridge_new_lines(input_path, output_path, offset, args.cell_id)
        if count:
            print(f"bridged {count} metric line(s)")
        if args.once:
            break
        time.sleep(args.poll)


def bridge_new_lines(input_path: Path, output_path: Path, offset: int, cell_id: str) -> tuple[int, int]:
    with input_path.open("r", encoding="utf-8", errors="replace") as source:
        source.seek(offset)
        lines = source.readlines()
        offset = source.tell()
    metric_lines = [line for line in (to_metric_line(raw, cell_id) for raw in lines) if line]
    if metric_lines:
        with output_path.open("a", encoding="utf-8") as target:
            for line in metric_lines:
                target.write(line + "\n")
    return offset, len(metric_lines)


def to_metric_line(raw_line: str, default_cell_id: str) -> str | None:
    metrics = extract_metrics(raw_line)
    if not metrics:
        return None
    cell_id = extract_cell_id(raw_line, default_cell_id)
    stamp = extract_timestamp(raw_line) or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ordered = " ".join(f"{key}={round(value, 4)}" for key, value in metrics.items() if key in CANONICAL_KEYS)
    return f"{stamp} {cell_id} {ordered}".strip()


def extract_metrics(line: str) -> dict[str, float]:
    if "ind_msg latency" in line.lower():
        return {}
    metrics: dict[str, float] = {}
    explicit_pairs = extract_explicit_pairs(line)
    metrics.update(explicit_pairs)
    metrics.update(extract_readable_patterns(line))
    return metrics


def extract_explicit_pairs(line: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for raw_key, raw_value, raw_unit in re.findall(r"([A-Za-z0-9_.-]+)\s*[:=]\s*(-?\d+(?:\.\d+)?)(?:\s*\[?([A-Za-z%/]+)\]?)?", line):
        key = canonical_key(raw_key)
        if key:
            metrics[key] = convert_value(raw_key, float(raw_value), raw_unit)
    return metrics


def extract_readable_patterns(line: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    patterns = [
        ("dl_prb_usage_pct", r"\b(?:DL\s*)?PRB(?:\s*DL)?\s*(?:usage|used|=|:)?\s*(\d+(?:\.\d+)?)\s*%"),
        ("ul_prb_usage_pct", r"\bUL\s*PRB(?:\s*usage|used|=|:)?\s*(\d+(?:\.\d+)?)\s*%"),
        ("dl_bler_pct", r"\b(?:DL\s*)?BLER(?:\s*DL)?\s*(?:=|:)?\s*(\d+(?:\.\d+)?)\s*%"),
        ("ul_bler_pct", r"\bUL\s*BLER(?:\s*=|:)?\s*(\d+(?:\.\d+)?)\s*%"),
        ("sinr_db", r"\bSINR\s*(?:=|:)?\s*(-?\d+(?:\.\d+)?)\s*dB"),
        ("gnb_to_upf_rtt_ms", r"\b(?:RTT|rtt|latency)\s*(?:=|:)?\s*(\d+(?:\.\d+)?)\s*ms"),
        ("iperf_udp_jitter_ms", r"\bjitter\s*(?:=|:)?\s*(\d+(?:\.\d+)?)\s*ms"),
        ("packet_loss_pct", r"\b(?:loss|packet loss)\s*(?:=|:)?\s*(\d+(?:\.\d+)?)\s*%"),
        ("handover_fail_pct", r"\b(?:handover|HO)\s*(?:fail|failure|failures)\s*(?:=|:)?\s*(\d+(?:\.\d+)?)\s*%?"),
        ("cqi", r"\bCQI\s*(?:=|:)?\s*(\d+(?:\.\d+)?)"),
        ("mcs", r"\bMCS\s*(?:=|:)?\s*(\d+(?:\.\d+)?)"),
        ("rsrp_dbm", r"\bRSRP\s*(?:=|:)?\s*(-?\d+(?:\.\d+)?)\s*dBm"),
        ("rsrq_db", r"\bRSRQ\s*(?:=|:)?\s*(-?\d+(?:\.\d+)?)\s*dB"),
        ("ue_count", r"\b(?:UEs?|ue_count|connected_ues)\s*(?:=|:)?\s*(\d+(?:\.\d+)?)"),
    ]
    for key, pattern in patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match and key not in metrics:
            metrics[key] = float(match.group(1))
    bitrate = extract_bitrate_mbps(line)
    if bitrate is not None:
        metrics["pdcp_throughput_mbps"] = bitrate
        loss = extract_parenthesized_loss(line)
        if loss is not None or "iperf" in line.lower() or "jitter" in line.lower():
            jitter = extract_last_ms_value(line)
            if jitter is not None:
                metrics["iperf_udp_jitter_ms"] = jitter
        if loss is not None:
            metrics["packet_loss_pct"] = loss
    return metrics


def canonical_key(raw_key: str) -> str | None:
    key = raw_key.strip().lower()
    aliases = {
        "dl_prb_usage_pct": {"dl_prb", "dl_prb_usage_pct", "rru.prbuseddl", "rru.prbtotdl", "prb_dl", "mac_dl_prb"},
        "ul_prb_usage_pct": {"ul_prb", "ul_prb_usage_pct", "rru.prbusedul", "rru.prbtotul", "prb_ul", "mac_ul_prb"},
        "dl_bler_pct": {"dl_bler", "dl_bler_pct", "bler_dl"},
        "ul_bler_pct": {"ul_bler", "ul_bler_pct", "bler_ul"},
        "sinr_db": {"sinr", "sinr_db", "ue_sinr_db", "pusch_sinr_db", "pucch_sinr_db"},
        "pdcp_throughput_mbps": {"throughput", "throughput_mbps", "pdcp_throughput_mbps", "pdcp_dl_throughput_mbps", "drb.uethpdl", "drb.uethpul"},
        "gnb_to_upf_rtt_ms": {"rtt", "rtt_ms", "latency", "latency_ms", "gnb_to_upf_rtt_ms", "transport_rtt_ms", "drb.rlcsdudelaydl"},
        "handover_fail_pct": {"handover", "handover_fail", "handover_fail_pct", "ho.execfail"},
        "ping_rtt_ms": {"ping_rtt_ms"},
        "iperf_udp_jitter_ms": {"jitter", "jitter_ms", "iperf_udp_jitter_ms"},
        "packet_loss_pct": {"loss", "loss_pct", "packet_loss", "packet_loss_pct", "lost_percent"},
        "cqi": {"cqi", "dl_cqi", "ul_cqi", "wideband_cqi"},
        "mcs": {"mcs", "dl_mcs", "ul_mcs"},
        "rsrp_dbm": {"rsrp", "rsrp_dbm"},
        "rsrq_db": {"rsrq", "rsrq_db"},
        "ue_count": {"ue_count", "connected_ues", "rrc_connected_ues", "nb_ue", "ues"},
    }
    for canonical, names in aliases.items():
        if key == canonical or key in names:
            return canonical
    return None


def convert_value(raw_key: str, value: float, raw_unit: str) -> float:
    key = raw_key.strip().lower()
    unit = raw_unit.strip().lower() if raw_unit else ""
    if key in {"drb.uethpdl", "drb.uethpul"} and unit == "kbps":
        return value / 1000
    if key in {"rru.prbtotdl", "rru.prbtotul", "rru.prbuseddl", "rru.prbusedul"}:
        return min(value, 100.0)
    if key == "drb.rlcsdudelaydl" and unit in {"μs", "us"}:
        return value / 1000
    return value


def extract_cell_id(line: str, default: str) -> str:
    match = re.search(r"\bCELL_[A-Z]\b", line)
    return match.group(0) if match else default


def extract_timestamp(line: str) -> str | None:
    match = re.search(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\b", line)
    return match.group(0) if match else None


def extract_bitrate_mbps(line: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*([KMG])?bits/sec", line, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = (match.group(2) or "M").upper()
    if unit == "K":
        return value / 1000
    if unit == "G":
        return value * 1000
    return value


def extract_last_ms_value(line: str) -> float | None:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*ms", line, re.IGNORECASE)
    if not matches:
        return None
    return float(matches[-1])


def extract_parenthesized_loss(line: str) -> float | None:
    match = re.search(r"\((\d+(?:\.\d+)?)%\)", line)
    return float(match.group(1)) if match else None


if __name__ == "__main__":
    main()
