# Multi-Source Time-Reference Evaluation

This experiment cross-checks independent GNSS, upstream PTP/LLS-C, and peer/secondary references. Whole attack families and held benign runs remain outside model fitting. Results use 2-of-3 persistence.

## Four-way unseen-family comparison

| feature set | held family | RF recall | novelty | combined protection | episodes detected | within 2 s |
|---|---|---:|---:|---:|---:|---:|
| a_ptp_only | gnss_spoof_single_source | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| a_ptp_only | gnss_spoof_all_sources | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| a_ptp_only | gnss_jam | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | gnss_spoof_single_source | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | gnss_spoof_all_sources | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | gnss_jam | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| c_ptp_timesource_consistency | gnss_spoof_single_source | 92.78% | 0.00% | 92.78% | 100.00% | 100.00% |
| c_ptp_timesource_consistency | gnss_spoof_all_sources | 92.78% | 0.00% | 92.78% | 100.00% | 100.00% |
| c_ptp_timesource_consistency | gnss_jam | 0.00% | 87.08% | 87.08% | 100.00% | 100.00% |
| d_cross_source | gnss_spoof_single_source | 13.89% | 32.22% | 45.56% | 91.67% | 91.67% |
| d_cross_source | gnss_spoof_all_sources | 92.22% | 0.00% | 92.22% | 100.00% | 100.00% |
| d_cross_source | gnss_jam | 0.00% | 87.08% | 87.08% | 100.00% | 100.00% |

## Benign disagreement confounders

Rates are averaged across the three held-attack models. `H1 FP` is incorrect malicious classification; `UNKNOWN` is conservative novelty routing.

| feature set | benign scenario | H1 FP | UNKNOWN | combined protective alarm |
|---|---|---:|---:|---:|
| a_ptp_only | path_asymmetry_benign | 0.00% | 0.00% | 0.00% |
| a_ptp_only | peer_source_degraded | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | path_asymmetry_benign | 0.00% | 0.00% | 0.00% |
| b_ptp_timesource | peer_source_degraded | 0.00% | 0.00% | 0.00% |
| c_ptp_timesource_consistency | path_asymmetry_benign | 0.00% | 0.00% | 0.00% |
| c_ptp_timesource_consistency | peer_source_degraded | 0.00% | 0.00% | 0.00% |
| d_cross_source | path_asymmetry_benign | 0.00% | 0.00% | 0.00% |
| d_cross_source | peer_source_degraded | 0.00% | 2.26% | 2.26% |

## Methodology caveat

Related GNSS attack families remained in training for each held-scenario run. The configuration-C single-source result is therefore RF transfer from related families and is **not comparable** to the earlier strict unseen-GNSS-spoof result of 0%. This experiment measures the incremental effect of adding cross-source features; it does not re-test the strict unseen-spoof hypothesis.

## All-sources-compromised bound

When all references are shifted coherently, total protection is **92.22%**: RF contributes 92.22%, novelty contributes 0.00%, and configuration C was already 92.78%. Cross-source evidence therefore adds zero protection. This is the explicit upper-bound case: relative agreement cannot prove correctness when every reference shares the forgery.

## Existing-family regression check

| domain | family | prior | current | delta | within 2 s |
|---|---|---:|---:|---:|---:|
| simulated | dos | 88.27% | 88.27% | +0.00% | 100.00% |
| simulated | gnss_jam | 91.57% | 91.57% | +0.00% | 100.00% |
| simulated | replay | 80.45% | 80.45% | +0.00% | 100.00% |
| simulated | spoof | 93.30% | 93.30% | +0.00% | 100.00% |
| timesafe_real | announce | 99.96% | 99.96% | +0.00% | 100.00% |
| timesafe_real | sync_follow_up | 99.66% | 99.66% | +0.00% | 100.00% |
| timesafe_real | sync_single_step | 99.66% | 99.66% | +0.00% | 100.00% |

## Verdict

The success criterion fails: single-source protection changes from a best non-cross-source result of 92.78% to 45.56%, with worst benign H1 false positives of 0.00%. Within configuration D, novelty raises protection above its 13.89% RF recall, but total protection remains below configuration C. This is a third negative result and no parameters were tuned after measurement.
