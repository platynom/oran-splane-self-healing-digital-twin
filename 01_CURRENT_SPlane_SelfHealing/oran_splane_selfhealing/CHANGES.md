# Changes

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
