# Changes

## 2026-08-06 - Live-validation capability audit (uncommitted)

- Audited Windows 11 and Ubuntu 22.04 WSL2 resources, installed tool versions, privilege paths, and physical timing-device availability.
- Exercised network namespaces, a veth pair, `tc netem`, and nanosecond-precision `tcpdump` capture under the actual WSL2 kernel, then confirmed all transient probe interfaces were cleaned up.
- Installed the previously missing `ethtool` and confirmed every visible interface is software-timestamp-only; the exposed Hyper-V `/dev/ptp0` is not a NIC PHC and no GNSS receiver is present.
- Recorded the dependency compatibility defect: the pinned requirements install on Python 3.12 but not Ubuntu's Python 3.10 because `numpy==2.4.1` requires Python 3.11 or newer.
- Added measured Phase 0 artifacts `docs/ENV_CAPABILITY_AUDIT.md` and `results/env_audit.csv`, including feasibility gates and a two-hour disk projection based on existing 90-second capture sizes.
- Added a pinned Python 3.10 Linux compatibility requirements set without changing the validated Python 3.12 dependency set.
- Added `scripts/live_collect.py` for namespace-aware polling of the six requested pmc datasets, canonical rolling CSV output, counter-derived message rate, version-3.1 field parsing, Ctrl-C flushing, and explicit SyncE degradation.
- Added `scripts/live_loop.py` to run live windows through the trained RF, grouped open-set detector, 1-of-1/2-of-3 persistence comparison, digital-twin governed recommendation, and latency/false-alarm artifact generation without applying actions.
- Added fixture tests for real pmc field recovery, port-counter message rate, unsupported management datasets, and absent synce4l behavior.
- Fixed the live-management path in `harness/netem_harness.sh` by assigning distinct master and slave UDS addresses; network namespaces do not isolate filesystem Unix sockets, so the previous shared default could make pmc query the wrong daemon. PTP traffic and impairment parameters are unchanged.
- Batched pmc management requests into one process per poll to preserve the configured subsecond live-window cadence, and stopped treating the normal `UNCALIBRATED` convergence state as holdover when a GM is present.
- Set the live poll default to 0.1 seconds after a real smoke test proved that 0.2 seconds plus pmc overhead yields only two samples in the unchanged 0.4-second model window (feature extraction requires at least three).
- Replaced buffer-relative live windows with a fixed 0.2-second grid after the smoke transcript exposed nonmonotonic duplicate window starts; added a scheduling-jitter regression test and one-shot pmc outage/recovery logging for sequential harness scenarios.
- Removed duplicate model inference from live 1-of-1 reporting: the existing `PENDING` state is the raw protective flag before 2-of-3 persistence, preserving the metric while halving live decision compute.
- Corrected overlapping fixed-window extraction by translating observed sample timestamps onto the fixed grid while preserving their deltas; real scheduling jitter had otherwise shifted the feature extractor's internal anchor after the first window.
- Moved pmc sampling to a dedicated producer thread so Isolation Forest/twin inference cannot starve the 0.1-second collector and leave model windows under-sampled.
- Made every live-loop run stream the exact canonical input rows to a companion telemetry CSV and report attempted, valid, and under-sampled window counts, keeping long-run false-alarm denominators auditable.
- Fixed live PDV/frequency observability after the first long stream audit: `pdv_ns` is now the measured path-delay residual against a rolling median, and zero-valued linuxptp rate output falls back to the observed offset slope. The original runs remain preserved and are not relabelled.
- Added `scripts/analyze_live_validation.py` to regenerate exact long-baseline false-alarm/episode rates, corrected mixed-phase metrics, switch-local planned-GM results, latency, and live-pmc-vs-pcap feature coverage from preserved raw artifacts.
- Completed and documented live validation: a corrected 600.34-second mixed run, 87.60-minute uninterrupted benign telemetry segment (two-hour target explicitly not achieved), real two-master failover, 10/28 live-pmc versus 14/28 pcap feature coverage, measured false alarms, deduplicated operator burden, and latency/deadline results.
- Updated `PROJECT_STATUS.md` and plain-language `TEAM_REPORT.md` with live evidence and the newly discovered whole-session domain shift, pmc missing-data blind spot, and exact blocked items.
- Final gates passed in Ubuntu/Python 3.10: 42 tests in 268.13 seconds, Tier 1 end-to-end reproduction, and eight-seed Tier 2 report regeneration. The repeated Windows pytest failures were confirmed as temporary-directory ACL errors rather than test assertion failures.
- Added `harness/planned_gm_failover.sh`, a reversible three-namespace/two-master software BMCA experiment that stops preferred master A and measures legitimate re-parenting to master B through the same live collector/loop path.
- Added a thin `harness/live_scenario_sequence.sh` orchestrator for the required live PDV/loss/holdover recommendation-only demonstration, retaining separate real pcaps and UTC phase markers.

