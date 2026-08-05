# GNSS Time-Source Manipulation Evaluation

This test compares benign GNSS loss/holdover (H0) with malicious GNSS spoofing and jamming (H1). The timing ramps intentionally overlap. Spoofing reports healthy receiver state while delivering wrong time; jamming reports loss/holdover similarly to the benign case.

## Isolated H0-vs-H1 confusion matrix

| feature set | true | predicted | windows |
|---|---|---|---:|
| with_timesource | H0 | H0 | 45 |
| with_timesource | H0 | H1 | 15 |
| with_timesource | H1 | H0 | 43 |
| with_timesource | H1 | H1 | 75 |
| without_timesource | H0 | H0 | 16 |
| without_timesource | H0 | H1 | 44 |
| without_timesource | H1 | H0 | 19 |
| without_timesource | H1 | H1 | 99 |

## Per-scenario recall

| feature set | scenario | class | windows | recall |
|---|---|---|---:|---:|
| with_timesource | gnss_loss_holdover | H0 | 60 | 75.00% |
| with_timesource | gnss_spoof | H1 | 59 | 100.00% |
| with_timesource | gnss_jam | H1 | 59 | 27.12% |
| with_timesource | pooled_H1 | H1 | 118 | 63.56% |
| without_timesource | gnss_loss_holdover | H0 | 60 | 26.67% |
| without_timesource | gnss_spoof | H1 | 59 | 81.36% |
| without_timesource | gnss_jam | H1 | 59 | 86.44% |
| without_timesource | pooled_H1 | H1 | 118 | 83.90% |

## Leave-one-GNSS-attack-out under 2-of-3 persistence

| feature set | held family | RF recall | novelty | combined protection | episode detection | within 2 s |
|---|---|---:|---:|---:|---:|---:|
| with_timesource | gnss_spoof | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| with_timesource | gnss_jam | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| without_timesource | gnss_spoof | 30.17% | 0.00% | 30.17% | 91.67% | 91.67% |
| without_timesource | gnss_jam | 35.39% | 0.00% | 35.39% | 91.67% | 83.33% |

## Existing-family regression check

| domain | family | prior protection | current protection | delta | within 2 s |
|---|---|---:|---:|---:|---:|
| simulated | dos | 86.03% | 87.15% | +1.12% | 100.00% |
| simulated | gnss_jam | n/a | 0.00% | n/a | 0.00% |
| simulated | gnss_spoof | n/a | 0.00% | n/a | 0.00% |
| simulated | replay | 63.69% | 59.78% | -3.91% | 100.00% |
| simulated | spoof | 83.80% | 91.62% | +7.82% | 100.00% |
| timesafe_real | announce | 99.96% | 99.96% | +0.00% | 100.00% |
| timesafe_real | sync_follow_up | 99.66% | 99.66% | +0.00% | 100.00% |
| timesafe_real | sync_single_step | 99.66% | 99.66% | +0.00% | 100.00% |

## Verdict

The core fault-vs-attack claim is only partially supported in the closed-set test and **does not hold for unseen GNSS manipulation in this experiment**. Receiver status raises benign-holdover recall from 26.67% to 75.00% and closed-set spoof recall from 81.36% to 100%, but closed-set jam recall falls to 27.12%. Under true family holdout, the full system protects 0% of spoof and jam windows/episodes; the time-source channel changes protection by -30.17% for spoof and -35.39% for jam. PTP-only protection is also weak (30.17% and 35.39%), so live M-plane/receiver telemetry is necessary for observability but is not sufficient by itself for novel-family generalization. No thresholds or scenario parameters were tuned after observing these results.

Packet captures cannot provide `gnss_sync_status` or `satellites_tracked`; those fields require live `pmc`/receiver data or O-RU M-plane `o-ran-sync` telemetry. The pcap adapter therefore uses explicit unavailable defaults rather than inferring receiver health from PTP messages.
