from __future__ import annotations

import subprocess

from scripts.live_collect import LiveCollector, parse_live_pmc
from scripts.live_loop import _extract_fixed_window


PMC_FIXTURES = {
    "CURRENT_DATA_SET": "stepsRemoved 1\noffsetFromMaster -42.5\nmeanPathDelay 51000.0\n",
    "TIME_STATUS_NP": "master_offset -43\ncumulativeScaledRateOffset +0.000000006\ngmPresent true\n",
    "PARENT_DATA_SET": (
        "grandmasterPriority1 100\ngm.ClockClass 6\ngm.ClockAccuracy 0x20\n"
        "gm.OffsetScaledLogVariance 0x1234\ngrandmasterPriority2 110\n"
        "grandmasterIdentity 001122.fffe.334455\n"
    ),
    "PORT_DATA_SET": "portState SLAVE\npeerMeanPathDelay 50000\n",
    "PORT_SERVICE_STATS_NP": "",
    "PORT_STATS_NP": "rx_Sync 20\nrx_Follow_Up 20\nrx_Announce 2\ntx_Delay_Req 10\nrx_Delay_Resp 10\n",
}


def test_live_pmc_parser_recovers_measured_fields_and_rate() -> None:
    previous = {"Sync": 10, "Follow_Up": 10, "Announce": 1, "Delay_Req": 5, "Delay_Resp": 5}
    row, counts = parse_live_pmc(PMC_FIXTURES, previous, 1.0)
    assert row["offset_ns"] == -42.5
    assert row["path_delay_ns"] == 51000.0
    assert row["grandmaster_identity"] == "001122.fffe.334455"
    assert row["grandmaster_clock_class"] == 6
    assert row["steps_removed"] == 1
    assert row["msg_rate_hz"] == 31.0
    assert counts["Sync"] == 20


def test_live_local_holdover_zero_fields_are_invalid_not_healthy() -> None:
    outputs = dict(PMC_FIXTURES)
    outputs["CURRENT_DATA_SET"] = "stepsRemoved 0\noffsetFromMaster 0\nmeanPathDelay 0\n"
    outputs["TIME_STATUS_NP"] = "master_offset 0\ngmPresent true\n"
    outputs["PARENT_DATA_SET"] = "gm.ClockClass 255\n"
    outputs["PORT_DATA_SET"] = "portState MASTER\n"
    row, _ = parse_live_pmc(outputs, None, 0.1)
    assert row["offset_ns"] != row["offset_ns"]  # NaN, not a fabricated zero
    assert row["path_delay_ns"] != row["path_delay_ns"]
    assert row["telemetry_valid"] is False


def test_live_collector_degrades_without_synce_and_unsupported_dataset() -> None:
    calls = 0

    def runner(command, timeout):
        nonlocal calls
        calls += 1
        requested = [part.replace("GET ", "") for part in command if part.startswith("GET ")]
        output = "\n".join(
            f"fixture-0 RESPONSE MANAGEMENT {dataset}\n"
            f"{PMC_FIXTURES[dataset].replace('offsetFromMaster -42.5', 'offsetFromMaster -40.0').replace('meanPathDelay 51000.0', 'meanPathDelay 51010.0') if calls > 1 else PMC_FIXTURES[dataset]}"
            for dataset in requested
            if dataset != "PORT_SERVICE_STATS_NP"
        )
        error = "bad command: GET PORT_SERVICE_STATS_NP" if "PORT_SERVICE_STATS_NP" in requested else ""
        return subprocess.CompletedProcess(command, 0, output, error)

    collector = LiveCollector(namespace="fixture", poll_interval_s=0.1, runner=runner)
    first = collector.sample()
    second = collector.sample()
    assert first is not None and second is not None
    assert second["synce_ql"] == 4
    assert second["scenario"] == "live"
    assert second["grandmaster_identity"] == "001122.fffe.334455"
    assert second["path_delay_ns"] == 51010.0
    assert second["pdv_ns"] == 5.0
    assert second["freq_error_ppb"] != 0.0
    assert "PORT_SERVICE_STATS_NP" in collector.unsupported


def test_fixed_live_windows_do_not_depend_on_scheduler_alignment() -> None:
    collector_rows = []
    for index, timestamp in enumerate([0.01, 0.115, 0.221, 0.329, 0.431]):
        row = {
            "t_s": timestamp,
            "scenario": "live",
            "offset_ns": float(index),
            "measured_offset_ns": float(index),
            "path_delay_ns": 1000.0,
            "pdv_ns": 0.0,
            "freq_error_ppb": 0.0,
            "oscillator_holdover_nominal_ppb": 6.0,
            "oscillator_holdover_tolerance_ppb": 2.0,
            "oscillator_disciplined_tolerance_ppb": 1.5,
            "gnss_reference_ns": 0.0,
            "ptp_reference_ns": 0.0,
            "peer_reference_ns": 0.0,
            "source_agreement_tolerance_ns": 20.0,
            "synce_ql": 4,
            "ptp_seq_id": index,
            "ptp_msg_type": "Sync",
            "msg_rate_hz": 20.0,
            "grandmaster_identity": "gm-a",
            "grandmaster_priority1": 128,
            "grandmaster_clock_class": 248,
            "grandmaster_clock_accuracy": 254,
            "offset_scaled_log_variance": 65535,
            "grandmaster_priority2": 128,
            "steps_removed": 1,
            "time_source": 160,
            "gnss_sync_status": "BOOTING",
            "satellites_tracked": -1,
            "gnss_available": False,
            "holdover": False,
            "attack_flag": False,
            "fault_flag": False,
            "run_id": 0,
            "label": "healthy",
        }
        collector_rows.append(row)
    feature = _extract_fixed_window(collector_rows, 0.01, 0.4)
    assert feature is not None
    assert feature["window_start_s"] == 0.01
    assert feature["offset_abs_max"] == 3.0
    overlapping = _extract_fixed_window(collector_rows, 0.21, 0.4)
    assert overlapping is not None
    assert overlapping["window_start_s"] == 0.21
