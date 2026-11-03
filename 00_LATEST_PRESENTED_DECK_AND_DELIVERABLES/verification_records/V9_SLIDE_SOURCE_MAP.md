# v9 slide source map

Deck: `ORAN_SPlane_PRISM_Review_v9.pptx` (46 slides).

For unchanged material, the detailed clause-level lineage remains in `V8_SLIDE_SOURCE_MAP.md` §2. This map records the v9 number, the underlying source file and the relevant section. New and changed slides list their direct November/October evidence.

| v9 | Subject | Source file and section |
|---:|---|---|
| 1 | Worklet definition image | Embedded worklet image in frozen v8; `V8_SLIDE_SOURCE_MAP.md` §2 slide 1 |
| 2 | Title and team | Frozen v8 slide 2 |
| 3 | Reviewer question map | `verification_records/REVIEWER_HANDWRITTEN_NOTES.png`; `SESSION_RECORD_2026-10-03.md` §§6,10; v9 slide order |
| 4 | Architecture and project boundary | `V8_SLIDE_SOURCE_MAP.md` §2 slide 4; ETSI TS 103 982 clauses 3.1, 6.3 and 6.4.7 |
| 5 | Functional split and layers | `V8_SLIDE_SOURCE_MAP.md` §2 slide 5; ETSI TS 103 982 clauses 3.1, 6.3.3–6.3.6 and 6.4.7 |
| 6 | LLS-C1 to LLS-C4 | `ERRATA_V8_2026-11.md` §1; `V8_SLIDE_SOURCE_MAP.md` §2 slide 6; ETSI TR 104 106 `T-FRHAUL-02`, `T-SPLANE-01…04`; RFC 7384 §3.2 |
| 7 | Timing requirements | `V8_SLIDE_SOURCE_MAP.md` §2 slide 7; `V4_DECK_FACT_CHECK_2026-09-28.md`; ITU-T G.8271.1 |
| 8 | Attack–fault ambiguity | `ORAN_SPlane_Attack_vs_Benign_Classification_v2026-10-05.xlsx`, `STANDARDS BASELINE` and `LOOK-ALIKES`; `V8_SLIDE_SOURCE_MAP.md` slide 8 |
| 9 | Threat agents and access paths | `ERRATA_V8_2026-11.md` §2; TIMESAFE §4; ETSI TR 104 106 clauses 7.2 and 7.4.1.2 |
| 10 | Testbed entry points | Campaign `run/scenarios.sh` and `run/run_gap.sh`; `V8_SLIDE_SOURCE_MAP.md` §2 slide 10 |
| 11 | Attack provenance | `ERRATA_V8_2026-11.md` §3; RFC 7384 §3.2; ETSI TR 104 106 `T-SPLANE-01…04`; ETSI TS 104 105 §§11.1.5, 24.2.1 |
| 12 | Affected components and impact | `V8_SLIDE_SOURCE_MAP.md` §2 slide 12; `RESULTS_2026-10-05.md` §4 corrections |
| 13 | Literature survey | `V8_SLIDE_SOURCE_MAP.md` §2 slide 13; stored literature corpus |
| 14 | Research gaps | `V8_SLIDE_SOURCE_MAP.md` §2 slide 14; cited literature on slide |
| 15 | Contribution positioning | `V8_SLIDE_SOURCE_MAP.md` §2 slide 15 |
| 16 | Standards followed | `V8_SLIDE_SOURCE_MAP.md` §2 slide 16; stored standards corpus |
| 17 | Testbed configuration | G.8275.1 testbed archive and `V8_SLIDE_SOURCE_MAP.md` §2 slide 17 |
| 18 | Platform limits | Testbed `cfg/g87251.base`; `V8_SLIDE_SOURCE_MAP.md` §2 slide 18 |
| 19 | Processing pipeline | Campaign scripts and `V8_SLIDE_SOURCE_MAP.md` §2 slide 19 |
| 20 | KPI sources | IEEE 1588 message/data-set definitions; linuxptp 4.0 documentation; `ptp_deep_extract.py`; `V8_SLIDE_SOURCE_MAP.md` slide 20 |
| 21 | KPI recovery classes | `decision_rule.py`, `decision_rule_v3.py`; `V8_SLIDE_SOURCE_MAP.md` §2 slide 21 |
| 22 | Dataset produced | Campaign archive and `EVALUATION_V4.json`; `V8_SLIDE_SOURCE_MAP.md` §2 slide 22 |
| 23 | Dataset provenance | `dataset/README.md`; TIMESAFE repository; pilot `START_HERE_FINAL.md`; `V8_SLIDE_SOURCE_MAP.md` slide 23 |
| 24 | Fault injection | Campaign `run/inject.py`, `run/flood.py`, `run/scenarios.sh`; C2 note corrected from `ERRATA_V8_2026-11.md` §3 |
| 25 | Attack scenarios 1 of 2 | Campaign scenario definitions; `V8_SLIDE_SOURCE_MAP.md` §2 slide 25 |
| 26 | Attack scenarios 2 of 2 | `ERRATA_V8_2026-11.md` §§3–4; `RESULTS_2026-10-05.md` §§1,4,6; linuxptp `free_running` documentation |
| 27 | Benign scenarios | Campaign scenarios and `V8_SLIDE_SOURCE_MAP.md` §2 slide 27 |
| 28 | Ambiguous case and coverage | Campaign scenarios and `V8_SLIDE_SOURCE_MAP.md` §2 slide 28 |
| 29 | Classification method | Frozen decision-rule files; status note updated from `RESULTS_2026-10-05.md` §§1–6 |
| 30 | Experiment design | `EVALUATION_V4.json`, freeze records and `V8_SLIDE_SOURCE_MAP.md` §2 slide 30 |
| 31 | Experimental integrity | Freeze records, hashes and `V8_SLIDE_SOURCE_MAP.md` §2 slide 31 |
| 32 | Scenario-level classification | `EVALUATION_V4.json`; campaign run directories |
| 33 | Aggregate classification | `EVALUATION_V4.json`; `verify_claims_2026-10-04.py` |
| 34 | Recovery-loop design | `03_RECOVERY_LOOP_S-PLANE/RECOVERY_LOOP_DESIGN.md`, sections *Two detection channels*, *Localisation* and *Policy table*; `PREREGISTRATION.md` §3; stored RFC 7384 §§5.1.1, 5.9, 5.10.1; stored ITU-T G.8275.1 (02/2026) §6.3.1/Table 3 |
| 35 | Recovery-loop results | `03_RECOVERY_LOOP_S-PLANE/RESULTS_2026-10-05.md` §§1–6; `PREREGISTRATION.md` §§2–6 |
| 36 | Reactive/preventive/predictive | `05_REVIEWER_EVIDENCE_2026-11/03_RECOVERY_LOOP_S-PLANE/REACTIVE_VS_PROACTIVE.md`, sections *Direct answer to Q16*, *Mechanism classification* and *Measured reactive timing* |
| 37 | Measured/reference/not measured impact | `05_REVIEWER_EVIDENCE_2026-11/IMPACT_EVIDENCE_SCOPE.md`, sections *Evidence boundary* and *Per-attack impact* |
| 38 | Rule versus ML | Frozen v8 slide 34; `ML_VS_RULE_COMPARISON.md`; constant-baseline addition retained from v8 |
| 39 | Result interpretation | Frozen v8 slide 35; held-out comparison sources in `V8_SLIDE_SOURCE_MAP.md` |
| 40 | Unresolved cases | Frozen v8 slide 36; campaign evidence |
| 41 | Detection boundary | Frozen v8 slide 37; campaign evidence |
| 42 | Worklet status | `RESULTS_2026-10-05.md` §§1–6; `PREREGISTRATION.md`; original worklet milestone plan |
| 43 | Remaining work | `RECOVERY_LOOP_DESIGN.md` *Two detection channels*; `RESULTS_2026-10-05.md` §§1–2,6; frozen v8 slide 39 for still-open items |
| 44 | Applicability | Frozen v8 slide 40; IEEE PTP profile list; RFC 7384 scope |
| 45 | Technical summary | `EVALUATION_V4.json`; `ML_VS_RULE_COMPARISON.md`; `RESULTS_2026-10-05.md` §§1–6; `PREREGISTRATION.md` |
| 46 | References | Stored sources listed in slide notes; `CITATION_VERIFICATION_2026-11.md`; stored standards directory under `05_REVIEWER_EVIDENCE_2026-11/.../Standards/` |

## Evidence boundary

- **MEASURED** means observed in the software testbed.
- **REFERENCE** means a consequence stated by a stored standard or paper, not observed in this project.
- **NOT MEASURED** includes physical clock steering, nanosecond time error, RF performance and user-service availability.

