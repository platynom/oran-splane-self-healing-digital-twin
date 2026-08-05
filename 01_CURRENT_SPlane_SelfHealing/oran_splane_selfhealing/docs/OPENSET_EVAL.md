# Open-Set / Novelty Evaluation

Total known-window novelty budget: 2.0%. Group mode splits this budget across timing/protocol, rate, and BMCA detectors and flags UNKNOWN when any group fires.

## Three-way comparison

| domain | family | mode | RF recall | novelty rate | combined protection | benign novelty FP |
|---|---|---|---:|---:|---:|---:|
| simulated | spoof | pre_bmca | 0.894 | 0.553 | 0.972 | 0.021 |
| simulated | spoof | bmca_global | 0.978 | 0.128 | 0.989 | 0.017 |
| simulated | spoof | bmca_group | 0.978 | 0.916 | 0.978 | 0.020 |
| simulated | replay | pre_bmca | 0.430 | 0.212 | 0.525 | 0.017 |
| simulated | replay | bmca_global | 0.480 | 0.000 | 0.480 | 0.023 |
| simulated | replay | bmca_group | 0.480 | 0.330 | 0.648 | 0.013 |
| simulated | dos | pre_bmca | 0.000 | 0.944 | 0.944 | 0.017 |
| simulated | dos | bmca_global | 0.000 | 0.000 | 0.000 | 0.023 |
| simulated | dos | bmca_group | 0.000 | 0.927 | 0.927 | 0.017 |
| simulated | gnss_spoof | pre_bmca | nan | nan | nan | nan |
| simulated | gnss_spoof | bmca_global | 0.000 | 0.000 | 0.000 | 0.020 |
| simulated | gnss_spoof | bmca_group | 0.000 | 0.000 | 0.000 | 0.023 |
| simulated | gnss_jam | pre_bmca | nan | nan | nan | nan |
| simulated | gnss_jam | bmca_global | 0.000 | 0.084 | 0.084 | 0.017 |
| simulated | gnss_jam | bmca_group | 0.000 | 0.000 | 0.000 | 0.017 |
| timesafe_real | announce | pre_bmca | 0.238 | 0.001 | 0.239 | 0.022 |
| timesafe_real | announce | bmca_global | 0.047 | 0.321 | 0.365 | 0.037 |
| timesafe_real | announce | bmca_group | 0.047 | 1.000 | 1.000 | 0.045 |
| timesafe_real | sync_follow_up | pre_bmca | 1.000 | 0.000 | 1.000 | 0.000 |
| timesafe_real | sync_follow_up | bmca_global | 0.997 | 0.020 | 1.000 | 0.011 |
| timesafe_real | sync_follow_up | bmca_group | 0.997 | 0.013 | 0.997 | 0.056 |
| timesafe_real | sync_single_step | pre_bmca | 1.000 | 1.000 | 1.000 | 0.019 |
| timesafe_real | sync_single_step | bmca_global | 1.000 | 1.000 | 1.000 | 0.026 |
| timesafe_real | sync_single_step | bmca_group | 1.000 | 1.000 | 1.000 | 0.038 |

## Per-group calibration thresholds

