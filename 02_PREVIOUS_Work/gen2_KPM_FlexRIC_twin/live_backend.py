from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import sqlite3
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from oran_twin.device_population import DevicePopulationModel
from oran_twin.engine import OranDecisionEngine
from oran_twin.model_registry import ModelRegistry
from oran_twin.persistence import DecisionStore
from oran_twin.telemetry_adapters import build_adapter


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
LOG_PATH = ROOT / "outputs" / "live_backend.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


CELLS = [
    {"id": "CELL_A", "site": "MG Road / CBD", "lat": 12.9756, "lon": 77.6069, "edge": "MEC_1", "baseLoad": 0.58},
    {"id": "CELL_B", "site": "Manyata Tech Park", "lat": 13.0498, "lon": 77.6200, "edge": "MEC_1", "baseLoad": 0.72},
    {"id": "CELL_C", "site": "Electronic City", "lat": 12.8399, "lon": 77.6770, "edge": "MEC_2", "baseLoad": 0.64},
    {"id": "CELL_D", "site": "Whitefield", "lat": 12.9698, "lon": 77.7500, "edge": "MEC_3", "baseLoad": 0.68},
    {"id": "CELL_E", "site": "Hebbal Airport Road", "lat": 13.0358, "lon": 77.5970, "edge": "MEC_1", "baseLoad": 0.61},
    {"id": "CELL_F", "site": "Outer Ring Road", "lat": 12.9237, "lon": 77.6704, "edge": "MEC_2", "baseLoad": 0.76},
    {"id": "CELL_G", "site": "Yelahanka", "lat": 13.1007, "lon": 77.5963, "edge": "MEC_1", "baseLoad": 0.44},
    {"id": "CELL_H", "site": "Jayanagar", "lat": 12.9250, "lon": 77.5938, "edge": "MEC_2", "baseLoad": 0.52},
]


MEC_NODES = [
    {"id": "MEC_1", "site": "North Edge Cloud", "lat": 13.0350, "lon": 77.6150},
    {"id": "MEC_2", "site": "South Edge Cloud", "lat": 12.9000, "lon": 77.6500},
    {"id": "MEC_3", "site": "East Edge Cloud", "lat": 12.9700, "lon": 77.7200},
]


def load_service_profiles() -> dict[str, dict[str, Any]]:
    raw = json.loads((ROOT / "configs" / "service_profiles.json").read_text(encoding="utf-8"))
    profiles: dict[str, dict[str, Any]] = {}
    for service, profile in raw.items():
        profiles[service] = {
            "label": profile["description"].split(":", 1)[0],
            "description": profile["description"],
            "latency": profile["latency_ms_target"],
            "jitter": profile["jitter_ms_target"],
            "throughput": profile["throughput_mbps_target"],
            "loss": profile["packet_loss_pct_target"],
            "reliability": profile["reliability_pct_target"],
            "availability": profile["availability_pct_target"],
            "bandwidth": profile["bandwidth_mhz"],
            "packetSize": profile["packet_size"],
            "packetFrequency": profile["packet_frequency"],
            "mobility": profile["mobility_level"],
            "density": profile["density_level"],
            "connectionDensity": profile["connection_density"],
            "deviceDensity": profile["device_density"],
            "edge": profile["edge_dependency_level"],
            "security": profile["security_level"],
            "priority": profile["priority_weight"],
            "weight": str(profile["ai_optimization_weight"]).title(),
            "parameters": profile,
        }
    return profiles


SERVICE_PROFILES = load_service_profiles()


