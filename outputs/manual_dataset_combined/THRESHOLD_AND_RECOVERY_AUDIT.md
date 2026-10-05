# Threshold and recovery audit

## Thresholds

| Value | Where applied | Origin/status | What it supports | What it does not support |
|---|---|---|---|---|
| 100 ns | `healing.loop.detect`: `offset_abs_max > 100` or `pdv_std > 100` | `config/default.yaml`, configured | A software anomaly trigger for calculated window features | Universal O-RAN timing requirement, production calibration, root cause |
| 0.4 s / 0.2 s | Feature window / step | Configured dataset aggregation | Feature reporting interval and known overlap | Independent-window count or exact event boundary |
| 2 of 3 | Open-set persistence | Configured decision rule | Delay of a software candidate decision | Physical fault duration or recovery deadline |
| 1.0 s / 2.0 s | Decision budget / simulation failure window | Software configuration | Code timing and simulator evaluation target | Universal two-second network failure/recovery claim |
| 20 ns | Source-agreement tolerance | Configuration | Simulation/live multisource comparison when three references are measured | Agreement in a single-source PCAP with default zeros |
| 6, 2, 1.5 ppb | Nominal holdover drift / tolerances | Configuration defaults | Simulator/consistency-envelope calculation | Oscillator calibration for the captured equipment |

Open-set thresholds are fitted/calibrated from the supplied training/calibration windows in `stats/openset_eval.py`; they are model thresholds, not physical service limits. They are currently meaningful only for simulated data because projected real sessions are excluded.

### Anomaly Detection Threshold (100 ns)

The `anomaly_threshold_ns` setting (100 ns) is a software detector trigger defined in `config/default.yaml` and applied in `healing/loop.py` (`offset_abs_max > threshold` or `pdv_std > threshold`). It triggers defensive self-healing logic when calculated window timing features exceed 100 nanoseconds.

This value is a configured software default. No file in this repository derives, calibrates, or experimentally measures this threshold against physical hardware. It is not mandated by any physical standard in this codebase.

To empirically justify this threshold for production deployment, the following would be required:
1. An explicit physical measurement point (such as NIC hardware timestamping or physical cross-domain tap).
2. A traceable reference clock (such as a GNSS receiver or rubidium atomic standard).
3. A stated physical service budget tied to a specific O-RAN profile and fronthaul network configuration.

## Recovery evidence

`healing/loop.py` selects candidate names after detection. `twin/model.py` forecasts their effect using the hard-coded `ACTION_EFFECT` decay/floor coefficients. The code does not record an external command, device response, or before/after physical measurement.

Therefore classify these names as follows:

- Configured: `failover_lls_c3` appears in configuration.
- Selectable by current loop: `safe_default`, `isolate_rogue_master`, `failover_gnss`, `failover_lls_c1`, `failover_lls_c2`, `reroute_path`, `holdover` depending on predicted label.
- Modeled: every action listed in `ACTION_EFFECT`.
- Executed/measured successful: none established by the current evidence.

The fail-closed route is `safe_default` for invalid telemetry, novelty, or low twin fidelity. This is a defensive software behavior, not proof that it repairs timing.

To claim recovery effectiveness, retain the action command/log, exact execution time, receiver timing before/after, a comparable control, and the measurement provenance.
