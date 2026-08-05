# Open-Set / Novelty Evaluation

Total known-window novelty budget: 2.0%. Group mode splits this budget across timing/protocol, rate, and BMCA detectors and flags UNKNOWN when any group fires.

## Three-way comparison

| domain | family | mode | RF recall | novelty rate | combined protection | benign novelty FP |
|---|---|---|---:|---:|---:|---:|
| simulated | spoof | pre_bmca | 0.894 | 0.553 | 0.972 | 0.021 |
| simulated | spoof | bmca_global | 0.894 | 0.128 | 0.911 | 0.020 |
| simulated | spoof | bmca_group | 0.894 | 0.006 | 0.899 | 0.027 |
| simulated | replay | pre_bmca | 0.430 | 0.212 | 0.525 | 0.017 |
| simulated | replay | bmca_global | 0.000 | 0.000 | 0.000 | 0.020 |
| simulated | replay | bmca_group | 0.000 | 0.670 | 0.670 | 0.023 |
| simulated | dos | pre_bmca | 0.000 | 0.944 | 0.944 | 0.017 |
| simulated | dos | bmca_global | 0.000 | 0.000 | 0.000 | 0.020 |
| simulated | dos | bmca_group | 0.000 | 0.899 | 0.899 | 0.020 |
| timesafe_real | announce | pre_bmca | 0.238 | 0.001 | 0.239 | 0.022 |
| timesafe_real | announce | bmca_global | 0.238 | 0.277 | 0.454 | 0.037 |
| timesafe_real | announce | bmca_group | 0.238 | 1.000 | 1.000 | 0.045 |
| timesafe_real | sync_follow_up | pre_bmca | 1.000 | 0.000 | 1.000 | 0.000 |
| timesafe_real | sync_follow_up | bmca_global | 1.000 | 0.003 | 1.000 | 0.022 |
| timesafe_real | sync_follow_up | bmca_group | 1.000 | 0.013 | 1.000 | 0.056 |
| timesafe_real | sync_single_step | pre_bmca | 1.000 | 1.000 | 1.000 | 0.019 |
| timesafe_real | sync_single_step | bmca_global | 1.000 | 1.000 | 1.000 | 0.058 |
| timesafe_real | sync_single_step | bmca_group | 1.000 | 1.000 | 1.000 | 0.038 |

## Per-group calibration thresholds

| domain | family | mode | group | score threshold | group budget | calibration windows |
|---|---|---|---|---:|---:|---:|
| simulated | spoof | bmca_global | global | > 0.655641 | 0.0200 | 297 |
| simulated | spoof | bmca_group | timing | > 0.703118 | 0.0020 | 297 |
| simulated | spoof | bmca_group | protocol | > 0.585462 | 0.0140 | 297 |
| simulated | spoof | bmca_group | rate | > 0.634577 | 0.0020 | 297 |
| simulated | spoof | bmca_group | bmca | > 0.820074 | 0.0020 | 297 |
| simulated | replay | bmca_global | global | > 0.607905 | 0.0200 | 297 |
| simulated | replay | bmca_group | timing | > 0.650827 | 0.0020 | 297 |
| simulated | replay | bmca_group | protocol | > 0.682100 | 0.0140 | 297 |
| simulated | replay | bmca_group | rate | > 0.648328 | 0.0020 | 297 |
| simulated | replay | bmca_group | bmca | > 0.755845 | 0.0020 | 297 |
| simulated | dos | bmca_global | global | > 0.615125 | 0.0200 | 297 |
| simulated | dos | bmca_group | timing | > 0.640698 | 0.0020 | 297 |
| simulated | dos | bmca_group | protocol | > 0.587813 | 0.0140 | 297 |
| simulated | dos | bmca_group | rate | > 0.804510 | 0.0020 | 297 |
| simulated | dos | bmca_group | bmca | > 0.755845 | 0.0020 | 297 |
| timesafe_real | announce | bmca_global | global | > 0.600123 | 0.0200 | 156 |
| timesafe_real | announce | bmca_group | timing | > 0.634560 | 0.0020 | 156 |
| timesafe_real | announce | bmca_group | protocol | > 0.651466 | 0.0140 | 156 |
| timesafe_real | announce | bmca_group | rate | > 0.749710 | 0.0020 | 156 |
| timesafe_real | announce | bmca_group | bmca | > 0.489045 | 0.0020 | 156 |
| timesafe_real | sync_follow_up | bmca_global | global | > 0.683746 | 0.0200 | 156 |
| timesafe_real | sync_follow_up | bmca_group | timing | > 0.743771 | 0.0020 | 156 |
| timesafe_real | sync_follow_up | bmca_group | protocol | > 0.754560 | 0.0140 | 156 |
| timesafe_real | sync_follow_up | bmca_group | rate | > 0.814586 | 0.0020 | 156 |
| timesafe_real | sync_follow_up | bmca_group | bmca | > 0.636600 | 0.0020 | 156 |
| timesafe_real | sync_single_step | bmca_global | global | > 0.659584 | 0.0200 | 132 |
| timesafe_real | sync_single_step | bmca_group | timing | > 0.622656 | 0.0020 | 132 |
| timesafe_real | sync_single_step | bmca_group | protocol | > 0.755891 | 0.0140 | 132 |
| timesafe_real | sync_single_step | bmca_group | rate | > 0.824904 | 0.0020 | 132 |
| timesafe_real | sync_single_step | bmca_group | bmca | > 0.718412 | 0.0020 | 132 |

