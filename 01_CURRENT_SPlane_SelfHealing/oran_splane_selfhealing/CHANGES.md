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
