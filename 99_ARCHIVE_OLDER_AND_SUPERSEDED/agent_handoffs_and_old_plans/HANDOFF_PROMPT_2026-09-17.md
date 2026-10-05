# HANDOFF PROMPT — paste this into the new chat

You are picking up an in-progress research project. Read this whole brief before acting. Everything
below is verified fact from the prior session — do not re-derive it, but do verify anything you intend
to build on.

---

## 0 · Project

**Samsung PRISM worklet: "AI-Native Self-Healing O-RAN Network using a Digital Twin"**, scoped to
**Open Fronthaul S-plane (PTP/IEEE 1588) timing security**.

Folder on the user's machine (connected to this session):
`~/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/`

**The research question:** when a timing fault occurs on the fronthaul, is it an **ATTACK** or a
**BENIGN** (natural) fault? The user is a newcomer to this domain — explain jargon in plain terms and
do not assume background.

**Standing instruction from the user, repeated many times: NO COMPROMISE.** Never fabricate data,
never work around a limitation silently, never re-tune a rule after seeing validation results. If you
must stop, say why and stop.

---

## 1 · The novelty position (settled, do not relitigate)

- ❌ "Distinguishing faults from attacks" as a *concept* is **not novel** — it is an established
  cyber-physical-systems problem (arXiv:2510.14052; Control Engineering Practice 2024).
- ❌ "GNSS spoof vs GNSS outage in 5G timing" was **scooped in 2026** by arXiv:2607.11398
  (3GPP-integrated, Scope/Trend/Alarm classification). **Do not headline GNSS.**
- ✅ **Still open and defensible:** benign-fault vs attack discrimination across the **PTP transport
  layer** of the O-RAN fronthaul S-plane — specifically testing an assertion TIMESAFE *makes but
  never evaluates*.

**The key citation.** TIMESAFE (ACM ToPS 2025, doi:10.1145/3775060) labels its data
*"benign (0) or malicious (1) based on whether it came from an attacking machine"* — i.e. by
**provenance, not condition**. Its "benign" class is *healthy* traffic, never *faulty-but-benign*.
Verified by grep: no holdover, congestion, or planned-failover scenario appears anywhere in its
evaluation. Yet it asserts: *"legitimate changes in master clocks, changes in network topology, and
sequence number resets can often resemble malicious activity… ML models excel at… distinguishing
between benign fluctuations and actual threats."* That capability is **asserted and never tested**,
and is not in their future work. That gap is the contribution.

**The headline experiment is A1 vs B2** — rogue grandmaster vs legitimate planned failover. Both make
a new grandmaster appear; only provisioned context separates them.

---

## 2 · Complete file manifest (verified against the folder, not recalled)

All paths are relative to
`~/Documents/AI-Native Self-Healing O-RAN Network using a Digital Twin/`.

### 2.1 Created by this work — project root

| File | Size | Contents |
|---|---|---|
| `ORAN_SPlane_Master_Test_Catalogue.pdf` | 42 KB | **11 pp.** 168 catalogued test cases (60 attack, 50+ conformance, 58 benign), RUN/SPEC/IMPOSSIBLE status per case, results, standardised-constants table, honest coverage statement, O-RAN test-ID mapping, sources |
| `ORAN_SPlane_Testbed_Configuration_Reference.pdf` | ~195 KB | **7 pp.** Every config value traced to its standard; hardware limits with the command that proved each; the three declared deviations; topology; threshold provenance; measured noise floor |
| `ORAN_SPlane_Parameter_Fault_Matrix.xlsx` | 45 KB | **144 parameters × 16 faults**, ✔ (certain) / ☯ (possible) marks. Sheets: MATRIX, FAULT KEY (with testbed requirement + O-RAN threat IDs), GAP SUMMARY, SOURCES, SW TESTBED DATA AUDIT, DATA INTEGRITY FINDINGS, CHANGELOG |
| `ORAN_Fault_Detectability.xlsx` | 14 KB | Per-fault detectability: real data / real means / legitimate thresholds; software vs hardware requirement; threshold-basis sheet; what-was-built sheet |
| `ORAN_SPlane_Attack_vs_Benign_Classification.xlsx` | 23 KB | Standards-based attack/benign taxonomy. Updated 2026-09-17 with the §5 corrections. It carries no run numbers, by design. |
| `HANDOFF_PROMPT.md` | this file | Session handoff |

