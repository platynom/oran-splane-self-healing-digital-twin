from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Protocol


KPI_KEYS = ("latency", "jitter", "throughput", "loss", "prb", "handover", "edgeDelay", "backhaul", "sinr", "bler")
KPI_ALIASES = {
    "latency": ("latency", "latency_ms"),
    "jitter": ("jitter", "jitter_ms"),
    "throughput": ("throughput", "throughput_mbps"),
    "loss": ("loss", "packet_loss_pct"),
    "prb": ("prb", "prb_util_pct"),
    "handover": ("handover", "handover_fail_pct"),
    "edgeDelay": ("edgeDelay", "edge_delay_ms"),
    "backhaul": ("backhaul", "backhaul_delay_ms"),
    "sinr": ("sinr", "sinr_db"),
    "bler": ("bler", "bler_pct"),
}


class TelemetryAdapter(Protocol):
    mode: str
    name: str
    oai_ready: bool

    def describe(self) -> dict[str, Any]:
        ...

    def sample(
        self,
        *,
        t: int,
        cell: dict[str, Any],
        selected_cell: dict[str, Any],
        profile: dict[str, Any],
        scenario: Any,
        weather_impact: float,
    ) -> dict[str, Any]:
        ...


class SyntheticProfileTelemetryAdapter:
    mode = "profile_simulation"
    name = "SyntheticProfileTelemetryAdapter"
    oai_ready = True

    def describe(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "adapter": self.name,
            "oai_ready": self.oai_ready,
            "next_integration": "Map OAI/srsRAN/E2 KPM counters into the same KPI schema used by this API.",
            "required_real_counters": required_real_counters(),
        }

    def sample(
        self,
        *,
        t: int,
        cell: dict[str, Any],
        selected_cell: dict[str, Any],
        profile: dict[str, Any],
        scenario: Any,
        weather_impact: float,
    ) -> dict[str, Any]:
        selected = cell["id"] == selected_cell["id"]
        wave = 0.5 + 0.5 * math.sin((t / 18.0) + cell["baseLoad"] * 3)
        packet_pressure = level(profile["packetFrequency"], {"low": 0.1, "medium": 0.28, "high": 0.42, "very high": 0.55})
        burst_pressure = level(profile["parameters"].get("traffic_burstiness"), {"low": 0.03, "medium": 0.12, "high": 0.22})
        density_pressure = min(0.35, profile["density"] * 0.045)
        bandwidth_relief = min(0.18, profile["bandwidth"] / 800)
        load = min(
            1.0,
            cell["baseLoad"] * 0.42
            + scenario.network_load * 0.58
            + wave * 0.12
            + packet_pressure
            + burst_pressure
            + density_pressure
            - bandwidth_relief,
        )
        mobility_pressure = max(scenario.mobility, profile["mobility"] / 6)
        sync_pressure = level(profile["parameters"].get("synchronization_requirement"), {"low": 0.02, "medium": 0.08, "high": 0.18})
        edge_pressure = profile["edge"] / 10
        reliability_pressure = 0.18 if profile["parameters"].get("retransmission_policy") == "fast" else 0.06
        latency = profile["latency"] * (0.50 + load * 0.62 + edge_pressure * 0.18)
        jitter = profile["jitter"] * (0.50 + load * 0.55 + weather_impact * 0.22 + sync_pressure)
        throughput = profile["throughput"] * (1.15 - load * 0.34 + bandwidth_relief * 0.35)
        loss = profile["loss"] * (0.42 + load * 0.62 + reliability_pressure)
        prb = 28 + load * 68
        handover_sensitivity = level(
            profile["parameters"].get("handover_sensitivity"),
            {"low": -0.25, "medium": 0.0, "high": 0.22, "extreme": 0.42},
        )
        handover = 0.2 + mobility_pressure * (3.0 + handover_sensitivity * 3.0)
        edge_delay = profile["edge"] * (0.6 + load * 1.0)
        backhaul = 2 + load * 4
        sinr = 25 - load * 8 - weather_impact * 4
        bler = 0.4 + load * 2.8 + weather_impact * 1.4
        fault = scenario.fault_type if selected else "normal"
        severity = scenario.severity if selected else 0

        kpis = apply_fault(
            {
                "latency": latency,
                "jitter": jitter,
                "throughput": throughput,
                "loss": loss,
                "prb": prb,
                "handover": handover,
                "edgeDelay": edge_delay,
                "backhaul": backhaul,
                "sinr": sinr,
                "bler": bler,
            },
            fault=fault,
            severity=severity,
            profile=profile,
            mobility_pressure=mobility_pressure,
        )
        return normalize_kpis(kpis)