def load_openran_kpm_dataset_summary() -> dict[str, Any]:
    training_path = ROOT / "data" / "training" / "open_ran_kpm_training_dataset.csv"
    training_summary_path = ROOT / "data" / "training" / "open_ran_kpm_training_dataset.summary.json"
    aux_summary_path = ROOT / "data" / "training" / "open_ran_aux_metrics_summary.json"
    app_qos_path = ROOT / "data" / "training" / "open_ran_app_qos_summary.csv"
    cell_load_path = ROOT / "data" / "training" / "open_ran_cell_load_summary.csv"
    benchmark_path = ROOT / "outputs" / "benchmarks" / "ml_model_comparison_v2.json"
    legacy_benchmark_path = ROOT / "outputs" / "benchmarks" / "open_ran_kpm_model_comparison.json"

    return {
        "trainingSummary": read_json_file(training_summary_path),
        "auxSummary": read_json_file(aux_summary_path),
        "benchmark": compact_benchmark(read_json_file(benchmark_path) or read_json_file(legacy_benchmark_path)),
        "trainingSamples": read_csv_sample(training_path, limit=8),
        "appQosSamples": read_csv_sample(app_qos_path, limit=6),
        "cellLoadSamples": read_csv_sample(cell_load_path, limit=6),
        "paths": {
            "training": str(training_path),
            "trainingSummary": str(training_summary_path),
            "auxSummary": str(aux_summary_path),
            "appQos": str(app_qos_path),
            "cellLoad": str(cell_load_path),
            "benchmark": str(benchmark_path if benchmark_path.exists() else legacy_benchmark_path),
        },
    }


def load_live_telemetry_status() -> dict[str, Any]:
    raw_runtime = ROOT / "data" / "telemetry" / "raw" / "oai_runtime.log"
    live_metrics = ROOT / "data" / "telemetry" / "raw" / "live_oai_metrics.log"
    decisions = ROOT / "outputs" / "live_oai_decisions.jsonl"
    smoke_decisions = ROOT / "outputs" / "live_oai_decisions_smoke.jsonl"
    report = ROOT / "outputs" / "reports" / "live_oai_run_report.json"
    store = DecisionStore()
    return {
        "raw_runtime_log": file_status(raw_runtime),
        "live_metrics_log": file_status(live_metrics),
        "live_decisions": file_status(decisions if decisions.exists() else smoke_decisions),
        "latest_report": read_json_file(report),
        "sqlite": store.live_counts(),
        "flow": [
            "WSL OAI/FlexRIC logs",
            "data/telemetry/raw/oai_runtime.log",
            "tools/oai_metric_bridge.py",
            "data/telemetry/raw/live_oai_metrics.log",
            "tools/stream_live_oai_to_engine.py",
            "outputs/oran_twin.sqlite + outputs/live_oai_decisions.jsonl",
        ],
    }


def file_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "path": str(path), "lines": 0, "bytes": 0}
    stat = path.stat()
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            lines = sum(1 for _ in handle)
    except OSError:
        lines = 0
    return {
        "available": True,
        "path": str(path),
        "lines": lines,
        "bytes": stat.st_size,
        "modified_epoch": stat.st_mtime,
    }


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "path": str(path)}
    return {"available": True, **json.loads(path.read_text(encoding="utf-8"))}


def read_csv_sample(path: Path, limit: int) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def compact_benchmark(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("available", True):
        return payload
    benchmarks = payload.get("benchmarks", [])
    return {
        "available": True,
        "rows_evaluated": payload.get("rows_evaluated", 0),
        "dataset_profile": payload.get("dataset_profile", {}),
        "benchmarks": [
            {
                "name": item.get("name"),
                "precision": item.get("precision"),
                "recall": item.get("recall"),
                "f1_score": item.get("f1_score"),
                "rca_accuracy_on_prediction_records": item.get("rca_accuracy_on_prediction_records"),
            }
            for item in benchmarks
        ],
    }


def build_openran_kpm_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ueId": row.get("ue_id", ""),
        "serviceClass": row.get("service_class", ""),
        "faultType": row.get("fault_type", "normal"),
        "faultActive": _bool(row.get("fault_active", False)),
        "sliceId": row.get("slice_id", ""),
        "slicePrb": row.get("slice_prb", ""),
        "schedulingPolicy": row.get("scheduling_policy", ""),
        "prbGrantRatio": row.get("prb_grant_ratio", ""),
        "dlCqi": row.get("dl_cqi", ""),
        "dlMcs": row.get("dl_mcs", ""),
        "ulMcs": row.get("ul_mcs", ""),
        "cluster": row.get("cluster", ""),
        "slicing": row.get("slicing", ""),
        "scheduling": row.get("scheduling", ""),
        "reservation": row.get("reservation", ""),
        "labelQuality": row.get("label_quality", ""),
        "sourceFile": row.get("source_file", ""),
    }


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Scenario:
    service: str = "eMBB"
    target_cell: str = "CELL_A"
    fault_type: str = "normal"
    severity: float = 0.65
    network_load: float = 0.6
    mobility: float = 0.5
    weather_impact_override: float | None = None
    healing_mode: str = "twin_validated"


