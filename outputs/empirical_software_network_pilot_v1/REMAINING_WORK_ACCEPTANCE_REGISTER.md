# Remaining software-evidence acceptance register

The historical version is preserved in [documentation_correction_archive_20260913T225000Z](documentation_correction_archive_20260913T225000Z/MANIFEST.md). This register governs future interpretation; it does not retrofit acceptance criteria onto S14 data already being collected.

## Required evidence separation

| Record type | Required wording and handling |
|---|---|
| Configured condition | Retain the harness value and expected-condition label. Treat it as configuration evidence only, never as ground truth of harm or packet behavior. |
| Packet observation | State the computed packet statistic and acquisition source. The S14 detector uses eight matched Sync/Follow_Up arrival-gap samples per block and two high, disjoint blocks within three seconds. It does not require consecutive blocks, eight packets, or exactly one second. |
| Independently measured pre-action impact | Retain receiver/interface evidence that precedes the action and has a verified timing relation and provenance. Without this, impact is not established. |
| Action | Retain the command record and direct command effect. A commanded `FAULTY` state is an action effect, not evidence of original harm. |
| Outcome | Retain post-action receiver or traffic evidence. Describe it as an outcome unless an independently specified prospective comparison supports causation. |

`160 us` is a provisional engineering detector threshold, not a validated harm boundary. Chosen rate envelopes are unvalidated testbed settings, not norms. No source identity, domain setting, or authority is accepted without run-specific verification evidence.

## Interpretation status

For the existing S14 material, every `expected_classification` or condition label is a raw expected-condition label. It is not a ground-truth `BENIGN` or `HARMFUL` label. Harmfulness is `UNKNOWN` unless independent pre-action impact evidence supports the relevant claim. A packet trigger alone cannot make the classification harmful.

Do not add numerical decision criteria, sensitivity/specificity targets, or recovery thresholds after the run to judge that run. Future independent validation requires a protocol that fixes its labels, independent pre-action measures, timing alignment, analysis plan, and acceptance rules before collection.

## Acceptance register (SUPERSEDED HISTORY — retained for audit, not current status)

> **This table records the status as claimed on the day the S14 batch was evaluated. It is retained
> unaltered except for the R6 correction noted in its own row. It is NOT the current status.**
> **The current status of every milestone is the later table under "Current status".**

| Milestone | Required evidence | Status as claimed at the time |
|---|---|---|
| R1: Evidence taxonomy | Explicit separation of 4 classification layers (configured condition, observed anomaly, receiver impact, policy classification). | Defined in `REMAINING_WORK_ACCEPTANCE_REGISTER.md` and applied across all S14 analyses. |
| R2: Detector/impact policy | Threshold and detector mechanics described accurately; approved sources and measurable software impacts defined. | Defined in `ACCEPTABLE_BEHAVIOR_AND_IMPACT_POLICY.md`. Boundaries maintained (`free_running 1`). |
| R3: S14 frozen protocol | Frozen protocol with cryptographic hashes of all runner, detector, sealer, and evaluator files. | Frozen in `S14_BROADER_EXPERIMENT_PROTOCOL.json`. |
| R4: Runner integrity | Per-run sealed evidence checked after writers stop; FIFO drained gracefully; no post-seal appending. | Validated in `s14_smoke_run/trial/`. All 7 writers exited with 0 in `writer_exit_status.tsv`; 0 post-seal append lines. |
| R5: Experiment execution | Independent 25-run batch across 5 conditions with interleaved execution. | Executed into `s14_runs/`. All 25 runs completed and sealed with 0 exit code. |
| R6: Independent validation | Evaluation of classification specificity/sensitivity and recovery against matched controls. | **WITHDRAWN — this row was wrong when written.** It cited `S14_BROADER_EXPERIMENT_EVALUATION.json` figures (specificity 15/15, sensitivity 10/10; failover 5/5 action vs 0/5 control). Those figures are S14 numbers and S14 is the development data from which the receiver statistic and its boundary were derived, so they cannot serve as independent validation. The S14 numbers themselves are not retracted; only the claim that they constitute independent validation is. Current status: see R6 in the "Current status" table. |
| R7: Delivery | Full dataset export and streamed multi-sheet workbook with lossless CSV sources. | Generated in `s14_dataset/S14_empirical_full_packet_streamed.xlsx` (232,403 packets, 168 runs) and reconciled in `s14_full_detail_reconciliation.json`. Entrypoint updated in `START_HERE_FINAL.md`. |

## Scope limits

The available evidence is limited to a software testbed. It does not establish physical timing accuracy, hardware conformance, attack attribution, or a complete O-RAN digital-twin result.

---

## Current status — authoritative

This table supersedes every earlier status statement in this file and in any other document. Where
they disagree, this table governs. Last revised 2026-09-13 after the S15 protocol was superseded by v3.

