# Reviewer Evidence Pack Report — November 2026

**Date:** 2026-11-03  
**Project:** AI-Native Self-Healing O-RAN Network using a Digital Twin (O-RAN Open Fronthaul S-Plane PTP Timing Security)  
**Worktree branch:** `reviewer-evidence-2026-11` (base commit `368961d`)

---

## 1. Deliverables Produced

| File / Folder | Purpose |
|---|---|
| `REVIEWER_ANSWERS_2026-11.md` | Direct, evidence-backed answers to all 16 reviewer questions (`Q1`–`Q16`) plus the superseded v8 slide 38 delivery-status statement, with explicit `**Evidence:**` and `**Limits:**` blocks for every section. |
| `REVIEWER_ANSWERS_2026-11.pdf` | Formatted PDF rendering of `REVIEWER_ANSWERS_2026-11.md`, generated via `build_reviewer_answers_pdf.py`. |
| `CITATION_VERIFICATION_2026-11.md` | External citation audit of all 82 citation rows across v8 slides 4–12, 16, 20, 21, 24–27, 40 and `03_RECOVERY_LOOP_S-PLANE/STANDARDS_EVIDENCE.md`. |
| `IMPACT_EVIDENCE_SCOPE.md` | Per-attack scope matrix (`A1`, `A2`, `A3`, `A5`, `A8`, `C1`, `C2`, `C3`) strictly separating **MEASURED** testbed protocol outcomes, **REFERENCE** published/standards impacts, and **NOT MEASURED** physical/radio quantities, plus the Task 3b execution decision and 5 October workbook cross-check. |
| `03_RECOVERY_LOOP_S-PLANE/REACTIVE_VS_PROACTIVE.md` | Technical classification of the 5 October recovery loop into reactive runtime behavior, preventive provisioning, and unimplemented predictive forecasting. |
| `INDEPENDENT_CHECK_2026-11.md` | Sentence-by-sentence independent verification of all 105 factual sentences in `REVIEWER_ANSWERS_2026-11.md`, with before/after verdict counts and the four precision edits applied. |
| `ERRATA_V8_2026-11.md` | Detailed errata for all 5 `WRONG_CLAUSE` and `NOT_SUPPORTED` rows in `CITATION_VERIFICATION_2026-11.md` (`S06-02`, `S09-04`, `S11-10`, `S26-04`, `D05`), recording exact slide/document location, current wording, why it is wrong (with verbatim quote and PDF page), and exact corrected wording without modifying the frozen `.pptx` decks. |
| `REVIEWER_EVIDENCE_REPORT.md` | Summary report of the reviewer-evidence package, verification outputs, and remaining technical limits (this file). |
| `01_CURRENT_SPlane_SelfHealing/literature-survey/papers/Standards/` | 21 locally stored primary standards, technical reports, tutorials, man pages, and studies plus `SOURCES_MANIFEST.md` with retrieval URLs, byte sizes, and SHA-256 digests. |
| `verify_citation_quotes.py`, `verify_reviewer_answers.py`, `build_reviewer_answers_pdf.py` | Reproducible verification and PDF-generation scripts. |

---

## 2. Stored Sources and Excluded Sources

### Stored Sources (`21` files + `SOURCES_MANIFEST.md`)
All 21 files are stored in `01_CURRENT_SPlane_SelfHealing/literature-survey/papers/Standards/` and verified by SHA-256 in `SOURCES_MANIFEST.md` (all under 50 MB; largest is `ETSI_TS_103859_O-RAN_CUS_v12.0.1.pdf` at 8,413,012 bytes):
1. `RFC7384.txt` (IETF RFC 7384 text)
2. `RFC7384.pdf` (IETF RFC 7384 PDF)
3. `ETSI_TR_104106_V3.0.0.pdf` (O-RAN WG11 Security Threat Modeling and Risk Assessment)
4. `ETSI_TS_104105_V7.0.0.pdf` (O-RAN WG11 Security Test Specifications)
5. `ETSI_TS_103982_O-RAN_Architecture_Description_v08.pdf` (O-RAN WG1 Architecture Description V8.0.0)
6. `ETSI_TS_138401_NG-RAN_Architecture_R18.pdf` (3GPP TS 38.401 V18.1.0 NG-RAN Architecture)
7. `ETSI_TS_103859_O-RAN_CUS_v12.0.1.pdf` (O-RAN WG4 Control, User and Synchronization Plane Specification V12.0.1)
8. `ETSI_TS_138104_Rel19_v19.2.0.pdf` (3GPP TS 38.104 V19.2.0 NR Base Station Radio Transmission and Reception)
9. `Armstrong_ORAN_Fundamentals_WSTS_2023.pdf` (ATIS WSTS 2023 tutorial)
10. `Ruffini_Sync_for_5G_ATIS_2018.pdf` (ATIS WSTS 2018 tutorial)
11. `TIMESAFE_arXiv_2412.13049v3.pdf` (Groen et al., ACM TOPS 2025 / arXiv:2412.13049v3)
12. `BSI_5G_RAN_Risk_Analysis.pdf` (German BSI 5G RAN Risk Analysis v1.0, 2025)
13. `ITU_T_G.8271.1_2022.pdf` (ITU-T Rec. G.8271.1, 11/2022)
14. `ITU_T_G.8275.1_2026.pdf` (ITU-T Rec. G.8275.1, 02/2026)
15. `ITU_T_G.8273.2_2023.pdf` (ITU-T Rec. G.8273.2, 11/2023)
16. `ITU_T_G.8262_2024.pdf` (ITU-T Rec. G.8262, 05/2024)
17. `ITU_T_G.8261_2019.pdf` (ITU-T Rec. G.8261, 08/2019)
18. `IEEE_1588_PTP_Profiles.html` (IEEE SA public 1588 PTP profiles index)
19. `linuxptp_G.8275.1.cfg` (linuxptp v4.0 reference configuration)
20. `linuxptp_v4.0_ptp4l.8` (linuxptp v4.0 `ptp4l` manual page)
21. `linuxptp_v4.0_pmc.8` (linuxptp v4.0 `pmc` manual page)

