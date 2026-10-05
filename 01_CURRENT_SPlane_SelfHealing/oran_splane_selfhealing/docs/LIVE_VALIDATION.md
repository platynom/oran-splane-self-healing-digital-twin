# Live Software Validation

Generated from live WSL2/linuxptp artifacts on 2026-08-06 and 2026-08-07. No result in this report is extrapolated from TIMESAFE or simulation.

## Environment

The run used Ubuntu 22.04.5 under WSL2 (`6.18.33.1-microsoft-standard-WSL2`), linuxptp 3.1.1, software timestamping, veth/network namespaces, and `tc netem`. The collector polled the slave's dedicated Unix management socket. Full details and hardware probes are in `ENV_CAPABILITY_AUDIT.md` and `results/env_audit.csv`.

`PORT_SERVICE_STATS_NP` is not supported by linuxptp 3.1.1. `synce4l` is absent, so SyncE QL is explicitly DNU/unavailable rather than invented. No physical NIC PHC or GNSS receiver was present.

## Live Pipeline

`scripts/live_collect.py` polls `TIME_STATUS_NP`, `CURRENT_DATA_SET`, `PARENT_DATA_SET`, `PORT_DATA_SET`, `PORT_SERVICE_STATS_NP`, and `PORT_STATS_NP`. It streams canonical telemetry, derives message rate from port counters, derives PDV from the rolling measured path delay, and derives observed frequency from offset slope when linuxptp reports no rate offset.

`scripts/live_loop.py` runs the existing 28-feature pipeline and logs recommendations only:

```text
pmc -> canonical telemetry -> 0.4 s windows -> RF + grouped open set
    -> 2-of-3 persistence -> twin verification -> logged recommendation
```

It never changed ptp4l, qdiscs, routes, or clock state.

## Feature Coverage

Coverage was measured over the first 60 seconds of the corrected live PDV session and its matching pcap.

| Source | Nonconstant model features | Total |
|---|---:|---:|
| Live pmc | 10 | 28 |
| PTP pcap | 14 | 28 |

Live pmc made offset, delay/PDV, message mix, message rate, and derived consistency behavior nonconstant. Pcap additionally exposed sequence irregularity and holdover/degraded-exchange behavior. Neither source supplied live SyncE QL, O-RU GNSS receiver status, or satellite count. BMCA transition features correctly remained constant in the single-GM 60-second coverage slice.

The complete per-feature table is `results/live/live_feature_coverage.csv`.

## Ten-Minute Live Demo

The corrected run lasted **600.34 seconds**, emitted 4,345 canonical rows, attempted 2,998 fixed windows, and produced 2,167 valid windows. 831 windows were skipped because real command scheduling left fewer than three samples; none were filled with synthetic values.

| Real impairment | Valid windows | H1 | UNKNOWN | Protective after 2-of-3 | Mean latency | Max latency |
|---|---:|---:|---:|---:|---:|---:|
| PDV | 482 | 0.00% | 99.79% | 99.79% | 0.193 s | 0.404 s |
| Loss | 740 | 0.00% | 57.97% | 57.97% | 0.109 s | 0.298 s |
| Holdover impairment | 945 | 0.00% | 0.00% | 0.00% | 0.001 s | 0.157 s |

All valid ten-minute decisions were inside the configured 1-second decision budget. The holdover result is a negative finding: under severe loss the slave repeatedly selected its local clock and pmc returned zero offset/path-delay fields, so the current anomaly gate interpreted missing timing evidence as healthy. Live ingestion must add an explicit stale/missing-management-data signal before this path is deployment-ready.

Artifacts: `results/live/live_loop_10min_corrected.csv`, companion telemetry CSV, transcript, summary JSON, separate PDV/loss/holdover pcaps, and `mixed_phase_metrics.csv`.

## Benign Baseline

