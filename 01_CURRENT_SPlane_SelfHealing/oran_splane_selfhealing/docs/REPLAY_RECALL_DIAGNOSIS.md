# Replay Recall Diagnosis

Date: 2026-07-27

## Observed weakness

Leave-one-attack-out generalization from `results/tier2/leave_one_attack_out.csv`:

- Held-out `ptp_spoof`: unseen-family recall = 0.8715083798882681, n = 179.
- Held-out `ptp_replay`: unseen-family recall = 0.48044692737430167, n = 179.

## Diagnostic run

Diagnostic-only run using seed 1588, training with `ptp_replay` held out:

- Replay windows tested: 179.
- Replay recall: 0.48044692737430167.
- Replay predictions: `{'H0': 93, 'H1': 86}`.

Feature importance in the held-out replay model:

| Feature | Importance |
|---|---:|
| offset_std | 0.379547 |
| offset_abs_max | 0.334695 |
| offset_mean | 0.201976 |
| holdover_rate | 0.024502 |
| gnss_loss_rate | 0.020348 |
| path_delay_mean | 0.015489 |
| seq_regressions | 0.015480 |
| pdv_std | 0.005296 |
| synce_ql_max | 0.002666 |
| msg_irregularity | 0.000000 |

Median feature comparison:

| Scenario | offset_abs_max | pdv_std | seq_regressions | synce_ql_max | gnss_loss_rate | holdover_rate |
|---|---:|---:|---:|---:|---:|---:|
| gnss_loss_holdover | 24.723 | 17.796 | 0.0 | 1.0 | 0.05 | 0.05 |
| pdv_congestion | 22.549 | 20.922 | 0.0 | 1.0 | 0.00 | 0.00 |
| ptp_replay | 24.943 | 19.442 | 0.0 | 1.0 | 0.00 | 0.00 |
| ptp_spoof | 25.362 | 18.743 | 0.0 | 2.0 | 0.00 | 0.00 |
| synce_degrade | 22.931 | 17.932 | 0.0 | 4.0 | 0.00 | 0.00 |

## Why replay recall is weak

The current 0.4 s aggregate feature set makes unseen replay look like benign timing noise. Median `ptp_replay` has nearly the same `offset_abs_max`, `pdv_std`, `synce_ql_max`, `gnss_loss_rate`, and `holdover_rate` profile as `pdv_congestion` and healthy-ish benign windows. The intended replay cue, `seq_regressions`, has median 0.0 and only 0.015480 feature importance in the held-out model. `msg_irregularity` has zero importance because attacks were deliberately hardened to avoid message-type giveaways.

This means the classifier is learning mostly magnitude/statistical anomaly shape (`offset_std`, `offset_abs_max`, `offset_mean`) rather than protocol temporal consistency. That is acceptable as a realism stress test, but it explains why a never-seen replay family is confused with H0.

## Proposed fixes, not applied

1. Add protocol-temporal features that preserve ordering evidence beyond a 0/1 regression count:
   - duplicate sequence-ID ratio,
   - sequence gap entropy,
   - inter-arrival jitter by message type,
   - repeated `(seq_id, msg_type)` tuple rate,
   - monotonicity violation run length,
   - Sync-to-Follow_Up pairing latency statistics.

2. Use a two-branch discriminator:
   - branch A: physical timing features for spoof/fault separation,
   - branch B: protocol-state-machine anomaly score for replay/duplicate/out-of-order behaviour,
   - final governed decision combines calibrated probabilities.

3. Increase replay scenario diversity:
   - low-rate replay,
   - delayed replay without sequence regression,
   - replay during PDV,
   - duplicate Sync only,
   - duplicate Announce only,
   - replay with valid-looking sequence increments but stale origin timestamps.

4. Add leave-one-variant-out validation inside replay, not just leave-one-family-out, so improvements do not simply memorize a new replay signature.

No fixes were applied in this run because the task requested diagnosis and proposals only.
