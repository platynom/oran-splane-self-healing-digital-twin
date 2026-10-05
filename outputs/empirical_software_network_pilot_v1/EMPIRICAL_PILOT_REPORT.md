# Empirical software-network pilot v1: executed bounded evidence

## Result

Four calibrated, independent **free-running PTP protocol-observation** runs completed and passed structural validation. They are a feasibility sample—not evidence of physical timing quality, attacker behavior, or recovery effectiveness.

| Run | Condition | PTP records | Command evidence | Measured observation |
|---|---|---:|---|---|
| b2 | Baseline control | 899 | Baseline qdisc observed | PTP-timescale warning; no calibrated timing outcome. |
| n2 | Netem delay 1000 us, jitter 200 us, loss 1% | 872 | Qdisc command confirmed | PTP-timescale warning; impact remains unknown. |
| c2 | Authorised-source no-action control | 904 | Baseline qdisc observed | PTP-timescale warning; no calibrated timing outcome. |
| s4 | Authorised preferred-master stop | 1,334 | Stop recorded at `2026-09-10T05:26:05Z` | Receiver log selected the remaining advertised best-master identity after timeout; this is not recovery success. |

Full per-run counts, hashes, supplied/derived label separation, and retained failed attempts are in [EMPIRICAL_RUN_REGISTRY.json](EMPIRICAL_RUN_REGISTRY.json). Each completed run retains configuration, event records with UTC/monotonic time, process logs, pcap, manifest, and `validation.json`.

## What the evidence supports

The implementation ran isolated network namespaces with software PTP traffic, recorded the configured netem intervention, and observed a source-advertisement selection change in the source-stop condition. The no-action condition is a separate capture, preventing packet/window leakage across the two source-change conditions.

The receiver log repeatedly states `foreign master not using PTP timescale`. Therefore the records do **not** establish servo lock, offset improvement, clock accuracy, or successful recovery. `free_running 1` was intentionally set so the endpoint did not adjust a clock. All endpoints share the host software clock and are not independent oscillators.

## Retained failures and next evidence

Three source-stop attempts aborted prior to manifest finalization because the original expected-process termination path was unsafe; all are preserved and excluded from the calibrated comparison. The corrected `s4` attempt finalizes successfully.

Before any claim beyond protocol behavior, obtain a profile-appropriate configured PTP timescale, receiver management/servo observations, calibrated reference timing measurements, repeated run-level controls, and physically independent clock hardware. GNSS, SyncE, oscillator, O-RAN deployment, authentication, and physical recovery remain outside this pilot.
