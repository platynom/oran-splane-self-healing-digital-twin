"""Executable mechanical regression checks for real-session evidence gates.

Fixtures prove input-validation mechanics only. They are not scientific evidence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(APP))
from stats import openset_eval  # noqa: E402


def load(folder: Path) -> object:
    return openset_eval._load_real_sessions(folder, {"dataset": {"window_s": 0.4, "step_s": 0.2}})


def metadata(folder: Path) -> dict:
    return json.loads((folder / "TIMESAFE_SESSION_METADATA.json").read_text())


def main() -> None:
    fixtures = Path(__file__).with_name("evidence_gate_fixtures")
    results: dict[str, bool] = {"fixtures_are_mechanical_only": True}
    accepted = load(fixtures / "valid")
    results["valid_fixture_loads"] = not accepted.empty
    results["recorded_h0_label_is_preserved"] = set(accepted.get("label", [])) == {"H0"}
    results["undeclared_file_rejected"] = load(fixtures / "undeclared").empty
    results["altered_declared_file_rejected"] = load(fixtures / "changed").empty
    results["missing_label_column_rejected"] = load(fixtures / "missing_labels").empty
    results["partial_missing_labels_rejected_after_hash_binding"] = load(fixtures / "partial_missing_labels").empty
    results["malformed_run_id_rejected_after_hash_binding"] = load(fixtures / "malformed_run_id").empty
    results["unrelated_source_map_rejected"] = load(fixtures / "unrelated_source_map").empty
    results["quarantined_capture_id_rejected"] = load(fixtures / "quarantined").empty
    results["list_evidence_artifact_rejected_without_exception"] = load(fixtures / "malformed").empty

    # A reviewed document must not be the CSV currently being evaluated.  Use
    # the actual loader, a workspace-relative PCAP source map, and the valid
    # fixture's correctly bound input hash so this reaches the circularity guard.
    circular = metadata(fixtures / "valid")
    pcap_rel = "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_prod_successful_announce_attack_ptp.pcap"
    csv_rel = "outputs/manual_dataset_combined/evidence_gate_fixtures/valid/renamed_announce_but_h0.csv"
    circular["source_sha256"] = {pcap_rel: circular["source_sha256"][next(iter(circular["source_sha256"]))]}
    circular["inputs"][0]["source_paths"] = [pcap_rel]
    circular["evidence_artifact"] = csv_rel
    circular["evidence_sha256"] = circular["inputs"][0]["sha256"]
    with patch.object(openset_eval, "ROOT", ROOT), \
         patch.object(Path, "read_text", return_value=json.dumps(circular)):
        results["evaluated_csv_cannot_validate_itself"] = load(fixtures / "valid").empty

    original_hashes = set(openset_eval.QUARANTINED_INPUT_HASHES)
    try:
        openset_eval.QUARANTINED_INPUT_HASHES.add(metadata(fixtures / "valid")["inputs"][0]["sha256"])
        results["renamed_quarantined_content_rejected"] = load(fixtures / "valid").empty
    finally:
        openset_eval.QUARANTINED_INPUT_HASHES.clear()
        openset_eval.QUARANTINED_INPUT_HASHES.update(original_hashes)

    malformed = metadata(fixtures / "valid")
    for field, value in {"validation_method": [], "reviewer": {}, "review_date": 7,
                         "evidence_sha256": ["x"], "source_sha256": [], "inputs": {},
                         "evidence_type": []}.items():
        candidate = dict(malformed)
        candidate[field] = value
        results[f"malformed_{field}_rejected"] = not openset_eval._has_independent_clock_health_evidence(candidate)
    missing_source = dict(malformed)
    del missing_source['source_sha256']
    results['missing_source_map_rejected_without_exception'] = not openset_eval._has_independent_clock_health_evidence(missing_source)

    # Exercise the real evaluator orchestration, with mechanical stand-ins for
    # fitting/scoring. This checks control flow, not ML quality or data science.
    windows = pd.DataFrame([
        {'capture_id':capture,'attack_family':family,'label':label,'x':value}
        for capture,family in [('fixture_a','a'),('fixture_b','b')]
        for label,value in [('H0',0.),('H1',1.)]
    ])
    with patch.object(openset_eval, '_load_real_sessions', return_value=windows), \
         patch.object(openset_eval, '_fit_rf', return_value=object()), \
         patch.object(openset_eval, '_detector', return_value=object()), \
         patch.object(openset_eval, '_threshold_rows', return_value=[]), \
         patch.object(openset_eval, '_metric_row', side_effect=lambda *args: {'mode':args[1]}), \
         patch.object(openset_eval, '_prediction_trace', return_value=pd.DataFrame([{'fixture':True}])):
        evaluated = openset_eval.evaluate_real({'seed':1}, fixtures, features=['x'])
        results['eligible_control_flow_has_no_removed_helper_call'] = len(evaluated)==4
    with patch.object(openset_eval, '_load_real_sessions', return_value=windows[windows.label=='H0']):
        evaluated=openset_eval.evaluate_real({'seed':1}, fixtures, features=['x'])
        results['no_eligible_family_returns_empty_without_crash']=evaluated.empty and evaluated.attrs['persistence_traces'].empty

    from evasion import victim_transformer
    packet_inputs = victim_transformer._packet_input_hashes(APP)
    packet_control = dict(malformed, label_semantics='packet_maliciousness',
                          evidence_type='controlled_experiment_log', source_sha256=packet_inputs,
                          evidence_artifact='docs/EVASION_PHASE0_NOTES.md',
                          evidence_sha256=victim_transformer._sha256(APP/'docs/EVASION_PHASE0_NOTES.md'))
    with patch.object(Path,'is_file',return_value=True), patch.object(Path,'read_text',return_value=json.dumps(packet_control)):
        try:
            victim_transformer._require_traceable_validation(APP,'mechanical_fixture.json','packet_maliciousness')
        except ValueError:
            results['packet_consumer_full_input_binding_control']=False
        else:
            results['packet_consumer_full_input_binding_control']=True
    packet_circular = dict(packet_control)
    packet_circular['evidence_artifact']='data/external/timesafe_multi_raw/sync_followup_session_labels.csv'
    packet_circular['evidence_sha256']=packet_inputs[packet_circular['evidence_artifact']]
    with patch.object(Path,'is_file',return_value=True), patch.object(Path,'read_text',return_value=json.dumps(packet_circular)):
        try:
            victim_transformer._require_traceable_validation(APP,'mechanical_fixture.json','packet_maliciousness')
        except ValueError:
            results['packet_consumer_rejects_evaluated_input_as_evidence']=True
        else:
            results['packet_consumer_rejects_evaluated_input_as_evidence']=False
    packet_base=dict(malformed, label_semantics='packet_maliciousness', evidence_type='controlled_experiment_log')
    for name,value in [('evidence_type',[]),('evidence_artifact',[]),('source_sha256',None)]:
        candidate=dict(packet_base)
        if value is None:candidate.pop(name)
        else:candidate[name]=value
        # Patch only manifest I/O to reach the actual packet metadata consumer.
        with patch.object(Path,'is_file',return_value=True), patch.object(Path,'read_text',return_value=json.dumps(candidate)):
            try:
                victim_transformer._require_traceable_validation(APP,'mechanical_fixture.json','packet_maliciousness')
            except ValueError:
                results['packet_consumer_rejects_'+name]=True
            else:results['packet_consumer_rejects_'+name]=False
    if not all(results.values()):
        raise SystemExit(json.dumps(results, indent=2))
    Path(__file__).with_name('evidence_gate_regression_results.json').write_text(
        json.dumps({'interpreter':sys.executable,'results':results},indent=2), encoding='utf-8'
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
