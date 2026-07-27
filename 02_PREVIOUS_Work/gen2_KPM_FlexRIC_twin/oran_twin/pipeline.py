from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .config import Paths
from .device_population import DevicePopulationModel
from .engine import OranDecisionEngine
from .evaluation import evaluate, write_evaluation_report
from .model_registry import ModelRegistry
from .persistence import DecisionStore
from .profiles import load_profiles
from .simulator import OranKpiSimulator, SimulationConfig


def run_pipeline(run_name: str = "demo", duration: int = 240, seed: int = 42) -> Path:
    out_dir = Paths.runs / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    profiles = load_profiles()
    simulator = OranKpiSimulator(profiles=profiles, config=SimulationConfig(duration=duration, seed=seed))
    raw_rows = simulator.run()
    simulator.write_csv(raw_rows, out_dir / "simulated_kpis.csv")

    engine = OranDecisionEngine(profiles)
    store = DecisionStore()
    enriched: list[dict[str, object]] = []

    for row in raw_rows:
        result = engine.assess(row)
        store.record_decision(run_name=run_name, mode="batch", decision=result)
        enriched.append(
            {
                **result,
                "twin_reasons": ";".join(result["twin_reasons"]),
                "anomaly_reasons": ";".join(result["anomaly_reasons"]),
                "self_learning_reasons": ";".join(result["self_learning_reasons"]),
                "drift_reasons": ";".join(result["drift_reasons"]),
                "security_guard_reasons": ";".join(result["security_guard_reasons"]),
                "xapp_proposals": json.dumps(result["xapp_proposals"], separators=(",", ":")),
                "xapp_replay_record": json.dumps(result["xapp_replay_record"], separators=(",", ":")),
                "xapp_conflict_reasons": ";".join(result["xapp_conflict_reasons"]),
                "timing_stride_threats": ";".join(result["timing_stride_threats"]),
                "timing_reasons": ";".join(result["timing_reasons"]),
                "spectrum_reasons": ";".join(result["spectrum_reasons"]),
                "slice_impact_reasons": ";".join(result["slice_impact_reasons"]),
                "policy_reasons": ";".join(result["policy_reasons"]),
                "dtn_ai_service_chain": ";".join(result["dtn_ai_service_chain"]),
                "dtn_reasons": ";".join(result["dtn_reasons"]),
                "automation_safety_evidence": ";".join(result["automation_safety_evidence"]),
                "ric_control": json.dumps(result["ric_control"], separators=(",", ":")),
            }
        )

    write_csv(enriched, out_dir / "twin_assessments.csv")
    engine.self_learning.save(out_dir / "self_learning_model.json")
    summary = summarize(enriched)
    evaluation = evaluate(enriched)
    summary["evaluation"] = evaluation
    summary["model_registry"] = ModelRegistry().snapshot()
    summary["device_population"] = summarize_device_population(enriched)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    store.record_summary(run_name=run_name, records=len(enriched), summary=summary)
    write_evaluation_report(evaluation, out_dir / "evaluation_report.md")
    write_incident_report(enriched, summary, out_dir / "incident_report.md")
    build_html_dashboard(enriched, summary, out_dir / "dashboard.html")
    return out_dir


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    anomalies = [r for r in rows if r["anomaly_detected"]]
    true_faults = [r for r in rows if r["fault_active"]]
    aml_attacks = [r for r in rows if r.get("aml_attack_active")]
    approved = [r for r in rows if r["action_approved_by_twin"] and r["healing_action"] != "no_action"]
    detected_true = [r for r in true_faults if r["anomaly_detected"]]
    false_positive = [r for r in rows if r["anomaly_detected"] and not r["fault_active"] and not r.get("aml_attack_active")]
    guarded_attacks = [r for r in aml_attacks if r["aml_threat_level"] in {"medium", "high", "critical"}]
    blocked_by_security = [
        r
        for r in rows
        if r["security_guard_action"] in {"require_human_approval", "block_and_quarantine"}
        and r["healing_action"] != "no_action"
    ]
    drifted = [r for r in rows if r["drift_status"] == "drifted"]
    xapp_conflicts = [r for r in rows if r["xapp_conflict_detected"]]
    timing_incidents = [r for r in rows if r["timing_state"] == "timing_security_incident"]
    spectrum_anomalies = [r for r in rows if r["spectrum_state"] == "spectrum_anomaly"]
    severe_sla = [r for r in rows if r["sla_impact_level"] == "severe"]
    likely_breaches = [r for r in rows if float(r["sla_breach_probability"]) >= 0.65]
    unsafe_prevented = [r for r in rows if r["unsafe_action_prevented"]]
    safety_scores = [float(r["automation_safety_score"]) for r in rows if r["healing_action"] != "no_action"]
    baseline_execute = [r for r in rows if r["automation_baseline_would_execute"] and r["healing_action"] != "no_action"]
    guarded_execute = [r for r in rows if r["automation_guarded_would_execute"] and r["healing_action"] != "no_action"]
    self_learning_anomalies = [r for r in rows if r["self_learning_anomaly_detected"]]
    self_learning_scores = [float(r["self_learning_anomaly_score"]) for r in rows]

    by_service = defaultdict(lambda: {"records": 0, "sla_violations": 0, "anomalies": 0})
    for row in rows:
        item = by_service[str(row["service_class"])]
        item["records"] += 1
        item["sla_violations"] += int(bool(row["sla_violation"]))
        item["anomalies"] += int(bool(row["anomaly_detected"]))

    return {
        "records": total,
        "true_fault_records": len(true_faults),
        "anomaly_records": len(anomalies),
        "detection_recall_on_fault_records": round(len(detected_true) / max(1, len(true_faults)), 4),
        "false_positive_rate_on_normal_records": round(len(false_positive) / max(1, total - len(true_faults)), 4),
        "approved_healing_actions": len(approved),
        "baseline_executable_actions": len(baseline_execute),
        "guarded_executable_actions": len(guarded_execute),
        "unsafe_actions_prevented": len(unsafe_prevented),
        "mean_automation_safety_score": round(sum(safety_scores) / max(1, len(safety_scores)), 4),
        "automation_safety_decisions": dict(Counter(str(r["automation_safety_decision"]) for r in rows)),
        "self_learning_anomaly_records": len(self_learning_anomalies),
        "mean_self_learning_anomaly_score": round(sum(self_learning_scores) / max(1, len(self_learning_scores)), 4),
        "self_learning_modes": dict(Counter(str(r["self_learning_mode"]) for r in rows)),
        "self_learning_rca_predictions": dict(
            Counter(str(r["self_learning_rca_prediction"]) for r in rows if r["self_learning_rca_prediction"] != "unknown")
        ),
        "security_blocked_actions": len(blocked_by_security),
        "aml_attack_records": len(aml_attacks),
        "aml_attacks_guarded": len(guarded_attacks),
        "aml_attack_types_injected": dict(Counter(str(r["aml_attack_type"]) for r in aml_attacks)),
        "drifted_records": len(drifted),
        "drift_statuses": dict(Counter(str(r["drift_status"]) for r in rows)),
        "drift_types": dict(Counter(str(r["drift_type"]) for r in rows if r["drift_type"] != "none")),
        "drift_adaptation_actions": dict(Counter(str(r["drift_adaptation_action"]) for r in rows)),
        "drift_lifecycle_stages": dict(Counter(str(r["drift_lifecycle_stage"]) for r in rows)),
        "drift_retraining_priorities": dict(Counter(str(r["drift_retraining_priority"]) for r in rows)),
        "drift_automation_modes": dict(Counter(str(r["drift_automation_mode"]) for r in rows)),
        "xapp_conflict_records": len(xapp_conflicts),
        "xapp_conflict_types": dict(Counter(str(r["xapp_conflict_type"]) for r in xapp_conflicts)),
        "xapp_mitigation_strategies": dict(Counter(str(r["xapp_mitigation_strategy"]) for r in rows)),
        "xapp_distillation_states": dict(Counter(str(r["xapp_distillation_state"]) for r in rows)),
        "xapp_selected": dict(Counter(str(r["xapp_selected"]) for r in rows)),
        "timing_security_incidents": len(timing_incidents),
        "timing_states": dict(Counter(str(r["timing_state"]) for r in rows)),
        "timing_sync_states": dict(Counter(str(r["timing_sync_state"]) for r in rows)),
        "timing_stride_test_cases": dict(Counter(str(r["timing_stride_test_case"]) for r in rows)),
        "spectrum_anomaly_records": len(spectrum_anomalies),
        "spectrum_states": dict(Counter(str(r["spectrum_state"]) for r in rows)),
        "spectrum_actions": dict(Counter(str(r["spectrum_action"]) for r in rows)),
        "spectrum_dsa_policies": dict(Counter(str(r["spectrum_dsa_policy"]) for r in rows)),
        "spectrum_interference_sources": dict(Counter(str(r["spectrum_interference_source"]) for r in rows)),
        "severe_sla_impact_records": len(severe_sla),
        "predicted_sla_breach_records": len(likely_breaches),
        "sla_impact_levels": dict(Counter(str(r["sla_impact_level"]) for r in rows)),
        "slice_affected_domains": dict(Counter(str(r["slice_affected_domain"]) for r in rows)),
        "recommended_slice_actions": dict(Counter(str(r["recommended_slice_action"]) for r in rows)),
        "policy_states": dict(Counter(str(r["policy_state"]) for r in rows)),
        "policy_workflow_stages": dict(Counter(str(r["policy_zsm_workflow_stage"]) for r in rows)),
        "policy_escalation_levels": dict(Counter(str(r["policy_escalation_level"]) for r in rows)),
        "policy_trust_zones": dict(Counter(str(r["policy_trust_zone"]) for r in rows)),
        "dtn_states": dict(Counter(str(r["dtn_state"]) for r in rows)),
        "dtn_orchestration_modes": dict(Counter(str(r["dtn_orchestration_mode"]) for r in rows)),
        "dtn_twin_sync_quality": dict(Counter(str(r["dtn_twin_sync_quality"]) for r in rows)),
        "dtn_next_best_capabilities": dict(Counter(str(r["dtn_next_best_capability"]) for r in rows)),
        "aml_threat_levels": dict(Counter(str(r["aml_threat_level"]) for r in rows)),
        "aml_threat_types": dict(Counter(str(r["aml_threat_type"]) for r in rows if r["aml_threat_type"] != "none")),
        "root_causes": dict(Counter(str(r["root_cause"]) for r in anomalies)),
        "healing_actions": dict(Counter(str(r["healing_action"]) for r in anomalies)),
        "by_service": dict(by_service),
    }