class CsvReplayTelemetryAdapter:
    mode = "csv_replay"
    name = "CsvReplayTelemetryAdapter"
    oai_ready = True

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.rows = self._load_rows(csv_path)
        self.last_mtime = self._mtime(csv_path)

    def describe(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "adapter": self.name,
            "oai_ready": self.oai_ready,
            "source": str(self.csv_path),
            "rows": len(self.rows),
            "watching": True,
            "last_modified": self.last_mtime,
            "next_integration": "Use this mode to replay exported OAI/srsRAN/KPM counters after normalization.",
            "required_real_counters": required_real_counters(),
        }

    def sample(
        self,
        *,
        t: int,
        cell: dict[str, Any],
        selected_cell: dict[str, Any],
        profile: dict[str, Any],
        scenario: Any,
        weather_impact: float,
    ) -> dict[str, Any]:
        self.reload_if_changed()
        if not self.rows:
            return SyntheticProfileTelemetryAdapter().sample(
                t=t,
                cell=cell,
                selected_cell=selected_cell,
                profile=profile,
                scenario=scenario,
                weather_impact=weather_impact,
            )
        cell_rows = [row for row in self.rows if row.get("cell_id") in {cell["id"], ""}]
        rows = cell_rows or self.rows
        row = rows[t % len(rows)]
        fallback = SyntheticProfileTelemetryAdapter().sample(
            t=t,
            cell=cell,
            selected_cell=selected_cell,
            profile=profile,
            scenario=scenario,
            weather_impact=weather_impact,
        )
        kpis = normalize_kpis({key: parse_float(first_present(row, KPI_ALIASES[key]), fallback[key]) for key in KPI_KEYS})
        kpis = apply_openran_replay_calibration(kpis, row)
        kpis["_telemetry_row"] = row
        if first_present(row, ("cqi", "dl_cqi")) is not None:
            kpis["cqi"] = parse_float(first_present(row, ("cqi", "dl_cqi")), 0.0)
        if first_present(row, ("rsrp_dbm", "rsrp")) is not None:
            kpis["rsrp_dbm"] = parse_float(first_present(row, ("rsrp_dbm", "rsrp")), 0.0)
        if first_present(row, ("rsrq_db", "rsrq")) is not None:
            kpis["rsrq_db"] = parse_float(first_present(row, ("rsrq_db", "rsrq")), 0.0)
        return kpis

    @staticmethod
    def _load_rows(path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def reload_if_changed(self) -> None:
        current_mtime = self._mtime(self.csv_path)
        if current_mtime != self.last_mtime:
            self.rows = self._load_rows(self.csv_path)
            self.last_mtime = current_mtime

    @staticmethod
    def _mtime(path: Path) -> float | None:
        try:
            return path.stat().st_mtime
        except OSError:
            return None


class OaiLogTelemetryAdapter(CsvReplayTelemetryAdapter):
    mode = "oai_log_ingestion"
    name = "OaiLogTelemetryAdapter"

    def describe(self) -> dict[str, Any]:
        description = super().describe()
        description["next_integration"] = "Parse OAI gNB/UE metrics or converted log CSV into normalized KPI rows."
        return description


class NearRtRicKpmTelemetryAdapter(CsvReplayTelemetryAdapter):
    mode = "near_rt_ric_kpm"
    name = "NearRtRicKpmTelemetryAdapter"

    def describe(self) -> dict[str, Any]:
        description = super().describe()
        description["next_integration"] = "Read normalized E2SM-KPM measurements from near-RT RIC export or stream bridge."
        return description


class OpenRanKpmReplayTelemetryAdapter(CsvReplayTelemetryAdapter):
    mode = "open_ran_kpm_replay"
    name = "OpenRanKpmReplayTelemetryAdapter"

    def sample(
        self,
        *,
        t: int,
        cell: dict[str, Any],
        selected_cell: dict[str, Any],
        profile: dict[str, Any],
        scenario: Any,
        weather_impact: float,
    ) -> dict[str, Any]:
        if cell["id"] != selected_cell["id"]:
            return SyntheticProfileTelemetryAdapter().sample(
                t=t,
                cell=cell,
                selected_cell=selected_cell,
                profile=profile,
                scenario=scenario,
                weather_impact=weather_impact,
            )
        return super().sample(
            t=t,
            cell=cell,
            selected_cell=selected_cell,
            profile=profile,
            scenario=scenario,
            weather_impact=weather_impact,
        )

    def describe(self) -> dict[str, Any]:
        description = super().describe()
        description["next_integration"] = "Replay imported Open RAN Commercial Traffic Twinning KPM rows with UE/slice metadata."
        description["dataset_fields"] = [
            "ue_id",
            "service_class",
            "fault_type",
            "slice_id",
            "slice_prb",
            "scheduling_policy",
            "prb_grant_ratio",
            "dl_cqi",
            "dl_mcs",
            "ul_mcs",
        ]
        return description


def build_adapter(mode: str, source: str | None = None) -> TelemetryAdapter:
    source_path = Path(source) if source else Path("data/telemetry/sample_oai_like_kpis.csv")
    if mode == "csv_replay":
        return CsvReplayTelemetryAdapter(source_path)
    if mode == "oai_log_ingestion":
        return OaiLogTelemetryAdapter(source_path)
    if mode == "near_rt_ric_kpm":
        return NearRtRicKpmTelemetryAdapter(source_path)
    if mode == "open_ran_kpm_replay":
        return OpenRanKpmReplayTelemetryAdapter(source_path)
    return SyntheticProfileTelemetryAdapter()


def apply_fault(
    kpis: dict[str, float],
    *,
    fault: str,
    severity: float,
    profile: dict[str, Any],
    mobility_pressure: float,
) -> dict[str, float]:
    if fault == "cell_congestion":
        kpis["prb"] += 42 * severity
        kpis["latency"] += profile["latency"] * 2.1 * severity
        kpis["jitter"] += profile["jitter"] * 1.5 * severity
        kpis["throughput"] *= 1 - 0.45 * severity
        kpis["loss"] += profile["loss"] * 1.8 * severity + 0.1 * severity
    elif fault == "backhaul_degradation":
        kpis["backhaul"] += 28 * severity
        kpis["latency"] += 22 * severity
        kpis["jitter"] += 12 * severity
        kpis["loss"] += 0.42 * severity
    elif fault == "edge_overload":
        kpis["edgeDelay"] += 22 * severity * max(1, profile["edge"] / 3)
        kpis["latency"] += 12 * severity * max(1, profile["edge"] / 3)
        kpis["throughput"] *= 1 - 0.16 * severity
    elif fault == "handover_instability":
        kpis["handover"] += 9 * severity * max(0.5, mobility_pressure)
        kpis["latency"] += 8 * severity * max(0.5, mobility_pressure)
        kpis["loss"] += 0.22 * severity
    elif fault == "timing_drift":
        kpis["jitter"] += 13 * severity
        kpis["bler"] += 5 * severity
        kpis["latency"] += 3.5 * severity
    elif fault == "spectrum_interference":
        kpis["sinr"] -= 14 * severity
        kpis["bler"] += 4.8 * severity
        kpis["prb"] += 18 * severity
        kpis["throughput"] *= 1 - 0.35 * severity
        kpis["latency"] += profile["latency"] * 0.7 * severity
        kpis["loss"] += profile["loss"] * 0.95 * severity
    elif fault == "telemetry_poisoning":
        kpis["latency"] += 50 * severity
        kpis["loss"] += 3.5 * severity
        kpis["prb"] -= 35 * severity
        kpis["throughput"] *= 1 + 0.25 * severity
    elif fault == "model_evasion_attack":
        kpis["prb"] -= 28 * severity
        kpis["latency"] *= 1 - 0.35 * severity
        kpis["loss"] *= 1 - 0.45 * severity
        kpis["throughput"] *= 1 + 0.18 * severity
    elif fault == "unsafe_xapp_action":
        kpis["prb"] += 22 * severity
        kpis["throughput"] *= 0.92
    elif fault == "packet_loss_burst":
        kpis["loss"] += 1.8 * severity
        kpis["jitter"] += 5 * severity
        kpis["throughput"] *= 1 - 0.22 * severity
    elif fault == "node_failure":
        kpis["latency"] += 30 * severity
        kpis["jitter"] += 20 * severity
        kpis["throughput"] *= 1 - 0.65 * severity
        kpis["loss"] += 2.5 * severity
        kpis["prb"] = 100
    return kpis


def normalize_kpis(kpis: dict[str, float]) -> dict[str, float]:
    return {
        "latency": round(max(0.01, kpis["latency"]), 3),
        "jitter": round(max(0.01, kpis["jitter"]), 3),
        "throughput": round(max(0.01, kpis["throughput"]), 3),
        "loss": round(max(0, kpis["loss"]), 4),
        "prb": round(max(0, min(100, kpis["prb"])), 3),
        "handover": round(max(0, kpis["handover"]), 3),
        "edgeDelay": round(max(0, kpis["edgeDelay"]), 3),
        "backhaul": round(max(0, kpis["backhaul"]), 3),
        "sinr": round(kpis["sinr"], 3),
        "bler": round(max(0, kpis["bler"]), 3),
    }


def parse_float(value: Any, fallback: float) -> float:
    try:
        if value in {None, ""}:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def first_present(row: dict[str, str], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in {None, ""}:
            return row[key]
    return None


def apply_openran_replay_calibration(kpis: dict[str, float], row: dict[str, str]) -> dict[str, float]:
    fault = str(row.get("fault_type", "normal"))
    grant_ratio = parse_float(row.get("prb_grant_ratio"), 1.0)
    if fault == "cell_congestion":
        kpis["prb"] = max(kpis["prb"], 92.0)
        kpis["latency"] = max(kpis["latency"], 95.0)
        kpis["loss"] = max(kpis["loss"], (1.0 - min(1.0, grant_ratio)) * 2.2)
        kpis["sinr"] = max(kpis["sinr"], 12.0)
        kpis["bler"] = min(max(kpis["bler"], 2.0), 4.0)
    elif fault == "radio_quality_degradation":
        kpis["sinr"] = min(kpis["sinr"], 7.5)
        kpis["bler"] = max(kpis["bler"], 3.2)
    elif fault == "radio_link_degradation":
        kpis["sinr"] = min(kpis["sinr"], 5.0)
        kpis["bler"] = max(kpis["bler"], 5.5)
        kpis["loss"] = max(kpis["loss"], 5.0)
    elif fault == "packet_loss_degradation":
        kpis["loss"] = max(kpis["loss"], 8.0)
        kpis["jitter"] = max(kpis["jitter"], 10.0)
    return normalize_kpis(kpis)


def level(value: Any, mapping: dict[str, float]) -> float:
    return mapping.get(str(value).lower(), 0.0)


def required_real_counters() -> list[str]:
    return [
        "dl_prb_usage_pct",
        "ul_prb_usage_pct",
        "dl_bler_pct",
        "ul_bler_pct",
        "pdcp_throughput_mbps",
        "rlc_retx_pct",
        "ue_count",
        "sinr_db",
        "rsrp_dbm",
        "handover_fail_pct",
        "gnb_cu_du_latency_ms",
        "ptp_sync_offset_us",
    ]