## 2026-08-05 - Multi-source increment (uncommitted)

- Added independently noisy/drifting GNSS, upstream PTP/LLS-C, and peer reference traces with a configured healthy agreement tolerance.
- Added H1 single-source and coherent all-source GNSS spoof scenarios plus H0 degraded-peer and benign-path-asymmetry disagreement confounders.
- Added seven relative cross-source consensus/disagreement features and an independently budgeted `cross_source` open-set group; raw reference values do not enter `FEATURE_COLUMNS`.
- Added leakage-resistant four-way evaluation under 2-of-3 persistence, benign-confounder false-positive measurements, an all-sources-compromised bound, and existing-family regression reporting.
- Recorded the untuned third negative result: cross-source features add no combined protection over consistency-only for single-source spoofing (93.33% to 93.33%); coherent all-source spoofing has 0% novelty contribution and is protected only by closed-family RF transfer.
- Disabled cross-source features and research-only scenarios in the shipped configuration-C path; moved reference-noise generation to an independent deterministic RNG so disabled research telemetry cannot perturb legacy scenario results.
- Verified the gated default exactly restores post-consistency protection and deadlines; added the related-family methodology caveat and coherent all-source relative-agreement bound to the multi-source report.
- Added `docs/SOFTWARE_FEATURE_WORK_CLOSED.md` to close software feature engineering and direct further work to independently trustworthy Tier-3 timing evidence.
- Refreshed the root and active READMEs, `PROJECT_STATUS.md`, and plain-language `TEAM_REPORT.md` to the final 28-feature, 39-test configuration-C state and all three negative results.

## 2026-08-05

- Added the GNSS design lesson that receiver self-reported synchronization status is attacker-influenced and must be corroborated rather than trusted as a standalone detection signal.
- Added a configuration-backed oscillator holdover envelope and made benign GNSS holdover follow that physical specification explicitly.
- Added four derived physics-consistency features and an independently budgeted `consistency` open-set group; calibration uses only benign training runs and preserves held-run isolation.
- Added the unelevated `gnss_spoof_stealth` evaluation variant, which remains inside the oscillator envelope and is excluded from training datasets.
- Extended GNSS evaluation to fixed three-way PTP/status/consistency ablations, closed-set confusion and recall, persisted unseen-family episode metrics, stealth bounds, and existing-family regression deltas.
- Recorded the untuned second negative result: consistency recovered unseen jam to 91.57% protection but unseen spoof remained 0%, below the 27.37% PTP-only result.
- Documented the fundamental single-reference observability limit and the requirement for an independent reference to detect an otherwise in-distribution spoof.

## 2026-07-27