The target was at least two hours. The uninterrupted model/telemetry segment reached **5,255.80 seconds (87.60 minutes)** before the desktop execution session interrupted it. The two-hour target is therefore **BLOCKED / not achieved** and is not claimed. The decision stream covers 5,219.00 seconds (86.98 minutes) and 14,537 valid windows.

| Persistence | False-alarm windows | Window FP | False windows/hour | Deduplicated alarms | Operator alarms/hour |
|---|---:|---:|---:|---:|---:|
| 1-of-1 | 14,537 | 100.000% | 10,027.44 | 1 | 0.690 |
| 2-of-3 | 14,536 | 99.993% | 10,026.75 | 1 | 0.690 |

The window count is not the operator burden: nearly every window was part of one sustained UNKNOWN episode. Persistence cannot suppress a session-wide domain shift. Software-timestamped WSL offsets were commonly 1-3 microseconds, outside both the simulator-trained distribution and the 100 ns hardware-class budget, so this is a genuine sim-to-live calibration failure.

Mean end-to-end latency was **0.176 s** and maximum latency was **1.510 s**. **99.993%** of decisions met the internal 1-second budget and **100%** remained inside the proposal's 2-second failure window.

Artifacts: `baseline_2h_transcript.txt`, `baseline_2h_decisions_telemetry.csv`, `baseline_2h.pcap`, and `baseline_false_alarm_metrics.csv`. Names retain the intended target; this report records the exact shorter achieved duration.

## Planned Grandmaster Change

Two real ptp4l master instances advertised priority1 100 (A) and 150 (B). Master A was stopped at `2026-08-06T16:19:31Z`; the pcap confirms A traffic ended at 89.23 seconds while B continued through 179.08 seconds.

| Segment | Windows | H1 | UNKNOWN | Protective | Deduplicated protective episodes |
|---|---:|---:|---:|---:|---:|
| 60 s before switch | 158 | 0.00% | 100.00% | 100.00% | 1 |
| 5 s before through 10 s after | 50 | 0.00% | 30.00% | 30.00% | 1 |
| 60 s after switch | 242 | 0.00% | 1.65% | 1.65% | 1 |

The legitimate re-parent was **never labelled H1**. UNKNOWN cannot be attributed specifically to the GM change because the session was already 100% UNKNOWN in the preceding minute due to the software-timing distribution shift. This experiment fills the missing benign-GM-change software test, but it does not establish a production false-positive rate for hardware-timestamped planned failovers.

## Blocked And Tier 3

- **Two-hour continuous model run:** blocked at 87.60 minutes by desktop execution interruption; exact partial results are retained.
- **Live SyncE QL:** blocked because `synce4l` is absent and WSL interfaces are not SyncE hardware.
- **Hardware timing:** blocked because no interface exposes a physical PTP Hardware Clock.
- **Physical GNSS/O-RU telemetry:** blocked because no receiver or O-RU M-plane endpoint exists.
- **100 ns live validation:** impossible with this software-timestamped WSL setup; requires a hardware timestamp NIC and physical references.

The live tier is valuable because it revealed failures recordings did not: whole-session sim-to-live novelty, one >1 s decision, under-sampled windows, unsupported pmc datasets, and zero-valued management telemetry masking holdover. Those are the concrete Tier-3 engineering priorities.

## Final Regression

All gates ran in the audited Ubuntu/Python 3.10 environment using `requirements-py310.txt`:

```text
python -m pytest tests -p no:cacheprovider --basetemp /tmp/oran-pytest-final-20260807
42 passed in 268.13s

python scripts/run_all.py
All phases complete. See results/SUMMARY.md

python scripts/run_tier2.py
multiseed done for seeds=[1588, 2026, 7, 42, 101, 900, 31415, 27182]
Tier 2 complete. See results/tier2/TIER2_REPORT.md
```

The Windows Python run is not used as the final gate because host ACLs deny pytest enumeration/cleanup of temporary directories. The same tests pass in the target WSL environment with a native Linux base temp.
