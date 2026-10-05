from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any


OUTPUT_FIELDS = ["cell_id", "latency", "jitter", "throughput", "loss", "prb", "handover", "edgeDelay", "backhaul", "sinr", "bler", "cqi", "rsrp_dbm", "rsrq_db"]

DEFAULT_KPIS = {
    "latency": 20.0,
    "jitter": 4.0,
    "throughput": 100.0,
    "loss": 0.2,
    "prb": 60.0,
    "handover": 0.8,
    "edgeDelay": 2.5,
    "backhaul": 4.0,
    "sinr": 20.0,
    "bler": 1.2,
    "cqi": 9.0,
    "rsrp_dbm": -85.0,
    "rsrq_db": -9.0,
}

ALIASES = {
    "latency": ["latency", "rtt", "rtt_ms", "ping_rtt_ms", "gtp_u_latency_ms", "pdcp_latency_ms", "DRB.PacketDelayDl", "DRB.RlcSduDelayDl"],
    "jitter": ["jitter", "jitter_ms", "iperf_udp_jitter_ms"],
    "throughput": ["throughput", "throughput_mbps", "bitrate_mbps", "pdcp_throughput_mbps", "DRB.UEThpDl", "DRB.UEThpUl"],
    "loss": ["loss", "loss_pct", "lost_percent", "packet_loss", "packet_loss_pct"],
    "prb": ["prb", "prb_pct", "dl_prb", "ul_prb", "dl_prb_usage_pct", "ul_prb_usage_pct", "RRU.PrbUsedDl", "RRU.PrbUsedUl", "RRU.PrbTotDl", "RRU.PrbTotUl"],
    "handover": ["handover", "handover_fail", "handover_fail_pct", "HO.ExecFail"],
    "edgeDelay": ["edge_delay", "edgeDelay", "mec_app_latency_ms", "upf_to_mec_latency_ms"],
    "backhaul": ["backhaul", "backhaul_ms", "transport_rtt_ms", "gnb_to_upf_rtt_ms"],
    "sinr": ["sinr", "sinr_db", "ue_sinr_db", "pusch_sinr_db"],
    "bler": ["bler", "bler_pct", "dl_bler", "dl_bler_pct", "ul_bler_pct"],
    "cqi": ["cqi", "dl_cqi", "ul_cqi", "wideband_cqi"],
    "rsrp_dbm": ["rsrp", "rsrp_dbm"],
    "rsrq_db": ["rsrq", "rsrq_db"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize OAI/srsRAN/ping/iperf telemetry into dashboard KPI CSV.")
    parser.add_argument("--input", required=True, help="Raw telemetry file: iperf JSON/text, ping output, or key-value log.")
    parser.add_argument("--output", required=True, help="Normalized CSV output path.")
    parser.add_argument("--kind", default="auto", choices=["auto", "iperf_json", "iperf_text", "ping", "kv_log"])
    parser.add_argument("--cell-id", default="CELL_A")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    text = input_path.read_text(encoding="utf-8", errors="replace")
    kind = detect_kind(text, args.kind)
    rows = parse_rows(text, kind=kind, cell_id=args.cell_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_rows(output_path, rows)
    print(f"Normalized {len(rows)} row(s) from {kind} into {output_path}")


def detect_kind(text: str, requested: str) -> str:
    if requested != "auto":
        return requested
    stripped = text.lstrip()
    if stripped.startswith("{") and ("bits_per_second" in text or '"intervals"' in text):
        return "iperf_json"
    if "iperf" in text.lower() or "Mbits/sec" in text or "bits/sec" in text:
        return "iperf_text"
    if "ping statistics" in text.lower() or "packets transmitted" in text.lower() or "minimum =" in text.lower():
        return "ping"
    return "kv_log"


def parse_rows(text: str, *, kind: str, cell_id: str) -> list[dict[str, Any]]:
    if kind == "iperf_json":
        return parse_iperf_json(text, cell_id)
    if kind == "iperf_text":
        return parse_iperf_text(text, cell_id)
    if kind == "ping":
        return [parse_ping(text, cell_id)]
    return parse_kv_log(text, cell_id)


def parse_iperf_json(text: str, cell_id: str) -> list[dict[str, Any]]:
    data = json.loads(text)
    rows: list[dict[str, Any]] = []
    intervals = data.get("intervals") or []
    for interval in intervals:
        streams = interval.get("streams") or []
        summary = interval.get("sum") or (streams[0] if streams else {})
        rows.append(build_row(cell_id, from_iperf_summary(summary)))
    if rows:
        return rows
    end = data.get("end", {})
    summary = end.get("sum_received") or end.get("sum") or end.get("sum_sent") or {}
    return [build_row(cell_id, from_iperf_summary(summary))]


def from_iperf_summary(summary: dict[str, Any]) -> dict[str, float]:
    bits = float(summary.get("bits_per_second", 0) or 0)
    mbps = bits / 1_000_000
    return {
        "throughput": mbps if mbps > 0 else DEFAULT_KPIS["throughput"],
        "jitter": float(summary.get("jitter_ms", DEFAULT_KPIS["jitter"]) or DEFAULT_KPIS["jitter"]),
        "loss": float(summary.get("lost_percent", DEFAULT_KPIS["loss"]) or DEFAULT_KPIS["loss"]),
    }


def parse_iperf_text(text: str, cell_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if "bits/sec" not in line:
            continue
        throughput = extract_bitrate_mbps(line)
        jitter = extract_number_before(line, "ms")
        loss_match = re.search(r"\(([\d.]+)%\)", line)
        rows.append(
            build_row(
                cell_id,
                {
                    "throughput": throughput or DEFAULT_KPIS["throughput"],
                    "jitter": jitter or DEFAULT_KPIS["jitter"],
                    "loss": float(loss_match.group(1)) if loss_match else DEFAULT_KPIS["loss"],
                },
            )
        )
    return rows or [build_row(cell_id, {})]


def parse_ping(text: str, cell_id: str) -> dict[str, Any]:
    values: dict[str, float] = {}
    linux_loss = re.search(r"([\d.]+)%\s*packet loss", text)
    windows_loss = re.search(r"\(([\d.]+)%\s*loss\)", text, re.IGNORECASE)
    if linux_loss or windows_loss:
        values["loss"] = float((linux_loss or windows_loss).group(1))
    linux_rtt = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms", text)
    windows_rtt = re.search(r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms", text, re.IGNORECASE)
    if linux_rtt:
        min_rtt, avg_rtt, max_rtt, mdev = [float(item) for item in linux_rtt.groups()]
        values["latency"] = avg_rtt
        values["jitter"] = mdev
    elif windows_rtt:
        min_rtt, max_rtt, avg_rtt = [float(item) for item in windows_rtt.groups()]
        values["latency"] = avg_rtt
        values["jitter"] = max(0.1, (max_rtt - min_rtt) / 2)
    return build_row(cell_id, values)


def parse_kv_log(text: str, cell_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        row = parse_kv_line(line, cell_id)
        if row:
            rows.append(row)
    return rows or [build_row(cell_id, {})]


def parse_kv_line(line: str, cell_id: str) -> dict[str, Any] | None:
    if not line.strip() or line.strip().startswith("#"):
        return None
    if "ind_msg latency" in line.lower():
        return None
    values = extract_kv_metrics(line)
    if not values:
        return None
    return build_row(values.pop("cell_id", cell_id), values)


def extract_kv_metrics(line: str) -> dict[str, Any]:
    pairs: dict[str, Any] = {}
    cell_match = re.search(r"\b(CELL_[A-Z])\b", line)
    if cell_match:
        pairs["cell_id"] = cell_match.group(1)
    prb_values: list[float] = []
    for raw_key, raw_value, raw_unit in re.findall(r"([A-Za-z0-9_.-]+)\s*[:=]\s*(-?\d+(?:\.\d+)?)(?:\s*\[?([A-Za-z%/]+)\]?)?", line):
        value = convert_value(raw_key, float(raw_value), raw_unit)
        if raw_key.lower() in {"dl_prb", "ul_prb", "dl_prb_usage_pct", "ul_prb_usage_pct", "rru.prbuseddl", "rru.prbusedul", "rru.prbtotdl", "rru.prbtotul"}:
            prb_values.append(value)
            continue
        normalized = normalize_key(raw_key)
        if normalized:
            pairs[normalized] = value
    if prb_values:
        pairs["prb"] = mean(prb_values)
    elif "prb" not in pairs:
        dl_prb = find_named_number(line, ["dl_prb", "PRB_DL", "RRU.PrbUsedDl", "RRU.PrbTotDl"])
        ul_prb = find_named_number(line, ["ul_prb", "PRB_UL", "RRU.PrbUsedUl", "RRU.PrbTotUl"])
        prbs = [value for value in [dl_prb, ul_prb] if value is not None]
        if prbs:
            pairs["prb"] = mean(prbs)
    return pairs


def normalize_key(raw_key: str) -> str | None:
    key = raw_key.strip()
    lowered = key.lower()
    for normalized, aliases in ALIASES.items():
        if lowered == normalized.lower() or lowered in {alias.lower() for alias in aliases}:
            return normalized
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


def build_row(cell_id: str, values: dict[str, Any]) -> dict[str, Any]:
    row = {"cell_id": cell_id}
    for field in OUTPUT_FIELDS[1:]:
        row[field] = round(float(values.get(field, DEFAULT_KPIS[field])), 4)
    return row


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def extract_bitrate_mbps(line: str) -> float | None:
    match = re.search(r"([\d.]+)\s*([KMG])?bits/sec", line)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2) or "M"
    if unit == "K":
        return value / 1000
    if unit == "G":
        return value * 1000
    return value


def extract_number_before(line: str, unit: str) -> float | None:
    matches = re.findall(r"([\d.]+)\s*" + re.escape(unit), line)
    if not matches:
        return None
    return float(matches[-1])


def find_named_number(line: str, names: list[str]) -> float | None:
    for name in names:
        match = re.search(re.escape(name) + r"\s*[:=]\s*(-?\d+(?:\.\d+)?)", line, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


if __name__ == "__main__":
    main()
