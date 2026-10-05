# v8 deck — slide-by-slide source map

Deck: `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/ORAN_SPlane_PRISM_Review_v8.pptx` (42 slides).
The presented deck `ORAN_SPlane_PRISM_Review_v7_FINAL_PRESENTED_2026-09-29.pptx` is v8 slides 1, 2, 4, 7, 8, 13–19, 22, 24–39, 41
(v7 slide n → v8 slide: 1→1, 2→2, 3→4, 4→7, 5→8, 6→13, 7→14, 8→15, 9→16, 10→17, 11→18, 12→19, 13→22, 14→24, 15→25, 16→26,
17→27, 18→28, 19→29, 20→30, 21→31, 22→32, 23→33, 24→34, 25→35, 26→36, 27→37, 28→38, 29→39, 30→41).

Every local path below was checked to exist on 5 Oct 2026. Numbers were recomputed from raw files on 4–5 Oct
(`verify_claims_2026-10-04.py`, 44/44 PASS). External sources are not stored in the folder (no download access
from the working environment); their URLs are in section 3, with the exact clauses confirmed.

## 1. Path abbreviations

| Key | Path |
|---|---|
| ARCH | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/gap_coverage_2026-09-20/corrected_final/` — `splane_campaign_CORRECTED_2026-09-20.tgz` (all 168 runs: deep CSVs, context.json, verdicts, scripts `run/*`, freeze records), `EVALUATION_V4.json`, `AUDIT_AND_CORRECTIONS_2026-09-20.md` |
| TB | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results_2026-09-17/g87251_testbed_v2.tgz` — testbed configs `cfg/*.cfg`, `ptp_deep_extract.py`, `run/topology.sh`, `run/inject.py`, `run/flood.py`, `run/pmc_log.sh` |
| LOGS | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/ml_comparison_input/extracted_168run_ptp4l_logs/` |
| ML | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/ml_comparison_output/ML_VS_RULE_COMPARISON.md` (+ `.json`) |
| LIT | `01_CURRENT_SPlane_SelfHealing/literature-survey/papers/` |
| LATEST | `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/` (29 Sep documents) |
| VR | `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/verification_records/` |
| PILOT | `outputs/empirical_software_network_pilot_v1/` |

## 2. Slide map

| v8 | Slide | Project documents (in this folder) | Standards / literature |
|---|---|---|---|
| 1 | Worklet definition (image) | No separate source file found in the folder; image is embedded in the deck | Samsung PRISM worklet card |
| 2 | Title, team, mentors | — | — |
| 3 | Reviewer questions → slide map | VR `REVIEWER_HANDWRITTEN_NOTES.png`; VR `SESSION_RECORD_2026-10-03.md` (§6, §10) | — |
| 4 | O-RAN architecture and project boundary | LIT `Standards/ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf`; LIT `Standards/ETSI_TS_138401_NG-RAN_Architecture_R18.pdf`; LATEST `ORAN_SPlane_Testbed_Configuration_Reference_v2026-09-29.pdf` | ETSI TS 103 982 [4]; O-RAN.WG4.CUS.0; 3GPP TS 38.401 [11] |
| 5 | O-RAN functional split and layers | LIT `Standards/ETSI_TS_103982_…_v08.pdf` cl. 3.1, 6.3.3–6.3.6, 6.4.7; LIT `Standards/ETSI_TS_138401_…_R18.pdf` | [4], [11], [8], [9] |
| 6 | LLS-C1…C4 timing configurations | TB `run/topology.sh`; LATEST Testbed_Configuration_Reference; LIT `Government-Reports/BSI_5G_RAN_Risk_Analysis.pdf` | Armstrong (O-RAN.WG4.CUS.0 v06.00) [7]; RFC 7384 [1]; ETSI TR 104 106 [2]; TIMESAFE [10] |
| 7 | Timing requirements and security exposure | VR `V4_DECK_FACT_CHECK_2026-09-28.md`, `V5_VERIFICATION_LOG.md`, `V5_DISAGREEMENTS.md` (130 ns / ±1.5 µs scoping checks) | O-RAN.WG4.CUS.0 via Armstrong (WSTS 2022); ITU-T G.8271.1; TIMESAFE [10] |
| 8 | Attack–fault ambiguity, sub-scope | LATEST `ORAN_SPlane_Attack_vs_Benign_Classification_v2026-09-29.xlsx` (STANDARDS BASELINE, LOOK-ALIKES sheets) | IEEE 1588-2019 [5]; ITU-T G.8275.1 [6]; ETSI TR 104 106 [2] |
| 9 | Who attacks: agents and classes | — (literature slide) | ETSI TR 104 106 cl. 7.2, 7.4.1.2 [2]; RFC 7384 cl. 3.1, Table 1 [1]; TIMESAFE §4 [10] |
| 10 | Attack entry points (where/how) | ARCH tgz `run/scenarios.sh`, `run/run_gap.sh`, `run/inject_malformed.py`, `run/inject_wholesecond.py`; TB `run/inject.py`, `run/flood.py` | RFC 7384 cl. 3.1 [1] |
| 11 | Provenance of the 8 attacks | LATEST `ORAN_SPlane_Master_Test_Catalogue_v2026-09-29.pdf` (WG11 test IDs); LATEST `ORAN_SPlane_Parameter_Fault_Matrix_v2026-09-29.xlsx` (FAULT KEY threat mapping) | RFC 7384 cl. 3.2 [1]; ETSI TR 104 106 T-SPLANE-01…04 [2]; ETSI TS 104 105 [3]; TIMESAFE §4.1 [10]; IEEE 1588-2019 §8.2.4 [5] |
| 12 | Affected component and impact | LOGS (RU1–RU3 logs, 36 per scenario); TB `cfg/g87251.base` (free_running 1); VR `verify_claims_2026-10-04_output.txt` (F1–F6) | RFC 7384 Table 1 [1]; ETSI TR 104 106 [2]; TIMESAFE §6 [10]; 3GPP TS 38.133 via [8]; TS 38.104 [9] |
| 13 | Literature survey | LIT `arXiv/arXiv_2024_Colosseum_Open_RAN_Digital_Twin.pdf`; `arXiv/arXiv_2024_Digital_Twin_for_ORAN_Towards_6G.pdf`; `Elsevier/Elsevier_2023_OpenRAN_Gym_AI_ML_ORAN.pdf`; `Springer/P_Springer_2025_Time_Sensitive_Networking_Digital_Twin_for_STRIDE_Based_Security_Testing.pdf`; TIMESAFE repo README in `dataset/legitimate/timesafe_real_hardware_captures/s-plane_security_repo/` | TIMESAFE [10] (paper not stored locally) |
| 14 | Research gaps | LIT `IEEE/IEEE_2024_Federated_Continual_Learning_ORAN_Anomaly_Detection.pdf`; `Elsevier/P_Elsevier_2024_Adversarial_Machine_Learning_Threat_Analysis_and_Remediation_in_ORAN.pdf`; `Elsevier/P_Elsevier_2025_ORAN_xApps_Survey_and_Research_Challenges.pdf`; `IEEE/P_IEEE_2025_Anomaly_Detection_for_xApp_and_E2_Interface_Threats_in_ORAN_Near_RT_RIC.pdf` | as listed on the slide |
| 15 | Contribution positioning | ARCH `EVALUATION_V4.json`; ML | [5], [6], [2], O-RAN.WG4.CUS.0 |
| 16 | Standards followed | LATEST Attack_vs_Benign_Classification (STANDARDS BASELINE, SOURCES sheets); LATEST Parameter_Fault_Matrix (SOURCES sheet) | IEEE 1588-2019 [5]; O-RAN.WG4.CUS.0; ETSI TR 104 106 [2]; ITU-T G.8275.1 [6], G.8273.2, G.8262 |
| 17 | Testbed architecture | LATEST Testbed_Configuration_Reference; TB `run/topology.sh`, `cfg/*.cfg`; ARCH (archive contents — no PCAPs) | linuxptp 4.0 [14]; [5]; [6] |
| 18 | Configuration and platform limits | TB `cfg/g87251.base`; LATEST Testbed_Configuration_Reference; VR `V4_DECK_FACT_CHECK_2026-09-28.md` (live config readback); VR verify E1 | ITU-T G.8275.1 [6]; linuxptp `configs/G.8275.1.cfg` |
| 19 | Processing pipeline | TB `ptp_deep_extract.py`; ARCH deep CSVs; ARCH `run/decision_rule.py`, `run/decision_rule_v3.py` | [5], [6] |
| 20 | KPI sources | TB `ptp_deep_extract.py`, `run/pmc_log.sh`; LOGS (servo lines, pmc.jsonl); ARCH `cap/*/context.json`; ML (six features) | IEEE 1588-2019 [5]; linuxptp [14]; ETSI TS 103 982 cl. 6.3.3–6.3.6 [4] |
| 21 | KPI classification for recovery | ARCH `run/decision_rule.py`, `run/decision_rule_v3.py`; ARCH deep-CSV header; ARCH `cap/*/context.json` | [5], [6] |
| 22 | Dataset composition | ARCH tgz + `EVALUATION_V4.json`; LOGS (pmc.jsonl); VR verify A1–A6, G1 | — |
| 23 | Dataset provenance | `dataset/README.md`, `dataset/DATASET_MANIFEST.csv`; `dataset/legitimate/timesafe_real_hardware_captures/s-plane_security_repo/` (git remote); TB; PILOT `START_HERE_FINAL.md`; `99_ARCHIVE_OLDER_AND_SUPERSEDED/documents_2026-09-20_superseded_by_09-29/ORAN_Project_Walkthrough_2026-09-17.pdf` (August withdrawal) | TIMESAFE [10] |
| 24 | Fault-injection mechanisms | ARCH `run/scenarios.sh`, `run/run_gap.sh`, `run/inject_malformed.py`, `run/inject_wholesecond.py`, `run/bg_traffic.py`; LATEST Master_Test_Catalogue | IEEE 1588-2019 §8.2.4, §9.4 [5]; ETSI TS 104 105 [3] |
| 25 | Attack scenarios 1 of 2 | ARCH `EVALUATION_V4.json`, `cap/A*__r*/decision_v3.json`; LATEST `ORAN_SPlane_Packets_to_Classification_2026-09-29.xlsx` (PER-SCENARIO); LATEST Master_Test_Catalogue | [5], [6], [2] |
| 26 | Attack scenarios 2 of 2 | as 25 for A8, C1–C3; ARCH `cap/C1_removal__r*/inject.log`; LATEST AUDIT_AND_CORRECTIONS | [3], [5], [2] |
| 27 | Benign scenarios | as 25 for baseline, B2, B3, B7, B_bc_replacement; ARCH `results/b3_rerun.log`; LATEST AUDIT_AND_CORRECTIONS (B3 rebuild) | [6], [5] |
| 28 | Ambiguous case and catalogue coverage | LATEST Parameter_Fault_Matrix (MATRIX 144 × 16, FAULT KEY, GAP SUMMARY); ARCH `EVALUATION_V4.json` | ETSI TR 104 106 [2] |
| 29 | Classification method | ARCH `run/decision_rule.py`, `run/decision_rule_v3.py`; ARCH `cap/*/context.json` | [5], [6] |
| 30 | Campaign design and reproducibility | ARCH tgz `FROZEN.json`, `FROZEN_V2.json`, `FROZEN_V3.json`, `FROZEN_HARNESS_EPOCH2.json`, `results/campaign_v3.log`, `run/randparams.py`; ARCH `EVALUATION_V4.json` | — |
| 31 | Pipeline audit and reruns | LATEST `ORAN_SPlane_AUDIT_AND_CORRECTIONS_v2026-09-29.pdf`; ARCH `AUDIT_AND_CORRECTIONS_2026-09-20.md`; `…/gap_coverage_2026-09-20/_SUPERSEDED_withdrawn_numbers/` | — |
| 32 | Scenario-level results | ARCH `EVALUATION_V4.json`; LATEST Packets_to_Classification; VR verify B6–B8 | — |
| 33 | Aggregate performance | ARCH `EVALUATION_V4.json`; VR verify B4–B10 | — |
| 34 | Rule vs ML comparison | ML; `…/oran_splane_selfhealing/scripts/run_ml_vs_rule_comparison.py`; LOGS | — |
| 35 | Observability constraints behind the ML result | ML (features, importances); LOGS (88.0 / 44.5 / 28.0 servo lines per run, re-counted 5 Oct) | — |
| 36 | C1 detection boundary | ARCH `cap/C1_removal__r*/` deep CSVs and `inject.log`; ARCH `run/randparams.py`; VR `V5_VERIFICATION_LOG.md` (60.54 %); VR verify D2 | — |
| 37 | Verified limitations | ARCH `EVALUATION_V4.json`; ARCH `cap/B_bc_replacement__r*/context.json`, `decision_v3.json`, `run/decision_rule.py`; LOGS (pmc.jsonl); VR `V4_DECK_FACT_CHECK_2026-09-28.md` (GNSS scoping) | — |
| 38 | Delivery status and objectives | PILOT `S11_S12_CURRENT_REPORT.md` (port failover 5/5 vs 0/5); VR `V4_DECK_FACT_CHECK_2026-09-28.md` (worklet-objective audit) | — |
| 39 | Remaining work | LATEST Parameter_Fault_Matrix (GAP SUMMARY); slides 36–38 | — |
| 40 | Applicability beyond O-RAN | TB `cfg/g87251.base` (profile constants) | IEEE 1588 profiles list [13]; RFC 7384 [1]; ITU-T G.8275.1 [6] |
| 41 | Technical summary | ARCH `EVALUATION_V4.json`; ML; ARCH tgz | — |
| 42 | References | section 3 below | [1]–[14] |

## 3. External sources (confirmed clauses; not stored locally unless noted)

| # | Source | Confirmed content | Local copy |
|---|---|---|---|
| [1] | IETF RFC 7384, T. Mizrahi, Oct 2014 — https://www.rfc-editor.org/rfc/rfc7384.txt | cl. 3.1 attacker classes; cl. 3.2.1–3.2.12 threats; Table 1 | no |
| [2] | ETSI TR 104 106 V3.0.0 (2025-06) — https://www.etsi.org/deliver/etsi_tr/104100_104199/104106/03.00.00_60/tr_104106v030000p.pdf | cl. 7.2 threat agents; cl. 7.4.1.2 T-SPLANE-01…04, T-FRHAUL-01/02 | no |
| [3] | ETSI TS 104 105 V7.0.0 (2025-06) — https://www.etsi.org/deliver/etsi_TS/104100_104199/104105/07.00.00_60/ts_104105v070000p.pdf | tests 11.1.5.1.1, 11.1.5.2.1, 11.1.5.2.2, 11.1.5.3.1, 11.1.5.3.2, 24.2.1.1, 24.2.1.2 | no |
| [4] | ETSI TS 103 982 V8.0.0 (2024-01) | cl. 3.1, 6.3.3–6.3.6, 6.4.7 | **yes** — LIT `Standards/ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf` |
| [5] | IEEE Std 1588-2019 (paywalled) | message formats, data sets, §8.2.4, §9.4 | no |
| [6] | ITU-T G.8275.1 (paywalled) | profile constants, as cross-checked in VR `V4_DECK_FACT_CHECK_2026-09-28.md` | no |
| [7] | G. Armstrong, O-RAN Fundamentals, ATIS WSTS 2023 — https://wsts.atis.org/wp-content/uploads/2023/02/Greg-Armstrong_ORAN-Fundamentals.pdf | LLS-C1…C4, page 15; spec cited page 17 | no |
| [8] | S. Ruffini, Sync for 5G, ATIS 2018 — https://tam.atis.org/wp-content/uploads/2018/10/1_02_Ericsson_Ruffini_Sync-5G-What-Is-Needed.pdf | TS 38.133 3 µs, slide 6 | no |
| [9] | 3GPP TS 38.104 Rel-19 cl. 9.6.3.2 — https://itecspec.com/3gpp/38.104/s/9.6.3.2 | TAE 65 ns / 260 ns / 3 µs | no |
| [10] | Groen et al., TIMESAFE, ACM TOPS 28(5) 2025, doi:10.1145/3775060; arXiv 2412.13049v3 | §4, §4.1, §5.1, §6 quotes | data and README only: `dataset/legitimate/timesafe_real_hardware_captures/s-plane_security_repo/` |
| [11] | ETSI TS 138 401 Rel-18 | NG-RAN architecture | **yes** — LIT `Standards/ETSI_TS_138401_NG-RAN_Architecture_R18.pdf` |
| [12] | BSI 5G Risk Analysis: RAN v1.0, 20 Feb 2025 | GNSS jamming as RAN timing threat | **yes** — LIT `Government-Reports/BSI_5G_RAN_Risk_Analysis.pdf` |
| [13] | IEEE SA PTP profiles — https://sagroups.ieee.org/1588/ptp-profiles | profile list | no |
| [14] | linuxptp documentation — https://linuxptp.nwtime.org | ptp4l, pmc | no |

To make the folder self-contained, the open-access items without a local copy ([1], [2], [3], [7], [8], [10] arXiv PDF)
can be downloaded into `01_CURRENT_SPlane_SelfHealing/literature-survey/papers/Standards/` from the URLs above.