def summarize_device_population(rows: list[dict[str, object]]) -> dict[str, object]:
    latest_by_cell: dict[str, dict[str, object]] = {}
    for row in rows:
        latest_by_cell[str(row["cell_id"])] = row
    cells = [
        {
            "id": cell_id,
            "baseLoad": min(1.0, max(0.0, float(row["prb_util_pct"]) / 100)),
        }
        for cell_id, row in sorted(latest_by_cell.items())
    ]
    risk_by_cell = {cell_id: float(row["twin_risk_score"]) for cell_id, row in latest_by_cell.items()}
    selected = rows[-1] if rows else {}
    population = DevicePopulationModel().assess(
        cells=cells,
        selected_cell_id=str(selected.get("cell_id", "CELL_A")),
        active_service=str(selected.get("service_class", "eMBB")),
        risk_by_cell=risk_by_cell,
        fault_type=str(selected.get("fault_type", "normal")),
        severity=0.65,
        network_load=sum(float(row["prb_util_pct"]) for row in latest_by_cell.values()) / max(1, len(latest_by_cell) * 100),
        mobility=0.5,
    )
    return {
        "total_devices": population.total_devices,
        "active_devices": population.active_devices,
        "affected_devices": population.affected_devices,
        "by_service": population.by_service,
        "representative_ues": population.representative_ues,
    }