### 2.2 Created by this work — subfolders

| Path | Contents |
|---|---|
| `research/CATALOGUE_conformance_robustness_tests.md` | ~64 KB. Full UNH-IOL / ITU-T conformance + robustness catalogue with all test IDs, pass criteria and URLs. **Section 0 holds the standardised thresholds** that replaced invented constants |
| `research/CATALOGUE_benign_faults.md` | ~71 KB. 58 benign scenarios in 8 families + 12 documented real-world timing incidents, each with "mistakable for" and "how operators distinguish" |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/g87251_testbed.tgz` | 135 KB. **SUPERSEDED by the v2 tarball below.** Earlier working testbed — `cfg/`, `run/` (15 scripts), `results/` (FROZEN.json, NOISE_FLOOR.json, EVALUATION.json, per-run decision+context records; superseded by results_2026-09-17/ with 132 runs), `RESULTS.md`, both PDFs, both research catalogues |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results_2026-09-17/` | **CURRENT.** `g87251_testbed_v2.tgz` (the testbed used for the 132-run campaign: `cfg/`, `run/` incl. `decision_rule.py`, `randparams.py`, `conformance_neg.py`, `leak_check.py`), `EVALUATION.json`, `FROZEN.json`, `TIMESAFE_CROSSVAL.json`, `CONFORMANCE_NEG.json`, `NOISE_FLOOR.json`, `SESSION_FINDINGS.md`, `s15_full_raw_runs.tgz` (all 132 raw runs, ~35 MB) |
| `_docgen/` | Editable sources of the two PDFs (`config_ref.html`, `build_testcat_pdf.py`) and `canonical.json`, the single record of every validation number |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tools/ptp_deep_extract.py` | 9 KB. G.8275.1-aware full-surface PTP parser, 56 columns |

### 2.3 Data — reorganised by evidential legitimacy

| Path | Contents |
|---|---|
| `dataset/README.md` | **The classification rule** (abstention vs invention) + the provenance-leak warning |
| `dataset/DATASET_MANIFEST.csv` | 40 rows: source path, class, destination, reason, evidence for every moved item |
| `dataset/legitimate/` (1.5 GB) | `README.md`; `timesafe_real_hardware_captures/` (real pcaps, 7-col raw CSVs, production capture, `attack_app.py`); `netem_real_software_testbed/` (28 files from live linuxptp runs); `extracted_deep_ptp/` (**14 `.deep.csv` files, 350,794 packets, 56 columns**, plus `README.md` and `_unique_sources.json` mapping md5 → path) |
| `dataset/illegitimate/` (55 MB) | `README.md`; `synthetic_simulator_output/`; `mislabelled_duplicates_of_synthetic/`; `timesafe_derived_contaminated/`; `derived_model_artefacts/` |
| `dataset/Netem/`, `dataset/timesafe/` | ⚠️ **Now-empty leftover directories.** Deletion was not permitted in the prior session. Safe to remove. |
| `dataset/ORAN_Dataset_Encyclopedia.xlsx` | Pre-existing catalogue, not created by this work |

### 2.4 Pre-existing project files — NOT created by this work

**Exception, updated 2026-09-17:** `ORAN_Project_Walkthrough.pdf` (11 pp, plain-English, for newcomers) was brought fully up to date with the verified values. Its generator is `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/scripts/build_project_walkthrough.py`, and the August edition is kept in `_pre_2026-09-17_doc_update/`.

Do not treat these as current. Several cite results derived from synthetic-only features and from the
duplicated TIMESAFE sessions described in §3, so **they contradict the findings below and need
correcting**: `TEAM_REPORT.md` / `.pdf`, `01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md`,
`ORAN_SPlane_Technical_Report.pdf`, `ORAN_Project_Results.xlsx`,
`ORAN_Data_Provenance_Verification.pdf`, `ORAN_PRISM_Review.pptx`, `ORAN_PRISM_Presenter_Guide.pdf`,
`README.md`, `RECYCLE_MANIFEST.md`, `REORG_PLAN.md`, `SECURITY.md`.

Also pre-existing and useful: `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/team_research/Task2_Attack_Taxonomy.pdf`
and `Task3_Standards_Mapping.pdf` (the latter maps detection features to `pmc` / O-RAN YANG live sources).

## 3 · Data-integrity findings (all verified, all must be respected)

1. 🔴 `dataset/Netem/splane_telemetry.csv` was a **byte-identical copy of the synthetic simulator
   output** (md5 `46cf48c95e593b3b8b78b867bcc045df`). Now in `illegitimate/`.
2. 🔴 Mixing synthetic with real gives a **perfect provenance leak**: `offset_scaled_log_variance` is
   **4096** in every synthetic row and **65535** in every real row. One constant separates them at 100%.
   (TIMESAFE and real netem *agree* on these constants, so a TIMESAFE + real-netem join is safe.)
3. 🔴 **21 pcaps on disk are only 14 unique files.** `announce_session_1`, `announce_session_2` and
   `2024-10-06-announce_attack_UEdata` are ALL byte-identical to `15min_announce_attack`
   (md5 `5c6fd791a0ccf22a0d6cfe3031443168`). **Prior "held-session" TIMESAFE results may have tested
   on a session identical to a training one.**
4. 🟠 On real data, `synce_ql`, `freq_error_ppb`, `gnss_sync_status` are constant or absent. Therefore
   **12 of the project's 28 original features (the GNSS + oscillator-consistency groups) are
   synthetic-only and inert on real data.**
5. 🟠 `path_delay_ns` is 0.0 in 99.1% of TIMESAFE session rows despite Delay_Req/Delay_Resp being
   present in the pcap — an extraction gap, not a data gap.
6. 🟠 `gnss_available` in the derived CSVs is a **re-encoding of clockClass**, not telemetry.

---

## 4 · The profile confound (the single most important fix made)

Measured from raw bytes:

| | Real TIMESAFE captures | Old netem runs | New testbed |
|---|---|---|---|
| domain | **24** ✅ | **0** ❌ | **24** ✅ |
| logSync | **−4** (16/s) ✅ | −3 (8/s) ❌ | **−4** ✅ |
| logAnnounce | **−3** (8/s) ✅ | **+1 = one per 2 s** ❌ | **−3** ✅ |

Announce every 2000 ms (benign data) vs every 125 ms (attack data) is a **16× mismatch**. A classifier
would have separated the classes on cadence alone and learned nothing. **Consequence: all the old
netem benign data is unusable for a joined dataset.** Benign data has since been regenerated on the new testbed (the 132-run campaign, §7).

---

## 5 · Corrections issued against earlier claims — propagate these

These were wrong and are now corrected. All deliverables, including `ORAN_SPlane_Attack_vs_Benign_Classification.xlsx`, were updated with these corrections on 2026-09-17.

1. **The attacker does NOT win via `priority2` 120-vs-128.** Raw fields of
   `2024-10-16-announce_attack` (verified from the extracted CSV) show three Announce streams:
   (a) the provisioned GM `fcaf6afffe02babe`, relayed by BC `c45ab1ffff806085`: priority1 128, priority2 120, clockClass 6, stepsRemoved 2 (29,778 Announce);
   (b) `b8cef6fffe5e6afa` announcing itself: 128 / 128 / clockClass 248, stepsRemoved 0 (27,538);
   (c) **forged Announce from source `b8cef6ffff5e6afa`** (one nibble different from (b), same MAC `b8:ce:f6:5e:6a:fa`) claiming GM
   `b8cef6fffe5e6afa` with **priority1=0, priority2=0 AND clockClass=0**, stepsRemoved 2 (24,653). clockClass 0 is
   **RESERVED/illegal** per IEEE 1588-2019 Table 5. The earlier claim came from a derived CSV that had
   lost the attack packets' true field values.
2. **G.8275.1 PERMITS multiple simultaneous grandmasters** (alternate BMCA selects the nearest of
   equal quality). So grandmaster co-presence is **not** by itself illegal.
3. **`priority1` is removed from the G.8275.1 BMCA comparison** and fixed at 128 — but it is still a
   valid *anomaly* signature, since a constant that cannot legitimately change did change.

---

## 6 · The testbed (built and working)

**Environment:** the cloud container has **root, CAP_NET_ADMIN and namespaces** — verified. Install
with `apt-get install -y linuxptp iproute2 tcpdump` then extract the tarball. It does **not** need the
user's machine.

**Topology:** two bridges with a Boundary Clock between them (models O-RAN LLS-C2/C3):
```
[gma p2=100] [gmb p2=110] ── brUP ── [bc: v-bc-up | v-bc-dn] ── brDN ── [ru1] [ru2] [ru3]
```
6 namespaces. GM-B is the provisioned backup (enables B2). The BC makes `stepsRemoved` vary
(0 upstream → 1 downstream), enabling A8 and B7. Three clients give the spatial axis.

**Profile:** full G.8275.1 — domain 24, logSync −4, logAnnounce −3, priority1 128, L2 multicast
`01:1B:19:00:00:00`, `dataset_comparison G.8275.x` (the G.8275.1 alternate BMCA). PATH_TRACE is **disabled** (provenance leak).
Wire fields were verified by parsing the testbed's own capture. The BMCA setting is not visible on the wire, so it was checked against linuxptp's own `configs/G.8275.1.cfg`.

**Three declared deviations — stated, not hidden:**
1. `free_running 1` — all namespaces share one kernel clock; with the servo active GM and clients
   would fight over the *same* clock. Offsets are measured but not applied.
2. `time_stamping software` — veth reports `PTP Hardware Clock: none`. Microsecond floor.
3. `clock_class_threshold 248` — an **acceptance policy**, not a quality claim. No node is given a
   hand-set clockClass 6; hierarchy uses `priority2`, an operator field by design.

---

## 7 · Validation result (frozen-rule, session-disjoint)

| Metric | Value | 95% Wilson CI | n |
|---|---|---|---|
| Sensitivity (attack recall) | 1.000 | [0.940, 1.000] | 60 |
| Specificity — all decidable benign runs | **0.800** | [0.682, 0.882] | 60 |
| Specificity — excluding the known `B_bc_replacement` schema limitation | 1.000 | [0.926, 1.000] | 48 |
| Abstention correctness (ambiguous benign → UNKNOWN) | 1.000 | [0.757, 1.000] | 12 |
| Fault-attribution accuracy | 0.817 | [0.701, 0.894] | 60 |

**11 scenarios × 12 replicates = 132 runs** (replicates 30–41).
Attack: TP 60, FN 0, UNKNOWN 0 · decidable benign: TN 48, FP 12, UNKNOWN 0 · ambiguous benign: 12 correct abstentions, 0 over-claims, 0 false alarms.
Per-fault attribution: A1 8/12 · A2 12/12 · A3 12/12 · A5 12/12 · A8 5/12.

**Cross-domain (real TIMESAFE hardware captures, frozen rule, never trained on them):** 6 of 6 classified
ATTACK; **5 of 6 on standards/protocol rules alone** (3 by Announce-field legality, 2 by IEEE 1588 cl.11.3
sequenceId monotonicity). The one exception, `15min_announce_attack`, is a *healthy-looking spoof* —
fully conformant fields, monotonic sequence numbers — and needs the provisioned allow-list.

**Conformance-negative tests:** 7/7 pass, each firing on its own cited clause.

**Method that makes it evidence:** `run/decision_rule.py` has **no tunable parameter** — every
constant is a standard, a provisioned fact, or a structural definition. `run/freeze.sh` SHA-256 hashes
**18 artefacts** (frozen 2026-09-17T04:49:33Z); `run/verify_frozen.sh` refuses to run if any changed and
was passed before every admissible replicate. **Earlier replicates exposed defects, were used to fix them,
and are excluded from scoring.** Replicates 30–41 were produced after the final freeze with the rule
untouched. Every replicate draws fresh attacker identities, priorities, timings and burst sizes from
`run/randparams.py`, seeded by replicate number.

**⚠️ Limitations — state these whenever quoting the number:**
1. **A provisioned BC swap is misread as an attack.** The scenario provisions the replacement BC in the run's context file
   (`expected_bc_identity_secondary`), but the frozen rule reads only the single `expected_bc_identity`,
   so the legitimate replacement looks unapproved and is flagged A8. **This one scenario is all 12 false positives and the entire gap between 0.800 and 1.000.** The fix
   is a BC allow-*list*; it needs a re-freeze and a full re-run, so it was reported, not patched.
2. **Attribution (0.817) is weaker than detection (1.000).** A1→A3 (×4) and A8→A3 (×7): inserting a rogue
   master or BC re-parents downstream clients, producing *genuine* sequenceId restarts that the A3 clause
   matches first. The binary verdict was correct in all 60, but the *named* fault can be wrong.
3. **Self-authored attacks; provisioned context handed to the rule.** Narrows the claim to "detect
   unprovisioned or non-conformant clocks", not "detect attacks from traffic alone". §7's cross-domain
   result quantifies the dependence exactly: 5 of 6 real captures need no allow-list, 1 of 6 does.

*(The previous revision's headline limitation — "runs are not independent" — is now closed by
`run/randparams.py`; the CIs above are honest rather than optimistic.)*

---

## 8 · Defects found and fixed (disclosed, not hidden — keep them disclosed)

| Where | Defect | Root cause | Fix |
|---|---|---|---|
| Rep 1 | sequenceId counter keyed on the responding source for `Delay_Resp` | Protocol ignorance — IEEE 1588 cl.11.3 has `Delay_Resp` echo the **requester's** sequenceId; a master answering 3 clients produced **799 false regressions on a healthy baseline** | Key the counter on the requesting port |
| Rep 2 | Transient filter applied to off-allow-list GMs but not provisioned ones | Inconsistency — a standby GM announcing once (1 of 356) forced UNKNOWN | Apply uniformly |
| Rep 2 | Allow-list inspected only `grandmasterIdentity` | A Sync-only injector (1,800 forged Sync) never sends Announce and was **invisible** | Check every PTP source against the provisioned inventory |
| Reps 3–7 | **A8 built as a single-port self-announcing master** | **Experiment-design error** — structurally identical to A1; the same fault implemented twice, then the classifier was blamed for not separating them | Rebuilt as a genuine two-port BC that slaves upstream and relays downstream with stepsRemoved incremented |
| Reps 13, 21 | `ptp4l` starting before veth was up → empty capture | Startup race | Interface-readiness barrier + hard process cleanup + one automatic retry; infrastructure failures are discarded with disclosure, never scored |

---

## 9 · Standardised constants found in the literature survey (adopt these)

Status is checked against the **frozen** `run/decision_rule.py` (2026-09-17). "Identified" means the
standard value is known but the frozen rule does **not** use it yet; adopting it needs a re-freeze and re-run.

| Constant | Standardised value | Source | In the frozen rule? |
|---|---|---|---|
| Foreign-master qualification | **≥2 Announce within 4 announce intervals** (0.5 s at 8/s); `FOREIGN_MASTER_THRESHOLD = 2` | IEEE 1588 §9.3.2.4; linuxptp `foreign.h`; UNH PWR.c.2.3 | **Identified, not adopted.** The frozen rule still uses our own 1% transient filter (`TRANSIENT_FRACTION = 0.01`). This is the standard replacement for it. |
| Message-interval tolerance | **±30%** of stated mean at 90% confidence | IEEE 1588-2019 cl.7.7.2.1 | Identified, not adopted |
| Successive-interval cap | Successive Sync/Announce intervals **must not exceed 2× the mean** | G.8275.1 Amd.3 | **Yes**: `CADENCE_TOLERANCE = 2.0`, and the standard backs this factor |
| stepsRemoved discard | **≥255 must be discarded** | UNH PWR.c.2.4 | **Yes**, added before the freeze (NEG-3 passes) |
| alternateMasterFlag discard | Announce with alternateMasterFlag TRUE must be discarded | UNH PWR.c.2.5 | **Yes**, added before the freeze (NEG-2 passes) |
| announceReceiptTimeout | **3** → 375 ms at G.8275.1 | G.8275.1 Amd.3 | Yes, in the testbed config |
| Legal clockClass set | **{6, 7, 13, 14, 135, 140, 150, 160, 165, 248, 255}** — anything else is a conformance failure | G.8275.1 Amd.3 | Partly: the rule only checks clockClass ≥ 6 (IEEE 1588 Table 5). The full allow-set is identified, not adopted |
| Transport legality | Ethernet multicast only; **VLAN tags not allowed**; unicast prohibited | G.8275.1 | Partly: domain and multicast are checked (NEG-5, NEG-11); the VLAN and unicast checks are not |

---

## 10 · Official O-RAN test-ID mapping (use these — they beat self-invented names)

From **ETSI TS 104 105 = O-RAN.WG11.Security-Test-Specifications-R003-v07.00** (free PAS):

| O-RAN Test ID | Title | Our status |
|---|---|---|
| 11.1.5.1.1 | DoS Master Clock, LLS-C1/C2/C3 | ✅ our A5 |
| 11.1.5.1.2 | DoS Master Clock, LLS-C4 | ❌ hardware (local GNSS) |
| 11.1.5.2.1 | Impersonation of Master Clock | ✅ our A1 |
| 11.1.5.2.2 | Rogue PTP Instance | ✅ our A8 |
| 11.1.5.3.1 | Selective interception/removal of PTP packets | ❌ **not tested — buildable** |
| 11.1.5.3.2 | Delay attack on PTP packets | ⚠️ injectable, not measurable |
| 24.2.1.1 | S-Plane PTP DoS (end-to-end) | ✅ our A5 |
| 24.2.1.2 | S-Plane PTP unexpected/malformed input | ❌ **not tested — buildable** |

Threat IDs from ETSI TR 104 106: **T-SPLANE-01** (DoS on master), **T-SPLANE-02** (impersonation via
fake Announce), **T-SPLANE-03** (rogue PTP instance), **T-SPLANE-04** (selective interception/removal).

---

## 11 · Hardware boundary (settled — do not attempt to work around)

Verified by direct query, not assumption: no `/lib/modules` (so `ptp_mock`/`ptp_kvm` cannot be
loaded), no `/dev/ptp*`, and `ethtool -T` reports `PTP Hardware Clock: none` on veth.

**Permanently impossible in software:** A6 GNSS spoof, A7 GNSS jam, B1 GNSS holdover, B4 SyncE/EEC,
B6 oscillator drift. A4 delay attack is *injectable* but not *measurable* (a passive capture yields
only t1 and t4).

**What a second physical machine buys:** two crystals → **B6 becomes real**. Adding an Intel i210/i226
NIC per machine with a direct back-to-back cable adds hardware timestamping, dropping the floor from
microseconds (measured path delay ~7 µs, offset p95 ~6 µs) to tens of ns and making A4/B5 measurable. It does **not** unlock B1, B4, A6 or A7 — those need
a GNSS timing receiver or a SyncE-capable PHY. Verify any candidate NIC with `ethtool -T` before
purchase. Note: transmitting GNSS spoofing/jamming signals over the air is illegal in most
jurisdictions — legitimate work needs an RF-shielded chamber.

---

## 12 · Highest-value next work (in order)

**Done since the previous revision (2026-09-17):** per-replicate randomisation (`run/randparams.py`);
the two hard benign cases (unplanned failover → 12/12 correct UNKNOWN; BC replacement → 12/12 false
positives, schema limit); conformance negatives 7/7. Results in §7.

1. **BC allow-list in the context schema** — the direct fix for the 12 false positives. Needs a
   re-freeze and a full re-run of the 132-run campaign; it cannot be retrofitted.
2. **Fix attribution overlap** (A1→A3, A8→A3) — only in a new pre-registered rule version, never by
   re-ordering the current frozen rule.
3. **Packet removal / selective interception** (O-RAN 11.1.5.3.1) — mandated, not covered.
4. **Malformed / fuzzed input** (O-RAN 24.2.1.2) — mandated, not covered.
5. **Whole-second field abuse** — `currentUtcOffset`, `leap61`/`leap59`, traceability stripping.
   Trivial to craft, produce 1-second errors, essentially absent from the literature, and **every
   field is already collected by the extractor**.
6. **TIMESAFE-attacks + testbed-benign join** — benign data now exists on the G.8275.1-compliant
   testbed (the 132-run campaign), so the join can be attempted. Exclude `minor_version_ptp`
   (compile-time apparatus constant) and PATH_TRACE fields first.
7. **Wire the `pmc` telemetry into features** — it is logged (`run/pmc_log.sh`) but not yet used;
   it unlocks ~23 parameters including `portState` and the native replay counters, and is the
   precondition for A4.
8. **Adopt the identified standard constants** (§9): the IEEE 1588 foreign-master rule in place of the
   1% transient filter, the ±30% interval tolerance, the full clockClass allow-set, and the VLAN/unicast checks.
   Do this together with item 1 in **one** new pre-registered rule version, then re-freeze and re-run.

---

## 13 · Working rules the user expects

- **Never re-tune a rule after seeing validation results.** If a rule changes, every run produced
  under the old rule becomes development data and must be discarded. This is the exact failure that
  invalidated the project's earlier "S15" work (a boundary derived from S14 and then "validated" on
  S14).
- **Fix root causes, not symptoms.** When something fails, diagnose before patching.
- **Disclose every limitation in writing**, in the deliverable itself, not just in chat.
- **Never invent a number.** If a threshold cannot be traced to a standard, say it is structural or
  derived and say how.
- **No fabricated data, ever.** Missing sensor → empty/NaN with a flag, never a placeholder constant.
- Explain things simply — the user is new to PTP and to the statistics.
- Deliver files to the project folder, not just to chat.

---

## 14 · First actions in the new chat

1. Read `ORAN_SPlane_Master_Test_Catalogue.pdf` and `ORAN_SPlane_Testbed_Configuration_Reference.pdf`
   in the project root — they are the fastest way to full context.
2. Extract `results_2026-09-17/g87251_testbed_v2.tgz`, then read `results/RESULTS_SESSION_2026-09-17.md`, `results/SESSION_FINDINGS.md` and `run/decision_rule.py`. Take the numbers from `_docgen/canonical.json`.
3. Confirm the environment: `id -u`, `unshare -n true`, then install linuxptp.
4. Ask the user which of §12 they want first — do not assume.