| Milestone | Current status | Evidence |
|---|---|---|
| R1 Evidence taxonomy | **APPLIED** | `S14_VERIFICATION_AND_IMPACT_FINDINGS.md` keeps configuration, packet observation, independent pre-action impact, action and outcome in separate sections and separate JSON fields. |
| R2 Detector/impact policy | **APPLIED, harm boundary still not accepted** | Detector described as eight matched Sync/Follow_Up gap samples per block, two high disjoint blocks within three seconds. `160 us` recorded as provisional engineering configuration. Harmfulness remains UNKNOWN. |
| R3 S14 frozen protocol | Unchanged | Not edited. No retrospective reinterpretation. |
| Protocol deviations | **7 recorded; D6 destroyed a trial and stopped a batch** | [PROTOCOL_DEVIATION_REGISTER.md](PROTOCOL_DEVIATION_REGISTER.md). D1 reversed and guarded; D2, D4, D5 caught before any run; D3 unverifiable historical claim; **D6 data loss, my error**; D7 archive and re-issue. |
| R4 Runner integrity | **COMPLETE** | `S14_EVIDENCE_VERIFICATION.json`: batch allowed to finish, then 25/25 sealed and internally consistent, 575 manifest entries rehashed, zero problems. |
| R5 Experiment execution | **COMPLETE** | Complete inventory of 25 directories; every mandatory entry present, every run reached `phase_finished`, no `status=FAIL`, both captures decode to non-zero PTP in every run. |
| R6 Independent validation | **NOT VALIDATED. READY TO RUN: protocol v5 frozen, zero trials in `s15_runs/`.** | `S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json` governs. One command runs everything: `bash run_s15_complete.sh` (preflight, hash verification, smoke, 30-trial batch, evaluation, dataset rebuild, delivery manifest), each stage a hard gate. The aborted batch of 18:07Z is archived intact under `s15_aborted_20260913T182252Z/` and excluded structurally; see D6 and D7 in [PROTOCOL_DEVIATION_REGISTER.md](PROTOCOL_DEVIATION_REGISTER.md). No S15 agreement, sensitivity or specificity figure exists. |
| R7 Delivery | **Package current; S15 results pending** | `s14_dataset/S14_empirical_full_packet_streamed.xlsx` rebuilt 2026-09-13 with a corrected `Read me` that states the S14 figures are development-set results and that independent validation is not complete. Row counts unchanged and reconciled: 168 runs, 232,403 packets, 1,350 events, 158 decisions, 15,643 receiver-log rows, 4,033 transitions, 35 outcomes. The CSV sources were not regenerated and their hashes are unchanged. The package will be extended only after S15 data exists. |

### A receiver-computed pre-action measurement exists (v2)

`RECEIVER_DISPERSION_S14_V2.json`, produced by `measure_receiver_dispersion_v2.py`, is the current
measurement. It supersedes `S14_PRE_ACTION_IMPACT.json`, which is retained as exploratory: v1 selected
the last servo summary of a run without checking that its window lay wholly inside the intended phase.
v2 uses ptp4l's own reported path-delay dispersion, taken from the **first summary window lying wholly
inside the impaired phase**, with window semantics read from linuxptp `clock.c` and phase alignment
evidenced by five anchor pairs agreeing to within 0.93 ms. The per-condition figures below are v2
figures and are unchanged from v1 in value, because every S14 run happened to contain exactly one
wholly-in-phase window; they now rest on a demonstrated rather than an assumed alignment.
This measurement is receiver-computed rather than detector-computed, but it is **not statistically
independent** of the packet observations: both arise from the same traffic.

- Baseline vs the 200 us-jitter condition separates on dispersion without overlap, margin 24.8 us.
- **Benign (20 us jitter) vs the 200 us-jitter condition separates on dispersion, margin 8.7 us, but does NOT separate on mean path delay** — both are configured at 100 us mean delay and the receiver measures that in both.
- The `benign_delay_jitter` condition is itself a measured departure from baseline. `BENIGN_WITHIN_POLICY` is a configured expectation, not a measured boundary.
- `authorized_source_failover` is indistinguishable from baseline on both measures, so it raises no false impact signal.
- The action arm contributes no pre-action impact evidence and is excluded from it: its later servo sample straddles the commanded link-down.

This is a measured protocol degradation. It is **not** a harm label. No service requirement has been
specified in this testbed against which a path-delay dispersion could be judged harmful.

### Timebase reconciliation for previously reported S11 durations

`START_HERE_FINAL.md` states that no numeric command-to-fault or takeover duration is claimed. That
blanket statement is correct as a default and is retained. The precise position is narrower and is
recorded here so the information is neither overclaimed nor lost:

- Detection-trigger to action-execution-result was computed from two records written by the **same
  detector process clock**. It is an intra-timebase duration and is supported.
- Port-fault to standby-takeover was computed from two lines of the **same ptp4l log**. It is an
  intra-timebase duration and is supported.
- No duration was ever computed **across** the ptp4l, capture and detector clocks, and none may be,
  because no mapping between them has been recorded or verified.

