# GNSS Time-Source Manipulation Evaluation

This fixed-seed evaluation compares (a) PTP-only, (b) PTP plus receiver status, and (c) PTP plus receiver status and independently derived oscillator-consistency features. No scenario or threshold was tuned after observing the results.

## H0-vs-H1 confusion matrix

| feature set | true | predicted | windows |
|---|---|---|---:|
| a_ptp_only | H0 | H0 | 17 |
| a_ptp_only | H0 | H1 | 43 |
| a_ptp_only | H1 | H0 | 18 |
| a_ptp_only | H1 | H1 | 100 |
| b_ptp_timesource | H0 | H0 | 44 |
| b_ptp_timesource | H0 | H1 | 16 |
| b_ptp_timesource | H1 | H0 | 40 |
| b_ptp_timesource | H1 | H1 | 78 |
| c_ptp_timesource_consistency | H0 | H0 | 60 |
| c_ptp_timesource_consistency | H0 | H1 | 0 |
| c_ptp_timesource_consistency | H1 | H0 | 0 |
| c_ptp_timesource_consistency | H1 | H1 | 118 |

## Per-scenario closed-set recall

| feature set | scenario | class | windows | recall |
|---|---|---|---:|---:|
| a_ptp_only | gnss_loss_holdover | H0 | 60 | 28.33% |
| a_ptp_only | gnss_spoof | H1 | 59 | 81.36% |
| a_ptp_only | gnss_jam | H1 | 59 | 88.14% |
| a_ptp_only | pooled_H1 | H1 | 118 | 84.75% |
| b_ptp_timesource | gnss_loss_holdover | H0 | 60 | 73.33% |
| b_ptp_timesource | gnss_spoof | H1 | 59 | 100.00% |
| b_ptp_timesource | gnss_jam | H1 | 59 | 32.20% |
| b_ptp_timesource | pooled_H1 | H1 | 118 | 66.10% |
| c_ptp_timesource_consistency | gnss_loss_holdover | H0 | 60 | 100.00% |
| c_ptp_timesource_consistency | gnss_spoof | H1 | 59 | 100.00% |
| c_ptp_timesource_consistency | gnss_jam | H1 | 59 | 100.00% |
| c_ptp_timesource_consistency | pooled_H1 | H1 | 118 | 100.00% |

## Leave-one-GNSS-attack-out under 2-of-3 persistence

| feature set | held family | RF recall | novelty | combined protection | episode detection | within 2 s |
|---|---|---:|---:|---:|---:|---:|
| a_ptp_only | gnss_spoof | 27.37% | 0.00% | 27.37% | 83.33% | 83.33% |
| a_ptp_only | gnss_jam | 37.08% | 0.00% | 37.08% | 100.00% | 100.00% |
| b_ptp_timesource | gnss_spoof | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | gnss_jam | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| c_ptp_timesource_consistency | gnss_spoof | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| c_ptp_timesource_consistency | gnss_jam | 0.00% | 91.57% | 91.57% | 100.00% | 100.00% |

## Adversarial stealth-spoof bound

The stealth variant keeps drift inside the configured holdover envelope and is evaluated without adding it to training. This bounds how much protection depends on obvious physics violations.

| feature set | RF recall | novelty | combined protection | episode detection | within 2 s |
|---|---:|---:|---:|---:|---:|
| a_ptp_only | 92.78% | 0.00% | 92.78% | 100.00% | 100.00% |
| b_ptp_timesource | 87.78% | 0.00% | 87.78% | 100.00% | 100.00% |
| c_ptp_timesource_consistency | 93.33% | 0.00% | 93.33% | 100.00% | 100.00% |

## Existing-family regression check

| domain | family | prior protection | current protection | delta | within 2 s |
|---|---|---:|---:|---:|---:|
| simulated | dos | 87.15% | 88.27% | +1.12% | 100.00% |
| simulated | gnss_jam | n/a | 91.57% | n/a | 100.00% |
| simulated | gnss_spoof | n/a | 0.00% | n/a | 0.00% |
| simulated | replay | 59.78% | 80.45% | +20.67% | 100.00% |
| simulated | spoof | 91.62% | 93.30% | +1.68% | 100.00% |
| timesafe_real | announce | 99.96% | 99.96% | +0.00% | 100.00% |
| timesafe_real | sync_follow_up | 99.66% | 99.66% | +0.00% | 100.00% |
| timesafe_real | sync_single_step | 99.66% | 99.66% | +0.00% | 100.00% |

## Verdict

The success criterion fails. Consistency changes unseen spoof protection from 27.37% PTP-only to 0.00%, while unseen jam changes from 37.08% to 91.57%. It therefore does not beat both ablations for every unseen GNSS family. This is a second negative result: the fault-vs-attack claim still does not hold generally for time-source manipulation. On the spec-conformant stealth spoof, consistency adds +5.56% over status-only, and its novelty contribution is 0%; that protection is closed-family RF transfer rather than detection of a physics violation.

## Design lesson

Receiver self-reported synchronization status must not be trusted as a standalone detection feature because the attack class it targets can forge or preserve that report. Physics consistency supplies independent evidence, but the stealth-spoof result is the explicit bound on that evidence. Receiver status and consistency should be corroborated with cross-source time comparison, authenticated telemetry, RF/environmental monitoring, or an independent reference clock.

## Fundamental limit

With a single time reference, a spoof that mimics healthy operation is in-distribution by construction and cannot be identified by anomaly detection from that reference alone. Detecting that case requires an independent time reference whose disagreement supplies evidence the compromised source cannot forge.

Packet captures cannot provide `gnss_sync_status` or `satellites_tracked`; those fields require live `pmc`/receiver data or O-RU M-plane `o-ran-sync` telemetry.