- Config-only validation change: expanded `stats.seeds` in `config/default.yaml` from 6 seeds to 8 seeds (`31415`, `27182` added) so `scripts/run_tier2.py` regenerates tighter multi-seed confidence intervals.
- Config-only external-data validation change: set `data_source.backend: pcap` and `data_source.pcap_path: data/external/timesafe_prod_successful_announce_attack_ptp.pcap` after downloading the public TIMESAFE capture from `genesys-neu/s-plane_security`.
- Documentation-only addition: created `docs/REPLAY_RECALL_DIAGNOSIS.md` with the requested unseen-replay recall diagnosis and proposed fixes. No fixes were applied.
- Validation-run helper additions: created `scripts/run_netem_interactive_wsl.sh`, `scripts/launch_netem_interactive.ps1`, and `scripts/launch_netem_interactive.cmd` to let the user enter the WSL sudo password while the netem output is logged to `results/tier2/netem_interactive.log`.
- Real netem validation status: WSL installed `linuxptp`, `tcpdump`, and `iproute2`; baseline and PDV real `ptp4l` captures were produced and ingested. The requested all-scenario run did not complete because `netem_loss.pcap` contained no complete Sync/Delay_Req/Delay_Resp exchange recoverable by `pcap_to_telemetry()`, so the harness aborted before holdover.
- Real netem rerun status after user-provided harness fixes: reran all four scenarios for 90 s. `baseline`, `pdv`, and `loss` succeeded and were combined into `results/tier2/netem/netem_telemetry.csv`; `holdover` failed ingestion because its pcap had no Delay_Req/Delay_Resp exchange.
- Documentation-only addition: created `docs/NETEM_LOSS_DIAGNOSIS.md` with packet-type counts and root-cause analysis for the previous loss failure and current holdover ingestion failure.
- Real-data validation addition: downloaded matching public TIMESAFE CSV blobs, generated `results/tier2/timesafe_external_predictions.csv` and `results/tier2/timesafe_domain_gap.csv`, and wrote `docs/REAL_DATA_VALIDATION.md`. No model retraining was performed.
- Git hygiene update: added root-level ignore rules for nested virtual environments, pcaps, external validation datasets, dataset CSV/parquet blobs, and Tier 2 seed/netem caches so validation artifacts stay local and are not committed.
- Genuine Tier 2 harness bug fix: added a short pcap flush/stable-size wait in `harness/run_netem_scenarios.py` before ingestion. Very small loss/holdover captures could be ingested before `tcpdump` had fully closed/flushed the pcap, causing false `syncs_seen=0` failures even though delayed parsing recovered holdover rows.
- Real-feature ingest update: decoded IEEE-1588 Announce fields in `ingest/ptp_wire.py` and propagated clock-class/time-source status plus true packet message types through `ingest/pcap_ingest.py` without changing the canonical telemetry schema.
- Live-status adapter addition: added fixture-testable `pmc` and `synce4l` parsers in `ingest/sync_status.py`, with the production `SUBSCRIBE_EVENTS_NP` and O-RU M-plane NETCONF/YANG paths documented.
- Calibration evaluation fix: changed `scripts/calibrate_real.py` from a random within-file window split to multi-file, capture-grouped holdout; added leave-one-attack-family-out evaluation, class counts, and Wilson 95% confidence intervals.
- Reproducibility addition: added `scripts/prepare_timesafe_sessions.py` to derive labelled benign/attack telemetry from released TIMESAFE capture label intervals while retaining source capture identity.
- Test additions: added Announce field decoding, true PTP message-mix/status propagation, live sync-status parser, capture-isolation, and confidence-interval tests.
- Documentation addition: added `docs/REAL_FEATURES_AUDIT.md` with measured 6/10 to 9/10 real-feature coverage, leakage-proof calibration, and limitations.
- No Tier-1 logic was changed. Tier-2 changes are limited to the requested real-data parsing and leakage-resistant evaluation paths.
- 2026-08-04: Added canonical `msg_rate_hz` telemetry, trailing-one-second decoded PTP message rates for PCAP ingestion, and `msg_rate_mean`/`msg_rate_std` window features while retaining the original ten features.
- 2026-08-04: Added H1 `ptp_dos_flood` (`attack_family=dos`) and the overlapping H0 `traffic_burst` confounder; extended leave-one-attack-out output/reporting to spoof, replay, and DoS families.
- 2026-08-04: Added DoS/confounder and real-message-rate regression tests, and marked attack-roadmap family #4 covered. No external data, prior-work tree, or model calibration logic was changed.
- 2026-08-04: Versioned Tier 2 multi-seed cache entries by the active feature and H1-scenario definitions, preventing stale pre-DoS metrics from being reused while preserving all prior cache files.
- 2026-08-04: Regenerated the local ignored TIMESAFE session derivatives from their original labelled PCAPs so message rate is capture-derived, then reran capture-isolated calibration; the primary 2.04% benign-FP / 100% attack-TP result was unchanged.
- 2026-08-05: Refreshed the root README, active README, and `PROJECT_STATUS.md` with the measured DoS/confounder results, 18-test regression count, and 11-of-12 real-feature coverage before the DoS checkpoint commit.
- 2026-08-05: Added `discriminator.openset.NoveltyDetector`, using scaled Isolation Forest scores and a configurable quantile threshold that budgets known-window novelty flags at 2% by default.
- 2026-08-05: Added optional UNKNOWN routing in the governed healing loop; novel anomalies select `safe_default` with an auditable conservative-response reason, while callers without a fitted novelty detector retain existing behavior.
- 2026-08-05: Added leakage-resistant simulated and TIMESAFE open-set evaluation plus tests for OOD detection, known-data calibration, UNKNOWN healing, and unseen-DoS protective coverage.
- 2026-08-05: Enabled normal governed-loop use by fitting the novelty detector on the classifier's training split and attaching it to the trained RF; `choose_action` discovers it automatically while preserving explicit injection and disabled-mode compatibility.
- 2026-08-05: Measured open-set results: simulated unseen DoS improved from 0% RF-only recall to 94.4% combined protective coverage at 1.68% benign novelty false alarms; real held-out Announce changed only from 23.8% to 23.9%, which remains an explicit limitation.
- 2026-08-05: Documented that the real Announce miss is a BMCA feature-observability gap rather than a novelty-threshold problem, and flagged the real single-step capture's 100% novelty rate for session-shift sanity checking.
- 2026-08-05: Propagated parsed Announce BMCA attributes through canonical telemetry and added seven relative transition/plausibility window features; raw grandmaster identity remains telemetry-only and no MAC or high-cardinality identity enters `FEATURE_COLUMNS`.
- 2026-08-05: Updated simulated `ptp_spoof` to advertise a forged superior GM and added H0 `planned_gm_failover` as a legitimate re-parenting confounder.
- 2026-08-05: Added capture-isolated BMCA feature-importance export, measured pre/post open-set comparisons, same-capture single-step shift verdict generation, and focused BMCA leakage/confounder tests.
- 2026-08-05: Prevented heterogeneous-feature dilution in novelty scoring by combining calibrated Isolation Forest views over all features, the original timing/rate block, and the BMCA block under one global known-window false-alarm budget.
- 2026-08-05: Measured the real BMCA effect: held-out Announce combined protection increased from 23.9% to 99.97% at 2.24% same-capture benign novelty flags; documented the simultaneous closed-set cross-family regression rather than presenting it as universally solved.
- 2026-08-05: Replaced the interim mixed-view novelty score with configurable `global` and weighted-Sidak `group` modes. Group mode independently fits timing, protocol-regularity, message-rate, and BMCA Isolation Forests and flags UNKNOWN when any group fires; thresholds are calibrated on a known-benign training run or the largest available known-benign capture, with a larger configurable share of the 2% budget assigned to discrete replay signals.
- 2026-08-05: Added reproducible three-way comparison, per-group threshold, planned-GM-failover false-positive, and GM-identity-change ablation artifacts; documented that TIMESAFE lacks benign GM-change sessions.
- 2026-08-05: Added configurable temporal N-of-M persistence for novelty and RF-H1 decisions, with a stateful governed-loop wrapper and 2-of-3 default. Added 1-of-1/2-of-3/3-of-5/4-of-7 sweeps covering window false alarms, alarms/hour, per-family protection, episode detection, added latency, and decisions within the 2 s failure window.
- 2026-08-05: Distinguished persisted-window alarm rates from operator-facing alarm episodes by de-duplicating contiguous benign protective runs per capture/run and reporting both rates.
- 2026-08-05: Added repository ignore rules for regenerable pytest and Codex scratch directories after the pre-commit audit exposed ACL-hidden test outputs; no files were deleted or moved.
- 2026-08-05: Refreshed the root README, `01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md`, and root `TEAM_REPORT.md` to the validated 19-feature, 28-test BMCA/open-set/2-of-3 persistence checkpoint and current limitations.
- 2026-08-05: Added the O-RAN time-source telemetry channel (`gnss_sync_status`, `satellites_tracked`), fixture-testable pmc/YANG parsing, seven grouped GNSS/holdover features, and explicit pcap-unavailable defaults.
- 2026-08-05: Added hard GNSS spoof and jam attack families against benign GNSS loss/holdover, plus fixed confusion, leave-one-family-out, timesource ablation, persistence, and existing-family regression evaluations in `GNSS_TIMESOURCE_EVAL.md`.
- 2026-08-05: Routed cached real-session CSVs through canonical schema coercion so captures ingested before the GNSS columns existed receive explicit unavailable defaults instead of failing feature extraction.
- 2026-08-05: Recorded the untuned GNSS finding: status features improve closed-set benign-holdover/spoof separation but unseen spoof and jam receive 0% full-system protection; PTP-only protection remains 30.17%/35.39%, so M-plane observability is necessary but insufficient.
## 2026-08-07

