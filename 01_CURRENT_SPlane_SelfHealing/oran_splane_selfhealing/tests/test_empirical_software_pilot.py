from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
SPEC = importlib.util.spec_from_file_location("pilot_validator", ROOT / "outputs" / "empirical_software_network_pilot_v1" / "validate_pilot.py")
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def _event(phase: str, event: str, status: str = "PASS") -> dict[str, str]:
    return {"run_id": "a1", "phase": phase, "event": event, "utc": "2026-09-10T00:00:00Z", "monotonic_s": "1.0", "status": status}


def test_manifest_parser_uses_path_string_not_path_object_strip() -> None:
    digest = "a" * 64
    assert validator.parse_manifest_text(f"{digest}  /tmp/run/capture.pcap\n") == {"capture.pcap": digest}
    assert validator.parse_manifest_text("not-a-manifest-row\n") == {}


def test_structural_status_rejects_empty_packets_logs_and_readiness_failures() -> None:
    good = [_event("setup", f"{name}_ready") for name in ("tcpdump", "master_a", "master_b", "slave")]
    good += [_event("baseline_control", "phase_started"), _event("baseline_control", "phase_finished")]
    logs = {"master_a.log": 1, "master_b.log": 1, "slave.log": 1, "tcpdump.log": 1}
    assert validator.status_from_evidence(good, logs, 1, []) == "STRUCTURALLY_COMPLETE"
    assert validator.status_from_evidence(good, logs, 0, []) == "INCOMPLETE"
    assert validator.status_from_evidence(good, {**logs, "slave.log": 0}, 1, []) == "INCOMPLETE"
    assert validator.status_from_evidence(good, logs, 1, ["recorded_command_or_readiness_failure"]) == "INCOMPLETE"


def test_runner_uses_distinct_resource_names_free_running_and_version_correct_options() -> None:
    runner = (PROJECT / "harness" / "run_empirical_software_pilot.sh").read_text(encoding="utf-8")
    assert 'BR="${P}br"' in runner and 'BROOT="${P}cr"' in runner
    assert "free_running 1" in runner
    assert "slaveOnly 1" in runner and "clientOnly 1" not in runner
    assert "slaveOnly 1\npriority1 255" in runner
    assert '[ "$VERSION" = "3.1.1" ]' in runner
    assert 'kill -TERM "$A_PID"\n    event "$SCENARIO" preferred_master_stop_confirmed PASS' in runner
    assert runner.index("stop_owned; trap - EXIT") < runner.index('sha256sum "$OUT"/*')
    assert "authorized_source_change_no_action_control" in runner
    assert "benign_delay_jitter_no_loss" in runner
    assert "delay 100us 20us distribution normal" in runner