### Sources Intentionally Not Stored and Why

| Source | Status | Reason |
|---|---|---|
| `IEEE Std 1588-2019` | **NOT STORED** | Paywalled IEEE standard; no purchase, subscription bypass, or license-gate circumvention was performed. Citations to specific IEEE 1588-2019 clauses are marked `NOT_ACCESSIBLE`. |
| O-RAN Alliance-branded WG4/WG11 member documents | **NOT STORED** | Publicly downloadable ETSI PAS equivalents (`ETSI TS 103 859`, `ETSI TS 103 982`, `ETSI TR 104 106`, `ETSI TS 104 105`) were stored instead; no click-through or member-only portal was accessed. |
| `ETSI TS 104 104 V9.1.0` | **NOT STORED** | Outside the permitted download set; its single reference in `STANDARDS_EVIDENCE.md` (`D17`) is marked `NOT_ACCESSIBLE`. |
| Secondary workshop/vendor notes (Arnold & Frost WSTS 2016, O'Donoghue 2016, Rodrigues slides, Calnex summaries, NVIDIA Cumulus docs) | **NOT STORED** | Secondary sources cited in earlier notes (`STANDARDS_EVIDENCE.md`). Primary ITU-T/IETF/ETSI specifications were stored and verified directly; unstored secondary references are marked `NOT_ACCESSIBLE` (or `WRONG_CLAUSE` in `D05`). |

---

## 3. Citation Verdict Counts (`CITATION_VERIFICATION_2026-11.md`)

| Verdict | Count | Meaning |
|---|---:|---|
| `CONFIRMED` | **63** | Directly supported by the locally stored primary standard, study, or manual page; verified automatically by `verify_citation_quotes.py`. |
| `WRONG_CLAUSE` | **2** | `S06-02` (`T-FRHAUL-01` cited on v8 slide 6 for LLS-C1 timing control) and `D05` (`notSlave` attribute name in `STANDARDS_EVIDENCE.md` vs. `timeTransmitterOnly` / `notTimeTransmitter` in `ITU-T G.8275.1`). Documented in `ERRATA_V8_2026-11.md`. |
| `NOT_SUPPORTED` | **3** | `S09-04` (TIMESAFE §4 covers three of four slide 9 access paths; fourth is `T-FRHAUL-02`), `S11-10` (`C2` is a 3-variant deterministic subset, not ETSI 24.2.1.2's 250,000-iteration O-DU fuzz test), and `S26-04` (`C3` 1-second phase shift was not measured because `free_running 1` was enabled). Documented in `ERRATA_V8_2026-11.md`. |
| `NOT_ACCESSIBLE` | **14** | Paywalled `IEEE Std 1588-2019` clauses (`S08-01`, `S11-09`, `S16-01`, `S20-01`, `S21-01`, `S24-01`, `S25-01`, `S26-02`, `S27-02`) and unstored secondary/outside-set documents (`D04`, `D06`, `D10`, `D11`, `D17`). |
| **Total Audited Rows** | **82** | All 82 rows accounted for across slides and `STANDARDS_EVIDENCE.md`. |

---

## 4. Why Experiment "3b" (Clock-Steering Trial) Was Not Run

- **Status:** **NOT RUN** (documented in `IMPACT_EVIDENCE_SCOPE.md`).
- **Reason:** The local host environment is native Microsoft Windows (`Windows_NT`), which does not provide Linux network namespaces (`ip netns`), Linux Ethernet bridges (`ip link add type bridge`), `nftables`/`tc`, or the six-daemon `linuxptp 4.0` (`ptp4l`/`pmc`) runtime required to execute the G.8275.1 S-plane testbed with `free_running 0`. Per project integrity rules, no clock-steering numbers were simulated, extrapolated, or invented.

---

## 5. Verification Script Results

Both automated verification scripts were executed after regenerating `REVIEWER_ANSWERS_2026-11.pdf` via `python build_reviewer_answers_pdf.py`:

1. **`python verify_citation_quotes.py`:**
   ```text
   CONFIRMED citations checked: 63
   Stored source files searched: 18
   Mismatches: 0
   ```
2. **`python verify_reviewer_answers.py`:**
   ```text
   Campaign/source checks: 31
   Workbook agreement checks: 5
   Reviewer section checks: 48
   Citation verdict counts: {'CONFIRMED': 63, 'WRONG_CLAUSE': 2, 'NOT_SUPPORTED': 3, 'NOT_ACCESSIBLE': 14}
   Mismatches: 0
   ```

---

## 6. Independent Check Counts (`INDEPENDENT_CHECK_2026-11.md`)

All **105 factual sentences** in `REVIEWER_ANSWERS_2026-11.md` (covering the preamble, `Q1`–`Q16` body/Evidence/Limits, and the Superseded delivery-status section) were audited sentence by sentence against the cited files and stored standards:

| Verdict | Before Fix | After Fix |
|---|---:|---:|
| `SUPPORTED` | 101 | **105** |
| `OVERSTATED` | 4 | **0** |
| `UNSUPPORTED` | 0 | **0** |
| **Total** | **105** | **105** |

The four `OVERSTATED` sentences (`S33`, `S45`, `S80`, `S100`) were tightened in `REVIEWER_ANSWERS_2026-11.md` to specify that `dataset/DATASET_MANIFEST.csv` resides in the unversioned main workspace (recorded in `SESSION_RECORD_2026-10-03.md` §2 and `V8_SLIDE_SOURCE_MAP.md`), that `run/*` campaign scripts are packaged inside `splane_campaign_CORRECTED_2026-09-20.tgz` and `03_RECOVERY_LOOP_S-PLANE/code/FROZEN_RL.json`, and to quote the exact verbatim strings from v8 slide 38 (`“closed-loop healing not validated”`, `“None in the 168-run campaign”`, and `“No MTTR, recovery-time, availability or downtime figure was measured on this testbed”`).

---

## 7. Remaining Technical and Evidentiary Limitations

1. **No physical clock steering (`free_running 1`):** Both the 168-run classification campaign and the 140-run recovery-loop evaluation ran `ptp4l` with `free_running 1` and software timestamping on one host. All measured impact and recovery metrics quantify **protocol-level parent/grandmaster health and time-properties state**, not physical nanosecond time error (`|TE| > 1.5 µs` or `TAE > 65/130/260 ns`).
2. **No RF, O-DU/O-RU hardware, or UE service layer:** The testbed emulates the LLS-C3 S-plane timing path across Linux namespaces and bridges; it does not run Low-PHY/High-PHY/MAC/RLC, C/U-plane traffic, RF transmission, or 5G Core/UE attach. Service-level failure modes (such as O-RU software crash or cell drop) are cited strictly as external reference findings from `TIMESAFE` and `ETSI TR 104 106`.
3. **Paywalled `IEEE Std 1588-2019` clauses (`NOT_ACCESSIBLE`):** Nine deck citations to specific `IEEE Std 1588-2019` clauses (such as `§8.2.4` and `§9.4`) remain marked `NOT_ACCESSIBLE` until checked against a licensed copy of `IEEE Std 1588-2019`.
4. **Recovery-loop hypothesis `H3` failure and sample size:** In the 140-run recovery-loop evaluation (`5` replicates × `14` scenarios × `2` arms), `H1`, `H2`, and `H4` passed, but `H3` (zero disruptive actions on benign scenarios) failed because `1/25` benign loop runs (`B3_pdv_congestion` replicate `r17`) triggered `ACTIVATE_STANDBY_BC` during a genuine 16.5-second Announce-timeout outage (`RESULTS_2026-10-05.md` §4).
5. **Known rule limitation on `B_bc_replacement`:** In the 168-run classification campaign, the frozen rule (`v2`/`v3`) misclassified `12/12` `B_bc_replacement` runs as `ATTACK` (`A8`) because the base rule's rogue-BC clause read only `expected_bc_identity` rather than `expected_bc_identity_secondary` (`020000fffe0000b1`), lowering macro benign specificity to `0.7833` (`47/60`, or `47/48 = 0.9792` excluding `B_bc_replacement`).
6. **Reactive rather than predictive loop:** The implemented self-healing loop is reactive (triggered after packet-level attack evidence or a continuous 5.0-second timing outage) supported by preventive provisioning; it does not forecast attacks before their first packet or implement B6 oscillator-drift prediction.