| domain | family | mode | group | score threshold | group budget | calibration windows |
|---|---|---|---|---:|---:|---:|
| simulated | spoof | bmca_global | global | > 0.644415 | 0.0200 | 297 |
| simulated | spoof | bmca_group | timing | > 0.634355 | 0.0018 | 297 |
| simulated | spoof | bmca_group | protocol | > 0.615495 | 0.0128 | 297 |
| simulated | spoof | bmca_group | rate | > 0.662644 | 0.0018 | 297 |
| simulated | spoof | bmca_group | bmca | > 0.812935 | 0.0018 | 297 |
| simulated | spoof | bmca_group | timesource | > 0.742023 | 0.0018 | 297 |
| simulated | replay | bmca_global | global | > 0.601422 | 0.0200 | 297 |
| simulated | replay | bmca_group | timing | > 0.644140 | 0.0018 | 297 |
| simulated | replay | bmca_group | protocol | > 0.816298 | 0.0128 | 297 |
| simulated | replay | bmca_group | rate | > 0.676392 | 0.0018 | 297 |
| simulated | replay | bmca_group | bmca | > 0.752992 | 0.0018 | 297 |
| simulated | replay | bmca_group | timesource | > 0.731720 | 0.0018 | 297 |
| simulated | dos | bmca_global | global | > 0.604225 | 0.0200 | 297 |
| simulated | dos | bmca_group | timing | > 0.623334 | 0.0018 | 297 |
| simulated | dos | bmca_group | protocol | > 0.611962 | 0.0128 | 297 |
| simulated | dos | bmca_group | rate | > 0.807236 | 0.0018 | 297 |
| simulated | dos | bmca_group | bmca | > 0.752992 | 0.0018 | 297 |
| simulated | dos | bmca_group | timesource | > 0.734222 | 0.0018 | 297 |
| simulated | gnss_spoof | bmca_global | global | > 0.598425 | 0.0200 | 297 |
| simulated | gnss_spoof | bmca_group | timing | > 0.612942 | 0.0018 | 297 |
| simulated | gnss_spoof | bmca_group | protocol | > 0.611130 | 0.0128 | 297 |
| simulated | gnss_spoof | bmca_group | rate | > 0.656687 | 0.0018 | 297 |
| simulated | gnss_spoof | bmca_group | bmca | > 0.754800 | 0.0018 | 297 |
| simulated | gnss_spoof | bmca_group | timesource | > 0.728472 | 0.0018 | 297 |
| simulated | gnss_jam | bmca_global | global | > 0.609187 | 0.0200 | 297 |
| simulated | gnss_jam | bmca_group | timing | > 0.619420 | 0.0018 | 297 |
| simulated | gnss_jam | bmca_group | protocol | > 0.615092 | 0.0128 | 297 |
| simulated | gnss_jam | bmca_group | rate | > 0.669003 | 0.0018 | 297 |
| simulated | gnss_jam | bmca_group | bmca | > 0.762532 | 0.0018 | 297 |
| simulated | gnss_jam | bmca_group | timesource | > 0.781705 | 0.0018 | 297 |
| timesafe_real | announce | bmca_global | global | > 0.608117 | 0.0200 | 156 |
| timesafe_real | announce | bmca_group | timing | > 0.651876 | 0.0018 | 156 |
| timesafe_real | announce | bmca_group | protocol | > 0.689014 | 0.0128 | 156 |
| timesafe_real | announce | bmca_group | rate | > 0.749710 | 0.0018 | 156 |
| timesafe_real | announce | bmca_group | bmca | > 0.489045 | 0.0018 | 156 |
| timesafe_real | announce | bmca_group | timesource | > 0.682256 | 0.0018 | 156 |
| timesafe_real | sync_follow_up | bmca_global | global | > 0.690623 | 0.0200 | 156 |
| timesafe_real | sync_follow_up | bmca_group | timing | > 0.746290 | 0.0018 | 156 |
| timesafe_real | sync_follow_up | bmca_group | protocol | > 0.754560 | 0.0128 | 156 |
| timesafe_real | sync_follow_up | bmca_group | rate | > 0.814586 | 0.0018 | 156 |
| timesafe_real | sync_follow_up | bmca_group | bmca | > 0.636600 | 0.0018 | 156 |
| timesafe_real | sync_follow_up | bmca_group | timesource | > 0.637727 | 0.0018 | 156 |
| timesafe_real | sync_single_step | bmca_global | global | > 0.671181 | 0.0200 | 132 |
| timesafe_real | sync_single_step | bmca_group | timing | > 0.586899 | 0.0018 | 132 |
| timesafe_real | sync_single_step | bmca_group | protocol | > 0.755891 | 0.0128 | 132 |
| timesafe_real | sync_single_step | bmca_group | rate | > 0.824904 | 0.0018 | 132 |
| timesafe_real | sync_single_step | bmca_group | bmca | > 0.718412 | 0.0018 | 132 |
| timesafe_real | sync_single_step | bmca_group | timesource | > 0.775746 | 0.0018 | 132 |

## Planned-GM-failover confounder

Held-run RF H1 false-positive rate: **0.0%**; group novelty false-positive rate: **0.0%**. A legitimate GM transition is not treated as H1 merely because identity changed.

## GM-identity-change ablation on real Announce

| feature set | RF recall | novelty rate | combined protection | benign novelty FP |
|---|---:|---:|---:|---:|
| full_bmca | 0.047 | 1.000 | 1.000 | 0.045 |
| without_gm_identity_changes | 0.047 | 1.000 | 1.000 | 0.045 |

TIMESAFE contains no benign planned-GM-change session. Its real-data benign false-positive estimate is therefore optimistic for deployments with legitimate re-parenting.

Removing `gm_identity_changes` leaves Announce combined protection at 100.0% versus 100.0% with all BMCA features. The result therefore is not a one-rule `GM changed = attack` detector; other relative BMCA transition features carry the signal.

Held-session TIMESAFE benign novelty false alarms range from 3.8% to 5.6%. This exceeds the nominal 2% budget and shows residual capture-to-capture domain shift; thresholds were not tuned on held sessions.

Single-step attack novelty is 100.0%; benign windows from the same capture are 3.8%. This does not support a whole-capture shift.

Closed-set limitation: training the real RF on Announce sessions and testing on Sync sessions produces 0% attack recall. BMCA observability does not solve cross-family closed-set specialization.

## Temporal persistence sweep

Window step: 0.200 s; failure window: 2.0 s. Persistence is applied independently to RF-H1 and UNKNOWN votes. Alarm rate counts persisted protective windows per hour, matching the operational cost calculation requested here. **Caveat:** `alarms/hour` counts persisted windows, not distinct operator-facing alarm episodes. A sustained anomaly spanning consecutive windows is one alarm; `episode alarms/hour` de-duplicates contiguous persisted windows within each session.

