# Independent audit of `webapp-sim` (2026-10-06)

> **Final follow-up (`webapp-sim-final`, 2026-10-06):** all 111 sentences are VERIFIED and renderable; none remains SOURCE_NEEDED. Primary-source checking records 31 CONFIRMED, 0 CONFLICTS and 4 NOT_ACCESSIBLE external-standard claims. The four previously hidden sentences were restored only after confirmation in official ETSI/O-RAN publications. The `stepsRemoved` ambiguity was resolved from 555,335 decoded Announce packets; see [`STEPS_REMOVED_FINDING.md`](STEPS_REMOVED_FINDING.md). This note supersedes the historical unresolved counts below while preserving the original audit trail.

## Scope and method

- **Basis.** This audit judged only files, commands and the running app. It did not rely on the builder's reasoning.
- **Commit audited.** `2e1fda8` (the head of `webapp-sim` when the audit started).
- **Content citations.** Three independent auditor passes, each run by a subagent that had no access to this chat:
  1. **Pass 1:** every sentence (98) against its cited source.
  2. **Pass 2:** the 43 sentences that were rewritten or added after pass 1.
  3. **Pass 3:** the 14 that were rewritten again after pass 2.
- **Raw data.** A separate checker, `scripts/audit/independent_*`, reads the raw run archive and the rendered DOM. It imports none of the app's code or the builder's fidelity script.
- **Branches.** No other branch was touched.

## Verdicts

| Area | Verdict | Notes |
|---|---|---|
| 1. Fresh clone → `docker compose up --build` → http://localhost:3000 | **pass** | Clone from GitHub at `2e1fda8`, empty DB volume. Ingest checks passed (140 runs, 52,080 samples, 12,055 events, 168 campaign runs + 1,451,909 frames, 40 pilot, 2 B6). Home served the diagram. |
| 1. Test suite at `2e1fda8` | **pass** | Typecheck and lint clean. Unit **63/63**. Playwright **23/23**. Fidelity **787 / 0 mismatches**, but only after exporting the env vars; see defect D14. |
| 2. Content citations (sentence by sentence) | **pass with fixes** | Pass 1: 63 VERIFIED, 1 WRONG_CLAUSE, **30 UNSUPPORTED**, 4 SOURCE_NEEDED. All 31 were fixed (narrowed, split, or re-cited) and re-verified. Final: **107 VERIFIED, 0 UNVERIFIED, 4 SOURCE_NEEDED (hidden)** out of 111. |
| 3. B6 contradiction | **pass with fixes** | B6 was removed from the hardware strip and is shown as measured on two laptops. The premise that the workbook field is stale is **not supported** (see §B6). |
| 4a. LLS mapping | **pass with fixes** | **C3 is the closest match. C2 is not defensible** under the quoted O-RAN WG4 definition. The UI shows "LLS-C3 · closest match (reference doc says C2/C3)". |
| 4b. M-plane sync YANG name | **unresolved (SOURCE_NEEDED, hidden)** | "o-ran-sync" is found only in project-authored files. Three attempts to confirm it from O-RAN sources failed. |
| 4c. ±1.5 µs "TDD" wording | **pass (resolved)** | No source ties ±1.5 µs to TDD. It is scoped to G.8271.1 reference point E. "TDD" belongs only to the separate 3 µs TS 38.133 limit, and the app now uses it only there. |
| 5. Independent fidelity re-check | **pass** | 20 states and **529 rendered values vs raw files, 0 mismatches**. A negative control caught 3 of 3 injected errors. |
| 6. Tier assignments | **pass with fixes** | 2 elements demoted and 4 labels narrowed. Every tier now has a source (§Tiers). |
| 7. Final re-run of all tests after fixes | **pass** | Unit **68/68**, Playwright **24/24**, fidelity **787 / 0**, independent checks **245 / 0 and 284 / 0**. The fresh-clone container result is recorded at the end. |

## Defects found and fixed

