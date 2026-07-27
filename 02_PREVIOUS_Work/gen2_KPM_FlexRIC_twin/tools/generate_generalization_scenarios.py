from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path


SERVICES = ["eMBB", "mMTC", "URLLC", "FWA", "V2X"]


BASE = {
    "eMBB": {"latency": 20, "jitter": 8, "throughput": 120, "loss": 0.5, "prb": 55, "handover": 0.8, "edge": 2.5, "backhaul": 4, "sinr": 22, "bler": 1.2},
    "mMTC": {"latency": 100, "jitter": 30, "throughput": 2, "loss": 2.0, "prb": 38, "handover": 0.2, "edge": 1.5, "backhaul": 5, "sinr": 18, "bler": 1.6},
    "URLLC": {"latency": 2, "jitter": 1, "throughput": 20, "loss": 0.01, "prb": 42, "handover": 0.5, "edge": 1.2, "backhaul": 2.4, "sinr": 24, "bler": 0.7},
    "FWA": {"latency": 30, "jitter": 6, "throughput": 180, "loss": 0.3, "prb": 64, "handover": 0.1, "edge": 2.0, "backhaul": 6, "sinr": 21, "bler": 1.1},
    "V2X": {"latency": 5, "jitter": 2, "throughput": 25, "loss": 0.05, "prb": 46, "handover": 2.0, "edge": 1.4, "backhaul": 2.8, "sinr": 23, "bler": 0.9},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate hard virtual O-RAN scenario data for generalization testing.")
    parser.add_argument("--config", default="configs/generalization_scenarios.json")
    parser.add_argument("--output", default="data/training/generalized_virtual_ran_scenarios.csv")
    parser.add_argument("--rows", type=int, default=60000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    rows = [build_row(i, config, rng) for i in range(args.rows)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows, output)
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def build_row(index: int, config: dict[str, object], rng: random.Random) -> dict[str, object]:
    areas = config["area_personas"]
    area_name = rng.choice(list(areas))
    area = areas[area_name]
    event_name = weighted_choice({"normal_day": 0.55, "festival": 0.12, "rain_peak": 0.12, "sports_event": 0.08, "industrial_shift_change": 0.13}, rng)
    weather_name = weighted_choice({"clear": 0.62, "heavy_rain": 0.18, "storm": 0.06, "dense_fog": 0.14}, rng)
    hour = rng.randrange(24)
    temporal_name, temporal = temporal_for_hour(config["temporal_factors"], hour)
    event = config["event_factors"][event_name]
    weather = config["weather_factors"][weather_name]
    service = weighted_choice(area["service_mix"], rng)
    base = dict(BASE[service])

    traffic = float(event["traffic_multiplier"]) * float(temporal["traffic_multiplier"]) * rng.uniform(0.84, 1.18)
    mobility = min(1.0, float(area["mobility_base"]) * float(temporal["mobility_multiplier"]) * rng.uniform(0.85, 1.15))
    density = min(1.0, float(area["density_base"]) * traffic * rng.uniform(0.82, 1.12))
    interference = min(1.0, float(area["interference_base"]) + (0.18 if weather_name in {"heavy_rain", "storm"} else 0) + rng.uniform(-0.08, 0.1))
    edge_pressure = min(1.0, float(area["edge_dependency"]) * traffic * rng.uniform(0.75, 1.15))

    k = {
        "latency_ms": base["latency"] * (0.62 + density * 0.55 + edge_pressure * 0.25) + rng.gauss(0, max(0.2, base["latency"] * 0.07)),
        "jitter_ms": base["jitter"] * (0.55 + density * 0.45 + mobility * 0.12) + rng.gauss(0, max(0.1, base["jitter"] * 0.05)),
        "throughput_mbps": base["throughput"] * max(0.18, 1.18 - density * 0.42 - interference * 0.16) + rng.gauss(0, max(0.2, base["throughput"] * 0.04)),
        "packet_loss_pct": base["loss"] * (0.55 + interference * 0.9 + density * 0.28),
        "prb_util_pct": min(100, base["prb"] + density * 42 + traffic * 11 + rng.gauss(0, 4)),
        "handover_fail_pct": base["handover"] * (0.5 + mobility * 1.4) * float(weather["handover_multiplier"]),
        "edge_delay_ms": base["edge"] * (0.7 + edge_pressure * 1.6),
        "backhaul_delay_ms": base["backhaul"] * (0.75 + traffic * 0.55) * float(weather["backhaul_multiplier"]),
        "sinr_db": base["sinr"] - interference * 11 - float(weather["sinr_penalty"]) + rng.gauss(0, 1.2),
        "bler_pct": base["bler"] * (0.7 + interference * 1.8 + density * 0.28),
    }
    add_phy_odu_kpis(k, density=density, mobility=mobility, interference=interference, traffic=traffic, rng=rng)
    add_oru_low_phy_kpis(k, interference=interference, weather_name=weather_name, rng=rng)
    add_ocu_kpis(k, density=density, mobility=mobility, traffic=traffic, service=service, rng=rng)
    add_core_transport_kpis(k, traffic=traffic, density=density, edge_pressure=edge_pressure, service=service, rng=rng)

    fault_type = infer_fault(k, area, event, rng)
    apply_fault(k, fault_type, rng)
    for key in k:
        k[key] = round(max(0.0, k[key]), 4)
    k["sinr_db"] = round(max(-5.0, min(40.0, k["sinr_db"])), 4)
    k["prb_util_pct"] = round(max(0.0, min(100.0, k["prb_util_pct"])), 4)
    k["cqi"] = round(max(0.0, min(15.0, k["cqi"])), 4)
    k["beam_quality_score"] = round(max(0.0, min(1.0, k["beam_quality_score"])), 4)
    k["harq_retx_pct"] = round(max(0.0, min(100.0, k["harq_retx_pct"])), 4)
    k["rlc_buffer_kbytes"] = round(max(0.0, k["rlc_buffer_kbytes"]), 4)
    k["mac_scheduler_delay_ms"] = round(max(0.0, k["mac_scheduler_delay_ms"]), 4)
    k["timing_offset_us"] = round(max(0.0, k["timing_offset_us"]), 4)
    k["fronthaul_delay_ms"] = round(max(0.0, k["fronthaul_delay_ms"]), 4)
    k["rsrp_dbm"] = round(max(-140.0, min(-55.0, k["rsrp_dbm"])), 4)
    k["rsrq_db"] = round(max(-25.0, min(-3.0, k["rsrq_db"])), 4)
    k["rssi_dbm"] = round(max(-120.0, min(-40.0, k["rssi_dbm"])), 4)
    k["noise_floor_dbm"] = round(max(-120.0, min(-80.0, k["noise_floor_dbm"])), 4)
    k["evm_pct"] = round(max(0.0, min(30.0, k["evm_pct"])), 4)
    k["interference_power_dbm"] = round(max(-125.0, min(-55.0, k["interference_power_dbm"])), 4)
    k["beam_misalignment_deg"] = round(max(0.0, min(45.0, k["beam_misalignment_deg"])), 4)
    k["antenna_vswr"] = round(max(1.0, min(4.0, k["antenna_vswr"])), 4)
    k["rf_temperature_c"] = round(max(20.0, min(105.0, k["rf_temperature_c"])), 4)
    k["rrc_setup_fail_pct"] = round(max(0.0, min(100.0, k["rrc_setup_fail_pct"])), 4)
    k["rrc_reestab_rate_pct"] = round(max(0.0, min(100.0, k["rrc_reestab_rate_pct"])), 4)
    k["pdcp_discard_rate_pct"] = round(max(0.0, min(100.0, k["pdcp_discard_rate_pct"])), 4)
    k["pdcp_reordering_delay_ms"] = round(max(0.0, k["pdcp_reordering_delay_ms"]), 4)
    k["sdap_qos_flow_drop_pct"] = round(max(0.0, min(100.0, k["sdap_qos_flow_drop_pct"])), 4)
    k["qfi_violation_pct"] = round(max(0.0, min(100.0, k["qfi_violation_pct"])), 4)
    k["session_drop_rate_pct"] = round(max(0.0, min(100.0, k["session_drop_rate_pct"])), 4)
    k["mobility_pingpong_pct"] = round(max(0.0, min(100.0, k["mobility_pingpong_pct"])), 4)
    k["amf_registration_fail_pct"] = round(max(0.0, min(100.0, k["amf_registration_fail_pct"])), 4)
    k["amf_paging_delay_ms"] = round(max(0.0, k["amf_paging_delay_ms"]), 4)
    k["pdu_session_setup_ms"] = round(max(0.0, k["pdu_session_setup_ms"]), 4)
    k["pdu_session_fail_pct"] = round(max(0.0, min(100.0, k["pdu_session_fail_pct"])), 4)
    k["upf_cpu_util_pct"] = round(max(0.0, min(100.0, k["upf_cpu_util_pct"])), 4)
    k["upf_packet_drop_pct"] = round(max(0.0, min(100.0, k["upf_packet_drop_pct"])), 4)
    k["gtp_tunnel_loss_pct"] = round(max(0.0, min(100.0, k["gtp_tunnel_loss_pct"])), 4)
    k["n3_rtt_ms"] = round(max(0.0, k["n3_rtt_ms"]), 4)
    k["n6_internet_rtt_ms"] = round(max(0.0, k["n6_internet_rtt_ms"]), 4)
    k["transport_jitter_ms"] = round(max(0.0, k["transport_jitter_ms"]), 4)

    return {
        "t": index,
        "cell_id": f"VIRTUAL_{area_name.upper()}_{index % 9}",
        "area_persona": area_name,
        "hour": hour,
        "temporal_context": temporal_name,
        "event_context": event_name,
        "weather_context": weather_name,
        "service_class": service,
        "mobility_index": round(mobility, 4),
        "density_index": round(density, 4),
        "interference_index": round(interference, 4),
        "edge_pressure_index": round(edge_pressure, 4),
        "fault_active": fault_type != "normal",
        "fault_type": fault_type,
        "aml_attack_active": False,
        "aml_attack_type": "none",
        **k,
    }


def add_phy_odu_kpis(
    k: dict[str, float],
    *,
    density: float,
    mobility: float,
    interference: float,
    traffic: float,
    rng: random.Random,
) -> None:
    """Derive O-RU/O-DU-adjacent KPIs from the same radio/load state.

    These are still virtual features, but they have physical meaning:
    CQI and beam quality follow SINR/interference, HARQ follows BLER/SINR,
    RLC buffer and MAC scheduler delay follow PRB/load, and timing/fronthaul
    pressure follows jitter/mobility/load.
    """
    k["cqi"] = 2.0 + (k["sinr_db"] + 5.0) / 45.0 * 13.0 - interference * 1.4 + rng.gauss(0, 0.55)
    k["harq_retx_pct"] = 0.8 + k["bler_pct"] * 1.65 + max(0.0, 10.0 - k["sinr_db"]) * 0.42 + rng.gauss(0, 0.45)
    k["rlc_buffer_kbytes"] = 80.0 + density * 620.0 + max(0.0, k["prb_util_pct"] - 65.0) * 14.0 + rng.gauss(0, 35.0)
    k["mac_scheduler_delay_ms"] = 0.6 + max(0.0, k["prb_util_pct"] - 55.0) * 0.12 + density * 2.2 + rng.gauss(0, 0.35)
    k["beam_quality_score"] = 1.0 - min(0.92, interference * 0.7 + max(0.0, 14.0 - k["sinr_db"]) * 0.025)
    k["timing_offset_us"] = 1.2 + k["jitter_ms"] * 0.35 + mobility * 3.2 + rng.gauss(0, 0.8)
    k["fronthaul_delay_ms"] = 0.7 + traffic * 0.95 + density * 0.72 + rng.gauss(0, 0.18)


def add_oru_low_phy_kpis(
    k: dict[str, float],
    *,
    interference: float,
    weather_name: str,
    rng: random.Random,
) -> None:
    rain_penalty = 4.0 if weather_name == "heavy_rain" else 7.0 if weather_name == "storm" else 1.2 if weather_name == "dense_fog" else 0.0
    k["rsrp_dbm"] = -82.0 - interference * 21.0 - rain_penalty + rng.gauss(0, 2.2)
    k["rsrq_db"] = -8.0 - interference * 8.5 - max(0.0, k["bler_pct"] - 1.0) * 0.35 + rng.gauss(0, 0.9)
    k["rssi_dbm"] = k["rsrp_dbm"] + 8.0 + interference * 12.0 + rng.gauss(0, 1.4)
    k["noise_floor_dbm"] = -104.0 + interference * 10.0 + rng.gauss(0, 1.2)
    k["evm_pct"] = 2.2 + interference * 8.0 + max(0.0, 12.0 - k["sinr_db"]) * 0.32 + rng.gauss(0, 0.55)
    k["interference_power_dbm"] = -102.0 + interference * 35.0 + rng.gauss(0, 2.5)
    k["beam_misalignment_deg"] = max(0.0, interference * 14.0 + (rain_penalty * 0.6) + rng.gauss(0, 2.0))
    k["antenna_vswr"] = 1.12 + max(0.0, interference - 0.62) * 1.2 + rng.gauss(0, 0.08)
    k["rf_temperature_c"] = 41.0 + interference * 18.0 + rng.gauss(0, 2.5)


def add_ocu_kpis(
    k: dict[str, float],
    *,
    density: float,
    mobility: float,
    traffic: float,
    service: str,
    rng: random.Random,
) -> None:
    qos_weight = 1.4 if service in {"URLLC", "V2X"} else 1.15 if service in {"eMBB", "FWA"} else 0.85
    mobility_weight = 1.35 if service in {"V2X", "eMBB"} else 0.8
    k["rrc_setup_fail_pct"] = 0.4 + density * 2.6 + mobility * 1.2 + rng.gauss(0, 0.25)
    k["rrc_reestab_rate_pct"] = 0.25 + mobility * 2.4 * mobility_weight + max(0.0, k["handover_fail_pct"] - 1.5) * 0.42 + rng.gauss(0, 0.2)
    k["pdcp_discard_rate_pct"] = 0.2 + max(0.0, k["packet_loss_pct"] - 0.4) * 0.7 + density * 0.8 + rng.gauss(0, 0.18)
    k["pdcp_reordering_delay_ms"] = 0.8 + k["jitter_ms"] * 0.35 + mobility * 2.6 + rng.gauss(0, 0.35)
    k["sdap_qos_flow_drop_pct"] = 0.15 + qos_weight * max(0.0, traffic - 1.0) * 1.4 + max(0.0, k["latency_ms"] - 25.0) * 0.015 + rng.gauss(0, 0.15)
    k["qfi_violation_pct"] = 0.2 + qos_weight * max(0.0, k["latency_ms"] - 18.0) * 0.035 + max(0.0, k["throughput_mbps"] * -0.002 + 0.4) + rng.gauss(0, 0.2)
    k["session_drop_rate_pct"] = 0.12 + max(0.0, k["packet_loss_pct"] - 1.0) * 0.32 + max(0.0, k["rrc_setup_fail_pct"] - 2.0) * 0.22 + rng.gauss(0, 0.12)
    k["mobility_pingpong_pct"] = 0.3 + mobility * 3.2 * mobility_weight + max(0.0, k["handover_fail_pct"] - 1.0) * 0.5 + rng.gauss(0, 0.3)


def add_core_transport_kpis(
    k: dict[str, float],
    *,
    traffic: float,
    density: float,
    edge_pressure: float,
    service: str,
    rng: random.Random,
) -> None:
    critical = 1.25 if service in {"URLLC", "V2X"} else 1.0
    broadband = 1.25 if service in {"eMBB", "FWA"} else 0.75
    k["amf_registration_fail_pct"] = 0.15 + density * 0.8 + max(0.0, traffic - 1.15) * 0.7 + rng.gauss(0, 0.08)
    k["amf_paging_delay_ms"] = 22.0 + density * 25.0 + traffic * 10.0 + rng.gauss(0, 2.2)
    k["pdu_session_setup_ms"] = 55.0 + traffic * 28.0 + density * 18.0 + rng.gauss(0, 4.0)
    k["pdu_session_fail_pct"] = 0.12 + max(0.0, k["amf_registration_fail_pct"] - 0.8) * 0.65 + rng.gauss(0, 0.06)
    k["upf_cpu_util_pct"] = 38.0 + traffic * 24.0 * broadband + density * 12.0 + rng.gauss(0, 3.0)
    k["upf_packet_drop_pct"] = 0.08 + max(0.0, k["upf_cpu_util_pct"] - 70.0) * 0.045 + max(0.0, traffic - 1.1) * 0.7 + rng.gauss(0, 0.08)
    k["gtp_tunnel_loss_pct"] = 0.05 + k["upf_packet_drop_pct"] * 0.45 + max(0.0, k["backhaul_delay_ms"] - 7.0) * 0.04 + rng.gauss(0, 0.05)
    k["n3_rtt_ms"] = 8.0 + k["backhaul_delay_ms"] * 1.7 + traffic * 4.0 + rng.gauss(0, 1.0)
    k["n6_internet_rtt_ms"] = 24.0 + edge_pressure * 16.0 + traffic * 14.0 * critical + rng.gauss(0, 2.5)
    k["transport_jitter_ms"] = 1.5 + k["jitter_ms"] * 0.22 + max(0.0, traffic - 1.0) * 5.0 + rng.gauss(0, 0.6)


def infer_fault(k: dict[str, float], area: dict[str, object], event: dict[str, object], rng: random.Random) -> str:
    probability = 0.05 * float(event["fault_probability_multiplier"])
    if k["prb_util_pct"] > 88:
        probability += 0.22
    if k["sinr_db"] < 8:
        probability += 0.18
    if k["handover_fail_pct"] > 4:
        probability += 0.12
    if k.get("sdap_qos_flow_drop_pct", 0) > 1.8 or k.get("qfi_violation_pct", 0) > 2.5 or k.get("session_drop_rate_pct", 0) > 1.5:
        probability += 0.1
    if k.get("upf_cpu_util_pct", 0) > 82 or k.get("n6_internet_rtt_ms", 0) > 90 or k.get("pdu_session_fail_pct", 0) > 3:
        probability += 0.1
    if rng.random() > min(0.92, probability):
        return "normal"
    candidates = list(area["dominant_faults"])
    if k["prb_util_pct"] > 86:
        candidates += ["cell_congestion"] * 3
    if k["sinr_db"] < 7:
        candidates += ["spectrum_interference"] * 3
    if k["handover_fail_pct"] > 4:
        candidates += ["handover_instability"] * 3
    if k.get("sdap_qos_flow_drop_pct", 0) > 1.8 or k.get("qfi_violation_pct", 0) > 2.5 or k.get("session_drop_rate_pct", 0) > 1.5:
        candidates += ["qos_session_degradation"] * 3
    if k.get("pdu_session_fail_pct", 0) > 1.2 or k.get("amf_paging_delay_ms", 0) > 52:
        candidates += ["core_control_plane_degradation"] * 2
    if k.get("upf_cpu_util_pct", 0) > 72 or k.get("gtp_tunnel_loss_pct", 0) > 1.5:
        candidates += ["upf_user_plane_congestion"] * 3
    if k.get("n6_internet_rtt_ms", 0) > 58 or k.get("transport_jitter_ms", 0) > 10:
        candidates += ["transport_path_degradation"] * 2
    return rng.choice(candidates)


def apply_fault(k: dict[str, float], fault: str, rng: random.Random) -> None:
    severity = rng.uniform(0.45, 0.95)
    if fault == "cell_congestion":
        k["prb_util_pct"] += 18 * severity
        k["latency_ms"] += 35 * severity
        k["throughput_mbps"] *= 1 - 0.25 * severity
        k["packet_loss_pct"] += 1.2 * severity
        k["rlc_buffer_kbytes"] += 520 * severity
        k["mac_scheduler_delay_ms"] += 6.5 * severity
    elif fault == "spectrum_interference":
        k["sinr_db"] -= 8 * severity
        k["bler_pct"] += 4 * severity
        k["throughput_mbps"] *= 1 - 0.22 * severity
        k["cqi"] -= 4.5 * severity
        k["harq_retx_pct"] += 8.0 * severity
        k["beam_quality_score"] -= 0.28 * severity
        k["rsrq_db"] -= 4.2 * severity
        k["evm_pct"] += 6.5 * severity
        k["interference_power_dbm"] += 18.0 * severity
        k["beam_misalignment_deg"] += 11.0 * severity
    elif fault == "handover_instability":
        k["handover_fail_pct"] += 7 * severity
        k["latency_ms"] += 10 * severity
        k["packet_loss_pct"] += 0.6 * severity
        k["mac_scheduler_delay_ms"] += 2.2 * severity
        k["rrc_reestab_rate_pct"] += 5.0 * severity
        k["mobility_pingpong_pct"] += 7.0 * severity
        k["rrc_setup_fail_pct"] += 2.5 * severity
    elif fault == "edge_overload":
        k["edge_delay_ms"] += 18 * severity
        k["latency_ms"] += 12 * severity
    elif fault == "backhaul_degradation":
        k["backhaul_delay_ms"] += 20 * severity
        k["latency_ms"] += 18 * severity
        k["jitter_ms"] += 8 * severity
    elif fault == "timing_drift":
        k["jitter_ms"] += 10 * severity
        k["bler_pct"] += 3 * severity
        k["timing_offset_us"] += 18 * severity
        k["fronthaul_delay_ms"] += 3.2 * severity
        k["harq_retx_pct"] += 3.8 * severity
    elif fault == "packet_loss_burst":
        k["packet_loss_pct"] += 5 * severity
        k["jitter_ms"] += 5 * severity
        k["harq_retx_pct"] += 4.5 * severity
        k["pdcp_discard_rate_pct"] += 4.0 * severity
        k["session_drop_rate_pct"] += 1.8 * severity
    elif fault == "qos_session_degradation":
        k["sdap_qos_flow_drop_pct"] += 7.0 * severity
        k["qfi_violation_pct"] += 9.0 * severity
        k["pdcp_discard_rate_pct"] += 3.6 * severity
        k["pdcp_reordering_delay_ms"] += 7.0 * severity
        k["session_drop_rate_pct"] += 4.2 * severity
        k["latency_ms"] += 6.0 * severity
    elif fault == "core_control_plane_degradation":
        k["amf_registration_fail_pct"] += 4.5 * severity
        k["amf_paging_delay_ms"] += 80.0 * severity
        k["pdu_session_setup_ms"] += 150.0 * severity
        k["pdu_session_fail_pct"] += 4.0 * severity
        k["session_drop_rate_pct"] += 1.2 * severity
    elif fault == "upf_user_plane_congestion":
        k["upf_cpu_util_pct"] += 34.0 * severity
        k["upf_packet_drop_pct"] += 4.0 * severity
        k["gtp_tunnel_loss_pct"] += 3.5 * severity
        k["n3_rtt_ms"] += 35.0 * severity
        k["throughput_mbps"] *= 1 - 0.18 * severity
    elif fault == "transport_path_degradation":
        k["n6_internet_rtt_ms"] += 80.0 * severity
        k["transport_jitter_ms"] += 18.0 * severity
        k["gtp_tunnel_loss_pct"] += 1.8 * severity
        k["backhaul_delay_ms"] += 14.0 * severity
        k["latency_ms"] += 16.0 * severity
    if fault == "radio_quality_degradation":
        k["antenna_vswr"] += 1.2 * severity
        k["rf_temperature_c"] += 30.0 * severity
        k["rsrp_dbm"] -= 8.0 * severity
        k["rsrq_db"] -= 3.0 * severity


def temporal_for_hour(factors: dict[str, dict[str, object]], hour: int) -> tuple[str, dict[str, object]]:
    for name, item in factors.items():
        if hour in item["hours"]:
            return name, item
    return "normal_hour", {"mobility_multiplier": 1.0, "traffic_multiplier": 1.0}


def weighted_choice(weights: dict[str, float], rng: random.Random) -> str:
    total = sum(float(value) for value in weights.values())
    cursor = rng.random() * total
    running = 0.0
    for key, value in weights.items():
        running += float(value)
        if cursor <= running:
            return key
    return next(iter(weights))


def summarize(rows: list[dict[str, object]], output: Path) -> dict[str, object]:
    from collections import Counter

    return {
        "output": str(output),
        "rows": len(rows),
        "service_counts": dict(Counter(str(row["service_class"]) for row in rows)),
        "area_counts": dict(Counter(str(row["area_persona"]) for row in rows)),
        "event_counts": dict(Counter(str(row["event_context"]) for row in rows)),
        "weather_counts": dict(Counter(str(row["weather_context"]) for row in rows)),
        "fault_counts": dict(Counter(str(row["fault_type"]) for row in rows)),
    }


if __name__ == "__main__":
    main()