| domain | family | setting | benign FP | window alarms/hour | episode alarms/hour | window protection | episode detection | added latency (s) | mean TTD (s) | within 2 s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| simulated | dos | 1-of-1 | 18.46% | 3322.1 | 724.8 | 92.74% | 100.00% | 0.000 | 0.050 | 100.00% |
| simulated | gnss_jam | 1-of-1 | 2.35% | 422.8 | 362.4 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | gnss_spoof | 1-of-1 | 12.75% | 2295.3 | 1026.8 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | replay | 1-of-1 | 18.79% | 3382.6 | 724.8 | 64.80% | 100.00% | 0.000 | 0.217 | 100.00% |
| simulated | spoof | 1-of-1 | 21.14% | 3805.4 | 604.0 | 97.77% | 100.00% | 0.000 | 0.050 | 100.00% |
| timesafe_real | announce | 1-of-1 | 4.48% | 806.0 | 537.3 | 100.00% | 100.00% | 0.000 | 0.000 | 100.00% |
| timesafe_real | sync_follow_up | 1-of-1 | 5.62% | 1011.2 | 809.0 | 99.66% | 100.00% | 0.000 | 0.000 | 100.00% |
| timesafe_real | sync_single_step | 1-of-1 | 3.85% | 692.3 | 461.5 | 100.00% | 100.00% | 0.000 | 0.000 | 100.00% |
| simulated | dos | 2-of-3 | 18.79% | 3382.6 | 362.4 | 87.15% | 100.00% | 0.200 | 0.250 | 100.00% |
| simulated | gnss_jam | 2-of-3 | 0.67% | 120.8 | 60.4 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | gnss_spoof | 2-of-3 | 10.40% | 1872.5 | 543.6 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | replay | 2-of-3 | 18.79% | 3382.6 | 362.4 | 59.78% | 100.00% | 0.233 | 0.450 | 100.00% |
| simulated | spoof | 2-of-3 | 19.46% | 3503.4 | 302.0 | 91.62% | 100.00% | 0.200 | 0.250 | 100.00% |
| timesafe_real | announce | 2-of-3 | 2.24% | 403.0 | 134.3 | 99.96% | 100.00% | 0.200 | 0.200 | 100.00% |
| timesafe_real | sync_follow_up | 2-of-3 | 3.37% | 606.7 | 404.5 | 99.66% | 100.00% | 0.200 | 0.200 | 100.00% |
| timesafe_real | sync_single_step | 2-of-3 | 1.92% | 346.2 | 115.4 | 99.66% | 100.00% | 0.200 | 0.200 | 100.00% |
| simulated | dos | 3-of-5 | 17.45% | 3140.9 | 241.6 | 79.89% | 100.00% | 0.417 | 0.467 | 100.00% |
| simulated | gnss_jam | 3-of-5 | 0.00% | 0.0 | 0.0 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | gnss_spoof | 3-of-5 | 8.39% | 1510.1 | 302.0 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | replay | 3-of-5 | 17.45% | 3140.9 | 241.6 | 53.63% | 100.00% | 0.783 | 1.000 | 91.67% |
| simulated | spoof | 3-of-5 | 17.45% | 3140.9 | 241.6 | 84.92% | 100.00% | 0.400 | 0.450 | 100.00% |
| timesafe_real | announce | 3-of-5 | 2.24% | 403.0 | 134.3 | 99.91% | 100.00% | 0.400 | 0.400 | 100.00% |
| timesafe_real | sync_follow_up | 3-of-5 | 0.00% | 0.0 | 0.0 | 99.33% | 100.00% | 0.400 | 0.400 | 100.00% |
| timesafe_real | sync_single_step | 3-of-5 | 1.92% | 346.2 | 115.4 | 99.33% | 100.00% | 0.400 | 0.400 | 100.00% |
| simulated | dos | 4-of-7 | 16.11% | 2899.3 | 241.6 | 73.74% | 100.00% | 0.617 | 0.667 | 100.00% |
| simulated | gnss_jam | 4-of-7 | 0.00% | 0.0 | 0.0 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | gnss_spoof | 4-of-7 | 6.38% | 1147.7 | 241.6 | 0.00% | 0.00% | nan | nan | 0.00% |
| simulated | replay | 4-of-7 | 16.11% | 2899.3 | 241.6 | 44.69% | 83.33% | 1.080 | 1.280 | 66.67% |
| simulated | spoof | 4-of-7 | 16.11% | 2899.3 | 241.6 | 78.21% | 100.00% | 0.600 | 0.650 | 100.00% |
| timesafe_real | announce | 4-of-7 | 0.00% | 0.0 | 0.0 | 99.87% | 100.00% | 0.600 | 0.600 | 100.00% |
| timesafe_real | sync_follow_up | 4-of-7 | 0.00% | 0.0 | 0.0 | 98.99% | 100.00% | 0.600 | 0.600 | 100.00% |
| timesafe_real | sync_single_step | 4-of-7 | 0.00% | 0.0 | 0.0 | 98.99% | 100.00% | 0.600 | 0.600 | 100.00% |

Recommended setting: **2-of-3**. No evaluated setting reaches 95% within-2-second coverage for every family because simulated spoof is already 91.7% at 1-of-1. This setting is nearest the 2% weighted real benign-FP target and does not reduce spoof's within-window episode rate below that raw-detector baseline.

Combined protection is a defensive-routing metric, not proof of correct family classification.