| # | Defect | Evidence | Fix |
|---|---|---|---|
| D1 | `injector.s1` and `attack-packets.s2` said A1-style spoofing ran **inside RU3's namespace**. | `run/scenarios.sh` lines 40-50: A1 runs `ip netns add rogue` with port `p-rogue`, and the loop isolates `p-rogue`, not `p-v-ru3`. | Rewritten. New `injector.s5` states where A1 actually runs (`SCEN`). A unit test now rejects any rendered sentence that puts A1 in RU3's namespace. |
| D2 | `smo-nonrt.s1` put the SMO / Non-RT RIC **above** the RICs. | v8 slide 4 figure: it sits **beside** the Near-RT RIC. | Corrected. |
| D3 | `fh-mplane.s2` called `sync_status.py` an M-plane NETCONF/YANG parser. | Its docstring: the module parses pmc / synce4l text and only names NETCONF/YANG as the production equivalent. | Corrected. |
| D4 | `bc.s1`: "radio units see stepsRemoved 1". | `topology.sh` says "RUs see stepsRemoved=2". TBREF's purpose column gives "stepsRemoved 0→1". The observer logs do not record stepsRemoved, so measured data cannot settle it. | Rewritten to quote TBREF only. The conflict is recorded under limits. |
| D5 | Qualifiers dropped: `o-ru.s4` (FR2), `air-interface.s2` (TDD). | V5DIS item 5; v8 slide 12. | Restored. |
| D6 | `fh-splane.s3` attributed the 1100 ns point-C figure to V5LOG item 32. | 1100 ns is on v8 slide 7, not in item 32. | Split. New `fh-splane.s5` cites v8 slide 7. |
| D7 | The remaining 22 pass-1 UNSUPPORTED sentences (30 minus the 8 in D1–D6) each added an inference or detail that their cited source does not contain. | pass-1 entries in `docs/audit/content_audit_pass1.json`. | Each was narrowed to the quoted text, or split so that every part has its own source. |
| D8 | `osc-drift.s2` cited the run-2 report for run-1 figures. | Run 1 is in `DRIFT_REPORT.md`. | Re-cited (new source `B6R1`). |
| D9 | B6 was shown as **"requires hardware, not measured"** while being shown elsewhere as measured. | B6 record; `DRIFT_REPORT_run2.md:64` "Software timestamping over NTP/WiFi". | See §B6. |
| D10 | GM-A was labelled **"PRTC/T-GM"**. | TBREF §3: "the lab has no PRTC/GPS so every node truthfully advertises clockClass 248". TBREF §4 calls gma a T-GM. | Name and diagram label changed to T-GM. New `gm-a.s5`. |
| D11 | The tier-1 S-plane was labelled "PTP / SyncE". | v8 slide 16: "The testbed exercised PTP only; SyncE … was not implemented." | Renamed "S-plane (PTP)" / "Open Fronthaul S-plane (PTP in the testbed)". SyncE stays a tier-2 element. |
| D12 | The O-RU was presented as an O-RU. | TBREF §4: "O-RU proxies (T-TSC)". | Renamed "O-RU proxies". The sub-label "telecom time slave" was replaced by "ptp4l clients", per the cfg files. |
| D13 | LLS-C3 was labelled "the testbed's configuration", and the disagreement was left "unresolved". | §LLS below. | LLS-C3 now reads "closest match (reference doc says C2/C3)", with reasons in `lls-c2.s3` and `lls-c3.s4`. |
| D14 | `scripts/fidelity.ts` failed in a fresh clone (`Environment variable not found: DATABASE_URL`) when `.env` was created after `npm ci`. | Reproduced in the fresh clone. | The script now loads `.env` itself (`process.loadEnvFile`). Re-run in the fresh clone without exported env: 787 / 0. |
| D15 | Citation links to the app's own files (e.g. `04_WEB_SIMULATOR/ingest/extract.py`) pointed at the snapshot branch, where they do not exist. | `git cat-file -e` against `full-project-2026-10-05`. | `referenceUrl` now sends `04_WEB_SIMULATOR/` paths to `webapp-sim`. A unit test checks that every cited repo path exists. |
| D16 | The validator rejected any VERIFIED status. The footer said every sentence was "marked UNVERIFIED". | `src/lib/architecture.ts`. | VERIFIED is now allowed only with an auditor's verbatim quote, location and attribution (`verification`), and the validator enforces it. The footer shows live counts. |
| D17 | Tier 1 was given to `hw-faults` (not built or measured) and `ds-raw-missing` (absent data). | Tier rule: tier 1 means built and measured. | Both demoted to tier 2 and logged in `tier_log`. |
| D18 | The SMO role read "where a closed loop like ours **maps** in O-RAN". No source makes that mapping (pass 1, `smo-nonrt.s3`). | | Reworded as "Project framing: where a closed loop like ours would sit in O-RAN; not implemented there." The brief requires this label, so it is kept but marked as framing, not as a sourced claim. |