- Fixed a fail-open live-telemetry safety defect: absent or stale `pmc` timing fields are now represented as invalid (`NaN` plus explicit validity flags), never as a zero-nanosecond sync sample.
- Added canonical `offset_valid`, `path_delay_valid`, `telemetry_valid`, and `stale_s` fields. Validity is inferred for legacy complete sources while invalid live/log-derived samples remain explicit.
- Updated live collection to emit invalid canonical rows on failed polls and on `gmPresent false`, retaining outage evidence for persistence instead of dropping it.
- Made governed healing fail closed: invalid or incomplete windows bypass neither safety checks nor persistence and route to `UNKNOWN`/`safe_default` with an auditable reason.
- Propagated valid-sample quality through feature windows and made twin fidelity conservative for incomplete inputs. Updated linuxptp log ingestion to preserve a missing path delay as invalid rather than zero.
- Added and executed missing-data safety regression coverage before source changes; no scenario thresholds or model metrics were tuned.
- Live WSL holdover validation found a second representation of the same defect: local-master/ClockClass-255 holdover reports zero timing fields. It is now explicitly invalid, with a regression test based on the captured status combination.

## Fail-closed hardening (missing-telemetry safety)

Follow-up to the live-validation finding that zero-valued `pmc` fields were read
as healthy. See `docs/FAIL_CLOSED_DESIGN.md`.