def write_incident_report(rows: list[dict[str, object]], summary: dict[str, object], path: Path) -> None:
    incidents = [
        row
        for row in rows
        if row["healing_action"] != "no_action"
        or row["automation_safety_decision"] in {"block_automation", "require_human_approval"}
    ]
    prevented = [row for row in incidents if row["unsafe_action_prevented"]]
    top = sorted(incidents, key=lambda row: float(row["twin_risk_score"]), reverse=True)[:12]
    incident_rows = "\n".join(
        "| {t} | {cell} | {service} | {fault} | {root} | {action} | {risk} | {safety} | {decision} | {prevented} |".format(
            t=row["t"],
            cell=row["cell_id"],
            service=row["service_class"],
            fault=row["fault_type"],
            root=row["root_cause"],
            action=row["healing_action"],
            risk=row["twin_risk_score"],
            safety=row["automation_safety_score"],
            decision=row["automation_safety_decision"],
            prevented=row["unsafe_action_prevented"],
        )
        for row in top
    )
    population = summary.get("device_population", {})
    report = f"""# Incident And Automation Safety Report

## Executive Summary

- Total KPI records: `{summary['records']}`
- Total virtual devices represented: `{population.get('total_devices', 0)}`
- Active virtual devices represented: `{population.get('active_devices', 0)}`
- Affected virtual devices estimated: `{population.get('affected_devices', 0)}`
- Baseline executable actions: `{summary['baseline_executable_actions']}`
- Guarded executable actions: `{summary['guarded_executable_actions']}`
- Unsafe baseline actions prevented: `{summary['unsafe_actions_prevented']}`
- Mean automation safety score: `{summary['mean_automation_safety_score']}`
- Self-learning anomaly records: `{summary['self_learning_anomaly_records']}`
- Incidents/control records reviewed: `{len(incidents)}`
- Prevented unsafe automation incidents: `{len(prevented)}`

## Highest-Risk Incidents

| t | Cell | Service | Fault | RCA | Healing | Risk | Safety | Decision | Prevented |
|---:|---|---|---|---|---|---:|---:|---|---|
{incident_rows}

## Presentation Line

The baseline loop would execute recovery actions immediately after RCA. The guarded loop uses AML, drift, xApp conflict, SLA, timing, spectrum, ZSM policy, and DTN readiness checks before allowing automation.
"""
    path.write_text(report, encoding="utf-8")