## Planned-GM-failover confounder

Held-run RF H1 false-positive rate: **0.0%**; group novelty false-positive rate: **0.0%**. A legitimate GM transition is not treated as H1 merely because identity changed.

## GM-identity-change ablation on real Announce

| feature set | RF recall | novelty rate | combined protection | benign novelty FP |
|---|---:|---:|---:|---:|
| full_bmca | 0.238 | 1.000 | 1.000 | 0.045 |
| without_gm_identity_changes | 0.238 | 1.000 | 1.000 | 0.045 |

TIMESAFE contains no benign planned-GM-change session. Its real-data benign false-positive estimate is therefore optimistic for deployments with legitimate re-parenting.

Removing `gm_identity_changes` leaves Announce combined protection at 100.0% versus 100.0% with all BMCA features. The result therefore is not a one-rule `GM changed = attack` detector; other relative BMCA transition features carry the signal.

Held-session TIMESAFE benign novelty false alarms range from 3.8% to 5.6%. This exceeds the nominal 2% budget and shows residual capture-to-capture domain shift; thresholds were not tuned on held sessions.

Single-step attack novelty is 100.0%; benign windows from the same capture are 3.8%. This does not support a whole-capture shift.

Closed-set limitation: training the real RF on Announce sessions and testing on Sync sessions produces 0% attack recall. BMCA observability does not solve cross-family closed-set specialization.

## Temporal persistence sweep

Window step: 0.200 s; failure window: 2.0 s. Persistence is applied independently to RF-H1 and UNKNOWN votes. Alarm rate counts persisted protective windows per hour, matching the operational cost calculation requested here. **Caveat:** `alarms/hour` counts persisted windows, not distinct operator-facing alarm episodes. A sustained anomaly spanning consecutive windows is one alarm; `episode alarms/hour` de-duplicates contiguous persisted windows within each session.