@dataclass
class LiveState:
    scenario: Scenario = field(default_factory=Scenario)
    t: int = 0
    current: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    weather: dict[str, Any] = field(default_factory=dict)
    last_weather_fetch: float = 0.0
    telemetry_mode: str = "profile_simulation"
    telemetry_source: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    running: bool = True


class LiveTwinEngine:
    def __init__(self, self_learning_model_path: str | Path | None = None) -> None:
        self.state = LiveState()
        self.rng = random.Random(7)
        self.adapter = build_adapter(self.state.telemetry_mode, self.state.telemetry_source)
        self.self_learning_model_path = Path(self_learning_model_path) if self_learning_model_path else None
        self.engine = OranDecisionEngine(self_learning_model_path=self.self_learning_model_path)
        self.population_model = DevicePopulationModel()
        self.model_registry = ModelRegistry()
        self.store = DecisionStore()

    def loop(self) -> None:
        while self.state.running:
            with self.state.lock:
                self.state.t += 1
                self._refresh_weather_if_needed()
                self.state.current = self._evaluate()
                self.state.history.append(self.state.current)
                self.state.history = self.state.history[-300:]
            time.sleep(1)

    def set_scenario(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.state.lock:
            for key, value in payload.items():
                if hasattr(self.state.scenario, key):
                    if key in {"severity", "network_load", "mobility"}:
                        value = max(0.0, min(1.0, float(value)))
                    if key == "weather_impact_override" and value is not None:
                        value = max(0.0, min(1.0, float(value)))
                    setattr(self.state.scenario, key, value)
            if self.state.scenario.service not in SERVICE_PROFILES:
                self.state.scenario.service = "eMBB"
            if not any(cell["id"] == self.state.scenario.target_cell for cell in CELLS):
                self.state.scenario.target_cell = CELLS[0]["id"]
            self.state.current = self._evaluate()
            return self.snapshot()

    def set_telemetry(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.state.lock:
            mode = str(payload.get("mode", self.state.telemetry_mode))
            source = payload.get("source", self.state.telemetry_source)
            source = str(source) if source not in {None, ""} else None
            self.state.telemetry_mode = mode
            self.state.telemetry_source = source
            self.adapter = build_adapter(mode, source)
            self.engine.reset()
            self.state.current = self._evaluate()
            logging.info("telemetry_changed mode=%s source=%s", mode, source)
            return self.snapshot()

    def reset(self) -> dict[str, Any]:
        with self.state.lock:
            self.state.scenario = Scenario()
            self.state.t = 0
            self.state.history.clear()
            self.engine.reset()
            self.state.current = self._evaluate()
            logging.info("scenario_reset")
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "t": self.state.t,
            "telemetry": self.adapter.describe(),
            "profiles": SERVICE_PROFILES,
            "cells": CELLS,
            "mecNodes": MEC_NODES,
            "scenario": self.state.scenario.__dict__,
            "weather": self.state.weather,
            "modelRegistry": self.model_registry.snapshot(),
            "sources": {
                "service_profiles": "configs/service_profiles.json",
                "profile_notes": "configs/profile_sources.md",
                "weather": "Open-Meteo Forecast API for Bengaluru when reachable",
                "standards_basis": "3GPP TS 23.501 5QI/QoS and ITU IMT-2020 service requirements",
            },
            "current": self.state.current,
            "history": self.state.history[-80:],
        }

    def health(self) -> dict[str, Any]:
        current = self.state.current.get("selected", {}) if self.state.current else {}
        return {
            "status": "ok",
            "time": int(time.time()),
            "telemetry_mode": self.state.telemetry_mode,
            "history_records": len(self.state.history),
            "selected_cell": current.get("id"),
            "risk": current.get("risk"),
            "automation_safety_score": current.get("automationSafety", {}).get("score"),
            "database": str(self.store.path),
            "log": str(LOG_PATH),
        }

    def _refresh_weather_if_needed(self) -> None:
        now = time.time()
        if now - self.state.last_weather_fetch < 600 and self.state.weather:
            return
        self.state.last_weather_fetch = now
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=12.9716&longitude=77.5946&current=temperature_2m,precipitation,rain,wind_speed_10m"
            "&timezone=Asia%2FKolkata"
        )
        try:
            with urllib.request.urlopen(url, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
            current = data.get("current", {})
            rain = float(current.get("rain", 0) or 0)
            precipitation = float(current.get("precipitation", 0) or 0)
            wind = float(current.get("wind_speed_10m", 0) or 0)
            weather_impact = min(1.0, rain * 0.18 + precipitation * 0.12 + max(0, wind - 20) * 0.02)
            self.state.weather = {
                "source": "Open-Meteo",
                "mode": "live",
                "temperature_2m": current.get("temperature_2m"),
                "rain": rain,
                "precipitation": precipitation,
                "wind_speed_10m": wind,
                "weather_impact": round(weather_impact, 3),
                "time": current.get("time"),
            }
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            self.state.weather = {
                "source": "Open-Meteo",
                "mode": "fallback",
                "error": str(exc),
                "weather_impact": 0.1,
            }

    def _evaluate(self) -> dict[str, Any]:
        scenario = self.state.scenario
        service = scenario.service if scenario.service in SERVICE_PROFILES else "eMBB"
        profile = SERVICE_PROFILES[service]
        selected_cell = next((cell for cell in CELLS if cell["id"] == scenario.target_cell), CELLS[0])
        weather_impact = (
            scenario.weather_impact_override
            if scenario.weather_impact_override is not None
            else float(self.state.weather.get("weather_impact", 0.1))
        )
        cells = []
        selected_result = None
        for cell in CELLS:
            cell_result = self._evaluate_cell(cell, selected_cell, profile, scenario, weather_impact)
            cells.append(cell_result)
            if cell["id"] == selected_cell["id"]:
                selected_result = cell_result
        assert selected_result is not None
        active_service = str(selected_result.get("service", service))
        active_fault = str(selected_result.get("fault", scenario.fault_type))
        population = self.population_model.assess(
            cells=CELLS,
            selected_cell_id=selected_cell["id"],
            active_service=active_service,
            risk_by_cell={str(item["id"]): float(item["risk"]) for item in cells},
            fault_type=active_fault,
            severity=scenario.severity,
            network_load=scenario.network_load,
            mobility=scenario.mobility,
        )
        return {
            "service": active_service,
            "profile": profile,
            "targetCell": selected_cell["id"],
            "cells": cells,
            "selected": selected_result,
            "devicePopulation": {
                "totalDevices": population.total_devices,
                "activeDevices": population.active_devices,
                "affectedDevices": population.affected_devices,
                "byService": population.by_service,
                "representativeUes": population.representative_ues,
            },
            "overallState": self._state_label(float(selected_result["risk"])),
        }

    def _evaluate_cell(
        self,
        cell: dict[str, Any],
        selected_cell: dict[str, Any],
        profile: dict[str, Any],
        scenario: Scenario,
        weather_impact: float,
    ) -> dict[str, Any]:
        selected = cell["id"] == selected_cell["id"]
        fault = scenario.fault_type if selected else "normal"
        kpis = self.adapter.sample(
            t=self.state.t,
            cell=cell,
            selected_cell=selected_cell,
            profile=profile,
            scenario=scenario,
            weather_impact=weather_impact,
        )
        telemetry_row = kpis.get("_telemetry_row") if isinstance(kpis.get("_telemetry_row"), dict) else {}
        telemetry_service = str(telemetry_row.get("service_class") or scenario.service)
        telemetry_fault = str(telemetry_row.get("fault_type") or fault)
        telemetry_fault_active = _bool(telemetry_row.get("fault_active", fault != "normal"))
        if telemetry_service not in SERVICE_PROFILES:
            telemetry_service = scenario.service
        if selected and self.state.telemetry_mode == "open_ran_kpm_replay":
            fault = telemetry_fault
            profile = SERVICE_PROFILES.get(telemetry_service, profile)
        decision = self.engine.assess(
            {
                **kpis,
                "t": self.state.t,
                "cell_id": cell["id"],
                "site": cell["site"],
                "lat": cell["lat"],
                "lon": cell["lon"],
                "edge_node": cell["edge"],
                "service": telemetry_service if selected else scenario.service,
                "fault": fault,
                "fault_active": (
                    telemetry_fault_active
                    if selected and self.state.telemetry_mode == "open_ran_kpm_replay"
                    else fault != "normal"
                    and fault not in {"telemetry_poisoning", "model_evasion_attack", "unsafe_xapp_action"}
                ),
                "aml_attack_active": fault in {"telemetry_poisoning", "model_evasion_attack", "unsafe_xapp_action"},
                "aml_attack_type": fault
                if fault in {"telemetry_poisoning", "model_evasion_attack", "unsafe_xapp_action"}
                else "none",
            }
        )
        self.store.record_decision(run_name="live", mode=self.state.telemetry_mode, decision=decision)
        logging.info(
            "decision cell=%s service=%s fault=%s risk=%.4f safety=%.4f action=%s",
            cell["id"],
            scenario.service,
            fault,
            float(decision["twin_risk_score"]),
            float(decision["automation_safety_score"]),
            decision["healing_action"],
        )
        risk = float(decision["twin_risk_score"])
        root = str(decision["root_cause"])
        action = str(decision["healing_action"])
        reason = str(decision["healing_reason"])
        validation = {
            "approved": bool(decision["action_approved_by_twin"]),
            "postRisk": decision["post_action_risk_score"],
            "note": decision["validation_note"],
        }
        return {
            **cell,
            "selected": selected,
            "fault": fault,
            "service": telemetry_service if selected else scenario.service,
            "openRanKpm": build_openran_kpm_context(telemetry_row) if selected and telemetry_row else None,
            "amlAttack": {
                "active": decision["aml_attack_active"],
                "type": decision["aml_attack_type"],
            },
            "kpis": kpis,
            "risk": round(risk, 4),
            "state": self._state_label(risk),
            "rootCause": root,
            "healingAction": action,
            "healingReason": reason,
            "validation": validation,
            "automationSafety": {
                "score": decision["automation_safety_score"],
                "decision": decision["automation_safety_decision"],
                "baselineAction": decision["automation_baseline_action"],
                "baselineWouldExecute": decision["automation_baseline_would_execute"],
                "guardedWouldExecute": decision["automation_guarded_would_execute"],
                "unsafeActionPrevented": decision["unsafe_action_prevented"],
                "improvement": decision["automation_improvement"],
                "evidence": decision["automation_safety_evidence"],
            },
            "confidence": decision["ai_confidence"],
            "security": {
                "aiTrustScore": decision["ai_trust_score"],
                "amlThreatLevel": decision["aml_threat_level"],
                "amlThreatType": decision["aml_threat_type"],
                "guardAction": decision["security_guard_action"],
                "automationAllowed": decision["security_guard_action"] in {"allow_automation", "allow_with_monitoring"},
                "reasons": decision["security_guard_reasons"],
            },
            "drift": {
                "score": decision["drift_score"],
                "status": decision["drift_status"],
                "type": decision["drift_type"],
                "adaptationAction": decision["drift_adaptation_action"],
                "modelProfileId": decision["drift_model_profile_id"],
                "lifecycleStage": decision["drift_lifecycle_stage"],
                "retrainingPriority": decision["drift_retraining_priority"],
                "automationMode": decision["drift_automation_mode"],
                "reasons": decision["drift_reasons"],
            },
            "xappConflict": {
                "detected": decision["xapp_conflict_detected"],
                "type": decision["xapp_conflict_type"],
                "selectedXapp": decision["xapp_selected"],
                "mitigationStrategy": decision["xapp_mitigation_strategy"],
                "distillationState": decision["xapp_distillation_state"],
                "replayRecord": decision["xapp_replay_record"],
                "proposals": decision["xapp_proposals"],
                "reasons": decision["xapp_conflict_reasons"],
            },
            "timing": {
                "riskScore": decision["timing_risk_score"],
                "state": decision["timing_state"],
                "strideThreats": decision["timing_stride_threats"],
                "ptpDomain": decision["timing_ptp_domain"],
                "clockRole": decision["timing_clock_role"],
                "estimatedPtpOffsetUs": decision["timing_estimated_ptp_offset_us"],
                "syncState": decision["timing_sync_state"],
                "strideTestCase": decision["timing_stride_test_case"],
                "attackSurface": decision["timing_attack_surface"],
                "recommendedAction": decision["timing_recommended_action"],
                "remediationPlan": decision["timing_remediation_plan"],
                "reasons": decision["timing_reasons"],
            },
            "spectrum": {
                "riskScore": decision["spectrum_risk_score"],
                "state": decision["spectrum_state"],
                "action": decision["spectrum_action"],
                "band": decision["spectrum_band"],
                "channel": decision["spectrum_channel"],
                "backupBand": decision["spectrum_backup_band"],
                "channelOccupancy": decision["spectrum_channel_occupancy"],
                "spectralEfficiency": decision["spectrum_efficiency"],
                "interferenceSource": decision["spectrum_interference_source"],
                "dsaPolicy": decision["spectrum_dsa_policy"],
                "dsaConfidence": decision["spectrum_dsa_confidence"],
                "reasons": decision["spectrum_reasons"],
            },
            "sliceImpact": {
                "score": decision["slice_impact_score"],
                "level": decision["sla_impact_level"],
                "customerImpact": decision["customer_impact"],
                "revenueRisk": decision["revenue_risk"],
                "sliceId": decision["slice_id"],
                "tenantSegment": decision["tenant_segment"],
                "predictedE2eLatencyMs": decision["predicted_e2e_latency_ms"],
                "slaBreachProbability": decision["sla_breach_probability"],
                "affectedDomain": decision["slice_affected_domain"],
                "recommendedAction": decision["recommended_slice_action"],
                "whatIfRiskReduction": decision["slice_what_if_risk_reduction"],
                "reasons": decision["slice_impact_reasons"],
            },
            "policy": {
                "state": decision["policy_state"],
                "action": decision["policy_action"],
                "domain": decision["policy_orchestration_domain"],
                "requiresAudit": decision["policy_requires_audit"],
                "operatorId": decision["policy_operator_id"],
                "tenantId": decision["policy_tenant_id"],
                "trustZone": decision["policy_trust_zone"],
                "federationPolicy": decision["policy_federation_policy"],
                "zsmWorkflowStage": decision["policy_zsm_workflow_stage"],
                "auditEventId": decision["policy_audit_event_id"],
                "confidence": decision["policy_confidence"],
                "targetMttdSeconds": decision["policy_target_mttd_seconds"],
                "targetMttmSeconds": decision["policy_target_mttm_seconds"],
                "escalationLevel": decision["policy_escalation_level"],
                "reasons": decision["policy_reasons"],
            },
            "digitalTwinNetwork": {
                "readinessScore": decision["dtn_readiness_score"],
                "state": decision["dtn_state"],
                "twinSyncQuality": decision["dtn_twin_sync_quality"],
                "aiServiceChain": decision["dtn_ai_service_chain"],
                "orchestrationMode": decision["dtn_orchestration_mode"],
                "nextBestCapability": decision["dtn_next_best_capability"],
                "reasons": decision["dtn_reasons"],
            },
            "ricControl": decision["ric_control"],
            "prediction": self._predictive_status(risk, root, profile),
        }

    @staticmethod
    def _calculate_risk(k: dict[str, float], p: dict[str, Any]) -> float:
        def excess(actual: float, target: float) -> float:
            return max(0, min(1, (actual - target) / max(target, 0.0001)))

        def deficit(actual: float, target: float) -> float:
            return max(0, min(1, (target - actual) / max(target, 0.0001)))

        latency_risk = excess(k["latency"], p["latency"] * (1.12 if p["priority"] >= 5 else 1.35))
        jitter_risk = excess(k["jitter"], p["jitter"] * (1.15 if p["priority"] >= 5 else 1.45))
        loss_risk = excess(k["loss"], p["loss"] * 1.5)
        throughput_risk = deficit(k["throughput"], p["throughput"] * (0.76 if p["weight"] in {"Throughput", "Capacity"} else 0.45))
        handover_risk = excess(k["handover"], max(0.8, 4.5 / max(1, p["mobility"])))
        edge_risk = excess(k["edgeDelay"], max(2, p["edge"] * 1.9))
        continuity_weight = 0.08 if p["parameters"].get("service_continuity_requirement") == "very high" else 0.03
        sync_weight = 0.06 if p["parameters"].get("synchronization_requirement") == "high" else 0.02
        return min(
            1,
            latency_risk * (0.26 if p["priority"] >= 5 else 0.18)
            + jitter_risk * (0.20 if p["priority"] >= 5 else 0.12)
            + loss_risk * (0.20 if p["priority"] >= 5 else 0.14)
            + throughput_risk * (0.20 if p["weight"] in {"Throughput", "Capacity"} else 0.08)
            + handover_risk * (0.17 if p["mobility"] >= 5 else 0.08)
            + edge_risk * (0.17 if p["edge"] >= 5 else 0.08)
            + jitter_risk * sync_weight
            + latency_risk * continuity_weight,
        )

    @staticmethod
    def _infer_root_cause(k: dict[str, float], selected_fault: str, risk: float) -> str:
        if selected_fault != "normal" and risk > 0.25:
            return selected_fault
        if k["prb"] > 88:
            return "cell_congestion"
        if k["backhaul"] > 14:
            return "backhaul_degradation"
        if k["edgeDelay"] > 11:
            return "edge_overload"
        if k["handover"] > 5.5:
            return "handover_instability"
        if k["jitter"] > 9 and k["bler"] > 3.5:
            return "timing_drift"
        if k["loss"] > 1:
            return "packet_loss_burst"
        if risk > 0.62:
            return "unknown_anomaly"
        return "normal"

    @staticmethod
    def _recommend(root: str, profile: dict[str, Any], mode: str) -> tuple[str, str]:
        actions = {
            "normal": ("no_action", "No recovery action required."),
            "cell_congestion": (
                "prioritize_slice_and_traffic_steer" if profile["priority"] >= 5 else "load_balance_neighbor_cell",
                "Reduce congestion while protecting high-priority slices.",
            ),
            "backhaul_degradation": ("reroute_transport_path", "Move affected traffic to a healthier transport path."),
            "edge_overload": ("mec_failover_or_scale", "Shift workload to another MEC node or scale edge capacity."),
            "handover_instability": ("handover_parameter_tuning", "Tune handover thresholds and neighbor relations."),
            "timing_drift": ("switch_timing_source", "Switch timing source and isolate unstable clock domain."),
            "packet_loss_burst": ("prioritize_reliable_bearer", "Increase reliability treatment and deprioritize non-critical traffic."),
            "node_failure": ("failover_to_neighbor_cell", "Fail over users to neighboring cells and raise outage alarm."),
            "unknown_anomaly": ("human_review_guarded_mode", "Automation is blocked until RCA confidence improves."),
        }
        action, reason = actions.get(root, actions["unknown_anomaly"])
        if mode == "rule_based" and root != "normal":
            return "raise_alarm_static_rule", "Rule-based mode raises alarm without twin validation."
        return action, reason

    @staticmethod
    def _validate(risk: float, root: str, action: str, mode: str) -> dict[str, Any]:
        if action == "no_action":
            return {"approved": True, "postRisk": round(risk, 4), "note": "Healthy state."}
        if mode == "rule_based":
            return {"approved": False, "postRisk": round(risk * 0.92, 4), "note": "No twin validation in rule-based mode."}
        if action == "human_review_guarded_mode":
            return {"approved": False, "postRisk": round(risk, 4), "note": "Blocked for NOC review."}
        improvement = {
            "prioritize_slice_and_traffic_steer": 0.32,
            "load_balance_neighbor_cell": 0.24,
            "reroute_transport_path": 0.28,
            "mec_failover_or_scale": 0.30,
            "handover_parameter_tuning": 0.22,
            "switch_timing_source": 0.25,
            "prioritize_reliable_bearer": 0.20,
            "failover_to_neighbor_cell": 0.34,
        }.get(action, 0.12)
        return {
            "approved": True,
            "postRisk": round(max(0, risk - improvement), 4),
            "note": f"Twin predicts risk reduction for {root}.",
        }

    @staticmethod
    def _state_label(risk: float) -> str:
        if risk >= 0.68:
            return "fault"
        if risk >= 0.45:
            return "risk"
        return "healthy"

    @staticmethod
    def _predictive_status(risk: float, root: str, profile: dict[str, Any]) -> dict[str, Any]:
        rto = str(profile["parameters"].get("recovery_time_objective", "seconds")).lower()
        critical = profile["priority"] >= 5 or "millisecond" in rto
        if risk >= 0.6:
            horizon = "immediate"
        elif risk >= 0.42:
            horizon = "next 30-90 seconds" if critical else "next 2-5 minutes"
        else:
            horizon = "stable"
        return {
            "preFailureRisk": round(min(1, risk + (0.12 if critical else 0.05)), 4),
            "horizon": horizon,
            "watchItem": root if root != "normal" else "load, jitter, handover and PRB trend",
        }


ENGINE: LiveTwinEngine | None = None


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class LiveApiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            assert ENGINE is not None
            self._send_json(ENGINE.snapshot())
            return
        if parsed.path == "/api/health":
            assert ENGINE is not None
            self._send_json(ENGINE.health())
            return
        if parsed.path == "/api/history":
            assert ENGINE is not None
            limit = int(parse_qs(parsed.query).get("limit", ["100"])[0])
            with ENGINE.state.lock:
                self._send_json({"history": ENGINE.state.history[-limit:]})
            return
        if parsed.path == "/api/kpm-dataset":
            self._send_json(load_openran_kpm_dataset_summary())
            return
        if parsed.path == "/api/live-telemetry":
            self._send_json(load_live_telemetry_status())
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json()
        assert ENGINE is not None
        if parsed.path in {"/api/fault", "/api/scenario"}:
            self._send_json(ENGINE.set_scenario(payload))
            return
        if parsed.path == "/api/telemetry":
            self._send_json(ENGINE.set_telemetry(payload))
            return
        if parsed.path == "/api/reset":
            self._send_json(ENGINE.reset())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def find_available_port(start_port: int) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No available localhost port found")


def main() -> None:
    global ENGINE
    parser = argparse.ArgumentParser(description="Serve live BLR O-RAN Digital Twin backend and GUI.")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--self-learning-model",
        default="",
        help="Optional saved OnlineSelfLearningModel JSON artifact to preload, e.g. outputs/models/open_ran_kpm_self_learning_model.json.",
    )
    args = parser.parse_args()
    ENGINE = LiveTwinEngine(self_learning_model_path=args.self_learning_model or None)
    port = find_available_port(args.port)
    if port != args.port:
        print(f"Port {args.port} is busy. Using http://127.0.0.1:{port} instead.")
    thread = threading.Thread(target=ENGINE.loop, daemon=True)
    thread.start()
    with ReusableThreadingHTTPServer(("127.0.0.1", port), LiveApiHandler) as server:
        print(f"Live backend + GUI at http://127.0.0.1:{port}")
        if args.self_learning_model:
            print(f"Preloaded self-learning model: {args.self_learning_model}")
        print("API: /api/state /api/fault /api/reset /api/history /api/kpm-dataset")
        server.serve_forever()


if __name__ == "__main__":
    main()