def build_html_dashboard(rows: list[dict[str, object]], summary: dict[str, object], path: Path) -> None:
    latest = rows[-20:]
    evaluation = summary["evaluation"]
    fault_eval = evaluation["fault_detection"]
    service_rows = "".join(
        f"<tr><td>{service}</td><td>{item['records']}</td><td>{item['sla_violations']}</td><td>{item['anomalies']}</td></tr>"
        for service, item in sorted(summary["by_service"].items())
    )
    recent_rows = "".join(
        "<tr>"
        f"<td>{r['t']}</td><td>{r['cell_id']}</td><td>{r['service_class']}</td><td>{r['fault_type']}</td>"
        f"<td>{r['twin_risk_score']}</td><td>{r['ai_trust_score']}</td><td>{r['aml_threat_level']}</td>"
        f"<td>{r['self_learning_anomaly_score']}</td><td>{r['self_learning_rca_prediction']}</td>"
        f"<td>{r['drift_status']}</td><td>{r['sla_impact_level']}</td><td>{r['timing_state']}</td><td>{r['root_cause']}</td>"
        f"<td>{r['healing_action']}</td><td>{r['automation_safety_score']}</td><td>{r['automation_safety_decision']}</td>"
        f"<td>{r['xapp_conflict_type']}</td><td>{r['security_guard_action']}</td>"
        "</tr>"
        for r in latest
    )
    cells = {
        str(row["cell_id"]): {
            "lat": row["lat"],
            "lon": row["lon"],
            "risk": row["twin_risk_score"],
            "fault": row["fault_type"],
        }
        for row in rows[-100:]
    }
    markers = json.dumps(list(cells.values()))
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>O-RAN Digital Twin MVP Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #17202A; background: #F5F8FB; }}
    header {{ background: #102033; color: white; padding: 22px 32px; }}
    h1 {{ margin: 0; font-size: 26px; }}
    main {{ padding: 24px 32px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
    .card {{ background: white; border: 1px solid #D8E2EA; border-radius: 8px; padding: 16px; }}
    .metric {{ font-size: 28px; font-weight: 700; color: #2F80ED; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #D8E2EA; padding: 8px; font-size: 13px; text-align: left; }}
    th {{ background: #EAF2FB; }}
    .map {{ position: relative; height: 360px; background: linear-gradient(135deg,#EAF2FB,#DDEEEB); border: 1px solid #D8E2EA; border-radius: 8px; overflow: hidden; }}
    .marker {{ position: absolute; width: 18px; height: 18px; border-radius: 50%; background: #43A047; border: 2px solid white; box-shadow: 0 1px 8px #555; }}
    .marker.risk {{ background: #E05252; }}
    .label {{ position: absolute; transform: translate(12px,-22px); font-size: 12px; font-weight: 700; }}
  </style>
</head>
<body>
<header>
  <h1>AI-Native O-RAN Digital Twin MVP Dashboard</h1>
  <p>Service-class-aware synthetic KPI simulation, anomaly detection, RCA and twin-validated healing.</p>
</header>
<main>
  <section class="grid">
    <div class="card"><div class="metric">{summary['records']}</div><div>Total KPI records</div></div>
    <div class="card"><div class="metric">{summary['device_population']['total_devices']}</div><div>Virtual devices represented</div></div>
    <div class="card"><div class="metric">{summary['device_population']['affected_devices']}</div><div>Estimated affected devices</div></div>
    <div class="card"><div class="metric">{summary['anomaly_records']}</div><div>Anomaly records</div></div>
    <div class="card"><div class="metric">{summary['detection_recall_on_fault_records']}</div><div>Fault detection recall</div></div>
    <div class="card"><div class="metric">{fault_eval['precision']}</div><div>Fault detection precision</div></div>
    <div class="card"><div class="metric">{fault_eval['f1_score']}</div><div>Fault detection F1</div></div>
    <div class="card"><div class="metric">{summary['approved_healing_actions']}</div><div>Twin-approved actions</div></div>
    <div class="card"><div class="metric">{summary['unsafe_actions_prevented']}</div><div>Unsafe baseline actions prevented</div></div>
    <div class="card"><div class="metric">{summary['mean_automation_safety_score']}</div><div>Mean automation safety score</div></div>
    <div class="card"><div class="metric">{summary['security_blocked_actions']}</div><div>AML-guarded actions</div></div>
    <div class="card"><div class="metric">{summary['self_learning_anomaly_records']}</div><div>Self-learning anomalies</div></div>
    <div class="card"><div class="metric">{summary['mean_self_learning_anomaly_score']}</div><div>Mean learned anomaly score</div></div>
    <div class="card"><div class="metric">{summary['drifted_records']}</div><div>Drifted records</div></div>
    <div class="card"><div class="metric">{summary['xapp_conflict_records']}</div><div>xApp conflict records</div></div>
    <div class="card"><div class="metric">{summary['severe_sla_impact_records']}</div><div>Severe SLA impact records</div></div>
    <div class="card"><div class="metric">{summary['timing_security_incidents']}</div><div>Timing security incidents</div></div>
    <div class="card"><div class="metric">{summary['spectrum_anomaly_records']}</div><div>Spectrum anomaly records</div></div>
  </section>
  <h2>Cell Risk Map</h2>
  <div class="map" id="map"></div>
  <h2>Service Class Summary</h2>
  <table><thead><tr><th>Service</th><th>Records</th><th>SLA Violations</th><th>Anomalies</th></tr></thead><tbody>{service_rows}</tbody></table>
  <h2>Recent Twin Decisions</h2>
  <table><thead><tr><th>t</th><th>Cell</th><th>Service</th><th>Fault</th><th>Risk</th><th>AI Trust</th><th>AML Level</th><th>Learned Score</th><th>Learned RCA</th><th>Drift</th><th>SLA Impact</th><th>Timing</th><th>RCA</th><th>Healing</th><th>Safety Score</th><th>Safety Decision</th><th>xApp Conflict</th><th>Security Guard</th></tr></thead><tbody>{recent_rows}</tbody></table>
</main>
<script>
const markers = {markers};
const map = document.getElementById('map');
const minLat = Math.min(...markers.map(m => m.lat));
const maxLat = Math.max(...markers.map(m => m.lat));
const minLon = Math.min(...markers.map(m => m.lon));
const maxLon = Math.max(...markers.map(m => m.lon));
markers.forEach((m, i) => {{
  const x = 40 + ((m.lon - minLon) / Math.max(0.0001, maxLon - minLon)) * (map.clientWidth - 90);
  const y = 40 + (1 - ((m.lat - minLat) / Math.max(0.0001, maxLat - minLat))) * (map.clientHeight - 90);
  const dot = document.createElement('div');
  dot.className = 'marker' + (m.risk > 0.6 ? ' risk' : '');
  dot.style.left = x + 'px';
  dot.style.top = y + 'px';
  dot.title = `risk=${{m.risk}} fault=${{m.fault}}`;
  const label = document.createElement('div');
  label.className = 'label';
  label.style.left = x + 'px';
  label.style.top = y + 'px';
  label.textContent = `Cell ${{i+1}}`;
  map.appendChild(dot);
  map.appendChild(label);
}});
</script>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
