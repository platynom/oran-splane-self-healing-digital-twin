# S15 — Explicit limits and final acceptance review

Date 2026-09-13. Every line below is reconciled against an artifact in this directory.

## Step-by-step acceptance

| Step | Status | Evidence | Limit |
|---|---|---|---|
| S1 dataset inventory | COMPLETE (earlier) | `outputs/manual_dataset_combined/` | Coverage gap: a large share of repository data files were never ingested. Recorded, not closed. |
| S2 duplicate / provenance audit | COMPLETE (earlier) | criterion 6 findings, parameter provenance | Two Announce sessions are one byte-identical capture; one label set quarantined. |
| S3 combined workbook | COMPLETE (earlier) | audit records in `manual_dataset_combined` | Contains unvalidated interpretation columns; superseded for empirical claims by S13. |
| S4 TIMESAFE C0-C3 classes | COMPLETE | `LABEL_TAXONOMY.md` | Advertised-change classes only. Not health, fault, attack or recovery truth. |
| S5 isolated testbed | COMPLETE | runner, `run_environment.txt` per run | Namespaces share one host software clock. Not independent clocks. |
| S6 causal detector + first validation | COMPLETE | `V3_NONOVERLAPPING_EVALUATION.json` | n=5 per condition. |
| **S7 broader validation** | **COMPLETE** | `V4_BROADER_EVALUATION.json`, `S7_CHECKPOINT.md` | 5/5 impairment, 0/20 non-loss, 280 hashes rehashed. |
| **S8 classification decision** | **COMPLETE** | `S8_CLASSIFICATION_DECISION.md` | Cannot attribute the observation to loss: three parameters vary together. |
| **S9 live detection** | **DEPLOYED IN A LOOP** | `live_detect_and_act.py`; 7/7 causality tests | Triggered in 10/10 S11 trials; detection-to-command 6.0-21.7 ms. Frozen engine imported unchanged; only the I/O is new. |
| **S10 recovery mechanism** | **FEASIBLE ON A TWO-SEGMENT TOPOLOGY** | `spike_two_segment/S11_MECHANISM_PROBE.json` | Single-bridge dual-port fails (second port enters MASTER). Two independent bridges work: commanded port-down faults the impaired port and the standby takes over. |
| **S11 closed-loop experiments** | **COMPLETE** | `S11_CLOSED_LOOP_EVALUATION.json` | Action 5/5 receiver moved, control 0/5; detector triggered 10/10; zero command failures. n=5 per arm. |
| **S12 measured recovery benefit** | **COMPLETE** | `S12_MEASURED_OUTCOME.json` | On the receiver's active path after the trigger: action 5/5 clean, control 0/5. Nothing was repaired; the impairment stayed in place. |
| **S13 final dataset** | **COMPLETE** | `s13_dataset/` | 143 runs including V5 and S11, all evidence layers separated, no row omitted, no simulated rows. |
| **S14 reproducible package** | **COMPLETE** | `S14_REPRODUCIBLE_PACKAGE.md` | Reproduction verified for analysis steps; capture steps need WSL root. |
| **S15 final review** | **THIS DOCUMENT** | - | - |

## What is genuinely established

1. A causal, single-pass packet observation that repeated in 5/5 configured-impairment runs and 0/20
   non-impaired runs in one pre-registered batch, and 5/5 versus 0/10 in an earlier independent one.
2. The persistence requirement suppresses isolated high-dispersion blocks that do occur in controls.
3. Source silence is observable on a channel independent of the dispersion channel.
4. Full artifact integrity: every manifested input rehashed and matched before every replay.
5. A run-level dataset in which a configured condition, an observed event and a recovery outcome are
   structurally impossible to confuse.

## What is NOT established, and must never be claimed

- That the observation detects packet loss. Three parameters co-vary. V5 is frozen to resolve this.
- Any detector accuracy, generalisation, or production performance. n=5 per condition, one host.
- Any attack detection. No adversary exists in this testbed.
- Any receiver harm. No run demonstrated it.
- Any clock accuracy, GNSS, SyncE, oscillator or holdover property. Shared software clock only.
- Any recovery capability, executed or effective. No action was ever executed.
- Any O-RAN compliance. Nothing here was tested against a conformance requirement.

## Honest bottom line

Software work is finished up to the point where the architecture stops it. S7, S8, S13 and S14 are
done. S9 is ready but undeployed. S10 returned a negative result that blocks S11 and S12: the
condition this detector observes has no available remedy in a single-path topology, so a closed-loop
recovery experiment cannot be run honestly without changing the testbed.

The next two actions, in order, are external to this analysis session because both need WSL root:
run the frozen V5 batch to resolve the attribution confound, then decide between extending the
topology and re-scoping the loop to source switching.

No completion score is assigned. The table above is the status.


---

# AMENDMENT 1 — 2026-09-13, after V5, S11 and S12

Three conclusions above are superseded.

**1. Attribution.** V5 varied one netem parameter at a time: reference 0/5,
loss-only 0/5, jitter-only 3/5, delay-only 0/5,
full impairment 3/5. The observation is attributable to **configured jitter magnitude**,
not to packet loss and not to mean delay. Every earlier description of this as loss detection is wrong.

**2. Sensitivity.** The identical full-impairment condition gave 5/5 in V3, 5/5 in V4 and 3/5 in V5:
pooled 13/15, Wilson 95% [0.6212, 0.9626]. No single five-run batch may be quoted as a sensitivity
figure. Specificity is unaffected: zero false observations in 45 non-jitter runs.

**3. Recovery.** S10 is feasible on a two-segment topology, and S11/S12 are complete with a matched
control. The commanded action moved the receiver in 5/5 action runs and 0/5 controls, and the
observation was absent from the receiver's active path afterwards in 5/5 action runs against 0/5
controls. **Nothing was repaired**: the impairment remained in place for every trial and the action
only changes which segment the receiver uses.

## Still outstanding after this amendment

- **Repository-wide read coverage.** Of 651 files under `dataset/`, 45 sources are ingested;
  144 model checkpoints and 589 files under `02_PREVIOUS_Work/` have never been opened by any tool.
  `full_coverage_inventory.py` was specified but never run. This is the largest remaining software gap
  and nothing external blocks it.
- 10 criteria BLOCKED_EXTERNAL (need the TIMESAFE authors or hardware), 7 QUARANTINED,
  4 DOCUMENTED_ONLY, 2 ASSERTED_NOT_REVERIFIED, 2 BROKEN_CITATION in the dataset register.
- No physical validation of any kind. Software scope only.