**Process defect caught during the audit.** The audit's own fix script once gave two sentences the same citation object. That silently copied VERIFIED onto `lls-c3.s4` without its quote. The new validator rule caught it (unit test failed). The script now copies the object; the final file has a quote for every VERIFIED sentence.

**Checked and found correct (no change):**
- Every `rule=` in an action reason matches the preceding eval hint (82 / 82 raw records).
- The extractor relabels flooder and unknown-MAC frames as `injector`, and no stray sender key reaches the app.
- All measured figures the auditor recomputed from EVALUATION_V4, EVALUATION_RL, S11 and the B6 reports match.

## §B6 — the premise of task 3, tested

The **app's** label "requires hardware, not measured" was wrong for B6. B6's physical premise was measured on two laptops:

- **run1:** +20.161 ppm, NOT ESTABLISHED;
- **run2:** +21.013 ppm, ESTABLISHED;
- method: software timestamping over NTP/WiFi (`DRIFT_REPORT_run2.md:64`).

The fix:

- B6 is removed from the hardware list.
- A separate line reads "B6 · Oscillator drift / thermal: measured on two laptops (software timestamping): run1 not established; run2 established". The run labels are read from the database.
- The line also states the scope: "Physical premise only (relative crystal offset between the laptops); not an end-to-end detection test on the testbed."
- The e2e test `B6 is shown as measured on two laptops, not in the hardware-only list` covers this.

The workbook field `testbedRequired = HARDWARE required` is **not stale** according to the B6 record. `B6_MEASUREMENT_RECORD_2026-10-02.md` §7 says:

- item 1: "Not an end-to-end B6 detection test. No PTP ran between the two machines, so the detector never saw this drift. This measures B6's physical premise";
- the closing note: "`ORAN_Fault_Detectability_v2026-09-29.xlsx` row B6 is **not** changed by this run. That row describes detectability on the software testbed, which is unaffected."

So the field describes testbed detection, and that is still hardware-bound. The source workbook was not altered. These points are now content sentences `osc-drift.s4`, `osc-drift.s5` and `hw-faults.s3` (all VERIFIED).

## §LLS, YANG, TDD

- **LLS.** The definitions are O-RAN.WG4.CUS.0 v06.00 as quoted on v8 slide 6 (via Armstrong, ATIS WSTS 2023). This is a secondary source; the specification itself was not reachable.
  - LLS-C1 and LLS-C2: "O-DU is part of the synchronization chain".
  - LLS-C3: "O-DU is not part of the synchronization chain. Timing is distributed from PRTC/T-GM to O-RU".
  - The testbed is GM → T-BC → O-RU proxies with **no O-DU** (TBREF §4 topology; cfg files; v8 slide 6: "The O-DU itself is not emulated").
  - So **C2 is not defensible**, and TBREF §4's "models O-RAN LLS-C2/C3" overstates the match.
  - C3 matches the structure but not exactly, because there is no PRTC (TBREF §3). Hence the label "closest match (reference doc says C2/C3)".