- `healing/loop.py::telemetry_is_valid` now fails **closed on absent provenance**.
  Previously a window carrying no `telemetry_valid` / `valid_sample_fraction`
  defaulted to *valid* (`window.get(..., 1.0)`), i.e. the same permissive-default
  pattern that caused the original defect. A window that cannot prove it was built
  from observed telemetry is now rejected. Non-finite (`inf`) features are also
  rejected. Constants `VALIDITY_FRACTION_KEYS`, `REQUIRED_DECISION_FEATURES` added.
- `twin/model.py::fidelity_score` given the same treatment: absent provenance now
  yields `MIN_FIDELITY` (new named constant, 0.15) instead of implicit full trust.
  Post-guard reads changed from `.get(key, 0.0)` to direct indexing so a future
  regression fails loudly rather than silently scoring 1.0.
- `tests/test_missing_data_safety.py`: 10 tests, written before the fix and
  verified failing against the original code. Adds provenance-absence,
  non-finite-value and twin-trust cases.
- `tests/test_openset.py`: two fixtures now assert provenance
  (`valid_sample_fraction=1.0`, `telemetry_valid=True`) so they exercise the
  novelty path rather than the validity gate. Behaviour unchanged; only the
  fixtures predated provenance.
- Audit sweep across `ingest/`, `scripts/`, `telemetry/`, `healing/`,
  `discriminator/`, `twin/`, `harness/`: no remaining silent numeric defaults in
  the decision path. The two broad `except Exception` handlers were reviewed and
  are fail-safe (`live_loop.py` logs and stops; `run_netem_scenarios.py` records
  per-scenario status), not fail-open.

No regression: run_all accuracy 0.990 / recovery 1.000; multi-seed 0.991 ± 0.002,
recovery 1.000 ± 0.000, MTTR 0.933 ± 0.008 s; twin Pearson 0.998; 53 tests passing.