| domain | family | setting | benign FP | window alarms/hour | episode alarms/hour | window protection | episode detection | added latency (s) | mean TTD (s) | within 2 s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| simulated | dos | 1-of-1 | 2.35% | 422.8 | 422.8 | 89.94% | 100.00% | 0.000 | 0.167 | 100.00% |
| simulated | replay | 1-of-1 | 2.35% | 422.8 | 422.8 | 67.04% | 100.00% | 0.000 | 0.133 | 100.00% |
| simulated | spoof | 1-of-1 | 2.68% | 483.2 | 483.2 | 89.94% | 100.00% | 0.000 | 0.283 | 91.67% |
| timesafe_real | announce | 1-of-1 | 4.48% | 806.0 | 537.3 | 100.00% | 100.00% | 0.000 | 0.000 | 100.00% |
| timesafe_real | sync_follow_up | 1-of-1 | 5.62% | 1011.2 | 809.0 | 100.00% | 100.00% | 0.000 | 0.000 | 100.00% |
| timesafe_real | sync_single_step | 1-of-1 | 3.85% | 692.3 | 461.5 | 100.00% | 100.00% | 0.000 | 0.000 | 100.00% |
| simulated | dos | 2-of-3 | 0.00% | 0.0 | 0.0 | 86.03% | 100.00% | 0.200 | 0.367 | 100.00% |
| simulated | replay | 2-of-3 | 0.00% | 0.0 | 0.0 | 63.69% | 100.00% | 0.400 | 0.533 | 100.00% |
| simulated | spoof | 2-of-3 | 0.00% | 0.0 | 0.0 | 83.80% | 91.67% | 0.200 | 0.255 | 91.67% |
| timesafe_real | announce | 2-of-3 | 2.24% | 403.0 | 134.3 | 99.96% | 100.00% | 0.200 | 0.200 | 100.00% |
| timesafe_real | sync_follow_up | 2-of-3 | 3.37% | 606.7 | 404.5 | 99.66% | 100.00% | 0.200 | 0.200 | 100.00% |
| timesafe_real | sync_single_step | 2-of-3 | 1.92% | 346.2 | 115.4 | 99.66% | 100.00% | 0.200 | 0.200 | 100.00% |
| simulated | dos | 3-of-5 | 0.00% | 0.0 | 0.0 | 78.77% | 91.67% | 0.400 | 0.418 | 91.67% |
| simulated | replay | 3-of-5 | 0.00% | 0.0 | 0.0 | 62.01% | 100.00% | 0.633 | 0.767 | 100.00% |
| simulated | spoof | 3-of-5 | 0.00% | 0.0 | 0.0 | 77.65% | 91.67% | 0.400 | 0.455 | 91.67% |
| timesafe_real | announce | 3-of-5 | 2.24% | 403.0 | 134.3 | 99.91% | 100.00% | 0.400 | 0.400 | 100.00% |
| timesafe_real | sync_follow_up | 3-of-5 | 0.00% | 0.0 | 0.0 | 99.33% | 100.00% | 0.400 | 0.400 | 100.00% |
| timesafe_real | sync_single_step | 3-of-5 | 1.92% | 346.2 | 115.4 | 99.33% | 100.00% | 0.400 | 0.400 | 100.00% |
| simulated | dos | 4-of-7 | 0.00% | 0.0 | 0.0 | 72.63% | 91.67% | 0.600 | 0.618 | 91.67% |
| simulated | replay | 4-of-7 | 0.00% | 0.0 | 0.0 | 55.31% | 100.00% | 1.050 | 1.183 | 91.67% |
| simulated | spoof | 4-of-7 | 0.00% | 0.0 | 0.0 | 71.51% | 91.67% | 0.600 | 0.655 | 91.67% |
| timesafe_real | announce | 4-of-7 | 0.00% | 0.0 | 0.0 | 99.87% | 100.00% | 0.600 | 0.600 | 100.00% |
| timesafe_real | sync_follow_up | 4-of-7 | 0.00% | 0.0 | 0.0 | 98.99% | 100.00% | 0.600 | 0.600 | 100.00% |
| timesafe_real | sync_single_step | 4-of-7 | 0.00% | 0.0 | 0.0 | 98.99% | 100.00% | 0.600 | 0.600 | 100.00% |

Recommended setting: **2-of-3**. No evaluated setting reaches 95% within-2-second coverage for every family because simulated spoof is already 91.7% at 1-of-1. This setting is nearest the 2% weighted real benign-FP target and does not reduce spoof's within-window episode rate below that raw-detector baseline.

Combined protection is a defensive-routing metric, not proof of correct family classification.