- **M-plane YANG name.** Not confirmed. `fh-mplane.s4` remains SOURCE_NEEDED and hidden.
- **TDD.** Resolved, as in the verdict table. No app text pairs ±1.5 µs with TDD.

## §Tiers (every assignment, with source)

| Tier | Elements | Source |
|---|---|---|
| 1 (built and measured) | gm-a, gm-b, bc, o-ru (proxies) | TBREF §4 node table |
| 1 | bc-standby | `provisioning.json` `standby_bc_identity`, port `p-bcs-dn` |
| 1 | fh-splane, PTP only | v8 slide 16 |
| 1 | injector | Guide ch.7 caption; `scenarios.sh` |
| 1 | ptp-exchange, bmca-contest, attack-packets, port-counts | `cfg/*.cfg`; run archive; RESULTS |
| 1 | loop-* and recovery-loop | DESIGN; PREREG §3; EVALUATION_RL.json |
| 1 | ds-recovery, ds-campaign, ds-pilot | EVALUATION_RL; EVALUATION_V4; S11 / S15 evaluations |
| 2 (context, not built) | o-du | v8 slide 6 "not emulated" |
| 2 | fh-mplane | RESULTS §4 (pmc only) |
| 2 | smo-nonrt | survey (context); framing as above |
| 2 | gnss-time | v8 slide 18 "No GNSS receiver" |
| 2 | synce | v8 slide 16 |
| 2 | osc-drift | B6 measured off the testbed |
| 2 | lls-c1 … c4 | v8 slide 6 definitions |
| 2 | hw-faults | **demoted from 1** |
| 2 | ds-raw-missing | **demoted from 1** |
| 3 (consequence only) | fh-cplane, fh-uplane, air-interface, ue | v8 slide 6 (no O-DU); v8 slide 12 "Measured impact is protocol-level" |
| dimmed (outside the project) | near-rt-ric, o-cu, core-5g, o-cloud | TBREF §4 node table lists only gma, gmb, bc, ru1-3; Guide p.20: S-plane "highlighted as our scope" |

A unit test pins the tier-1 set on the level-1 diagram to `bc, fh-splane, gm-a, gm-b, injector, o-ru`.

## Citation counts

| | Sentences | VERIFIED | UNVERIFIED | WRONG_CLAUSE | UNSUPPORTED | SOURCE_NEEDED |
|---|---|---|---|---|---|---|
| Before (builder's file) | 98 | 0 | 94 | – | – | 4 |
| Audit pass 1 verdicts | 98 | 63 | – | 1 | 30 | 4 |
| Pass 2 (43 rewritten or added) | 43 | 30 | – | 3 | 10 | 0 |
| Pass 3 (14 re-fixed) | 14 | 14 | – | 0 | 0 | 0 |
| **After** | **111** | **107** | **0** | 0 | 0 | **4 (hidden)** |

- **SOURCE_NEEDED (hidden):**
  - `o-du.s5`: O-DU clock type in LLS-C1/C2;
  - `fh-mplane.s4`: the o-ran-sync YANG name;
  - `fh-cplane.s3` and `fh-uplane.s3`: C/U-plane behaviour under timing loss.
- **Sources:** 28 → 33. Added: SCEN `scenarios.sh`, B6R1, B6REC, APPX `ingest/extract.py`, RUNS (run archive).
- **Sentence kinds after:** REFERENCE 38, CONFIGURED 34, MEASURED 22, UNKNOWN 17.

### Reproducing the content changes

Run the fix script on the pre-audit content (commit `2e1fda8`):

```
git show 2e1fda8:04_WEB_SIMULATOR/content/architecture.json > content/architecture.json
python3 ingest/audit_content_fixes.py docs/audit/content_audit_pass1.json docs/audit/content_audit_pass2.json docs/audit/content_audit_pass3.json
# -> {"VERIFIED": 107, "SOURCE_NEEDED": 4}
```

Every change is listed in `content/architecture.json` → `audit_log`. The auditors' verbatim quotes are stored per sentence under `verification`, and shown as the citation chip's tooltip.

## Independent fidelity re-check (task 5)

The checker is in `scripts/audit/`:

1. `independent_expected.py` derives the expected state from the **raw** `observer.jsonl`, `loop.jsonl` and `timeline.json` in `03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz`.
2. `independent_rendered.cjs` reads the **rendered DOM** at the matching deep links (levels 3 and 4), using only Playwright.
3. `independent_compare.py` compares the two.

| Batch | Seed | States | Values | Mismatches |
|---|---|---|---|---|
| Random (as asked) | 20261006 | 10 | 245 | **0** |
| Stratified supplement | 20261007 | 10 (states after a logged action) | 284 | **0** |

- **Values compared per state:**
  - replay time;
  - RU1-RU3 port state and `parentPortIdentity`;
  - rule verdict and hint;
  - logged act / would_act / verify / escalate times;
  - all six loop stages (lit, time, never-in-run).
- **Why a second batch.** Only 1 of the 10 random states contained an executed action, so the stratified batch was added to cover actions.
- **Negative control.** Three expectations were deliberately corrupted (a port state, a verdict, an escalate time shifted by 1 ms). All 3 were reported as mismatches.
- **attack-packets.s4.** A separate auditor counted the pcaps with its own parser (passes 2 and 3).
  - 30 / 30 loop isolations had 0 attacker frames from 1 s after the act.
  - Control runs had 220–79,597 frames.
  - A3 uses only provisioned MACs.
  - The app's extractor-based count (216–78,218) differs because of time alignment and window, so the sentence states only what both counts support: "more than 200".

## Remaining limits

- **External standards were not opened.** ETSI, ITU, O-RAN, ATIS and RFC pages were blocked by the egress policy. VERIFIED therefore means "verified against the cited repository document". Definitions such as LLS and G.8271.1 are verified **as quoted by** project documents, not against the standards themselves.
- **VERIFIED was assigned by independent AI auditor passes, not by a person.** Each carries a verbatim quote, so a person can check it quickly.
- **The stepsRemoved conflict is unresolved.** `topology.sh` says RUs see 2; `provisioning.json` expects 1; TBREF says "0→1". The recorded observer data does not include the field. The content quotes only TBREF.
- **The independent check covers 20 states.** Per-bin packet counts were not re-derived from the pcaps for those states; only the aggregate attack-frame claim was recounted from pcaps.
- **Text outside `architecture.json` is not cited.** This covers UI instructions and a few labels, e.g. "T-TSC (ptp4l clients)" (from the cfg files) and the SMO "project framing" label.
- **Carried over from `SIM_HANDOFF.md`:**
  - the B6 ppm 17th-digit storage artifact;
  - Lighthouse was not run;
  - browser back/forward has no e2e test;
  - the deep-link time resolution is 0.1 s.

## Final verification: fresh clone of commit `1160cfd`

The clone came from GitHub, with an empty DB volume, and was built with `docker compose up --build`. All checks below ran against that container.

| Check | Result |
|---|---|
| Ingest | runs=140, samples=52080, events=12055, campaign=168 (1,451,909 frames), pilot 40, B6 2: "row counts match the source files" |
| Home page | `http://localhost:3000/` returned 200 and rendered the diagram. The footer shows 107 VERIFIED. |
| `npm ci`; typecheck; `eslint . --max-warnings 0` | clean |
| Unit tests | **68 / 68** |
| Playwright | **24 / 24** |
| Fidelity | **787 values, 0 mismatches**. `.env` was created after `npm ci` with no exported env, which confirms the D14 fix. |
| Independent raw-file check | **245 / 0** (random, seed 20261006) and **284 / 0** (stratified, seed 20261007) |
