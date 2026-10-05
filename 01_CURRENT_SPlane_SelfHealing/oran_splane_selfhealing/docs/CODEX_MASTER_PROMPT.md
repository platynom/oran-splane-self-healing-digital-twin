# Codex Master Prompt — AUTONOMOUS mode (no human relay)

You are working in the repo `oran-splane-self-healing-digital-twin`. There is **no human in the loop**.
You coordinate with an automated **Reviewer** ONLY through files in
`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/evasion_handoff/`. Read
`evasion_handoff/PROTOCOL.md` first — it is the contract.

**How each "STOP" below works in autonomous mode:** when a step says STOP, you instead:
1. Write your evidence to `evasion_handoff/reports/codex_step_<N>.md` (contents per PROTOCOL.md).
2. Set `evasion_handoff/STATE.json` to `status:"AWAITING_REVIEW"`, `last_updated_by:"codex"`.
3. **Poll `STATE.json` every few minutes.** When the Reviewer sets:
   - `APPROVED` -> set `current_step=N+1`, `status:"PENDING_CODEX"`, and do the next step.
   - `CHANGES_REQUESTED` -> read `evasion_handoff/reviews/review_step_<N>.md`, fix, overwrite your
     report, set `AWAITING_REVIEW` again.
   - `BLOCKED_NEEDS_HUMAN` or `DONE` -> halt and wait; do nothing further.
Do exactly one STEP at a time. Never skip the report/poll cycle.

Two committed design docs are your full specification — read them before Step 1:
- `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/EVASION_MODULE_DESIGN.md` (the research design)
- `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/CODEX_BRIEF_evasion_phase0.md` (build rules)

Work inside `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/` for all commands.

## GLOBAL RULES (apply to every step)
1. **Never modify or delete existing committed code** in `discriminator/`, `healing/`, `telemetry/`,
   `ingest/`, `twin/`, `faults/`, `fronthaul_sim/`, `stats/`, `benchmark/`. Only import from them.
   All new code goes in a new `evasion/` package and new `scripts/`.
2. **All build work happens on the branch `evasion-module`.** `main` must never be modified by you.
   To undo everything, the human checks out `main` and deletes the branch. **Never run `git reset
   --hard`, and never reset to any old tag** — there are commits and files that a reset would destroy.
3. **After every step run `python scripts/audit_state.py` and paste its FULL output.** Never edit the
   audit script to make it pass. Never tune a detector or weaken a test to improve a number.
4. **The 56 existing tests must keep passing** (`python -m pytest tests -q`). Add tests for new code.
5. Keep everything CPU-runnable; if the transformer (Step 2) needs a GPU, gate it behind a flag so the
   rest still runs CPU-only, and say so.
6. Distinguish clearly in all output: simulator numbers vs real-capture numbers vs live numbers.
   Citations, if you write any, must be peer-reviewed (see `docs/reference_papers/README.md`).

---

### STEP 0 — Back up the current state (git housekeeping)
The human has already committed the latest work on `main` and created the restore tag
`known-good-2026-08-16` locally. Your job here is only to push and branch.

```
cd "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/.."   # repo root
git status                       # confirm working tree is clean; if NOT clean, STOP and report
git push origin main --follow-tags
git checkout main
git checkout -b evasion-module
git branch --show-current        # must print: evasion-module
```
**STOP.** Report to the human: (a) `git status` output, (b) confirmation the push succeeded and the
tag `known-good-2026-08-16` is on GitHub, (c) that the current branch is `evasion-module`.
Wait for "continue".

---

### STEP 1 — Phase 0 gate: reproduce the victim detector
Goal: build a TIMESAFE-class detector and show it reaches ~99% on the public captures, so a later
"we evaded a strong detector" claim is credible. Full detail: DESIGN doc §5 (victim), CODEX_BRIEF Phase 0.

- Create `evasion/victim_transformer.py`: small Transformer-encoder over PTP packet-sequence features
  (per packet: direction, length, PTP sequence ID, message type, inter-arrival; sliding window, stride 2).
- Train/evaluate on `data/external/timesafe_sessions/*.csv` and the pcaps in
  `data/external/s-plane_security_repo/DataCollectionPTP/`, using session-level splits
  (`GroupShuffleSplit` on session id — attacker and victim never share a session).
- Also wire our own pipeline (`discriminator/model.py` + `discriminator/openset.py`) as victim #1 by
  importing it — do not modify it.
- Write `results/evasion/victim_repro.csv` (accuracy + confusion matrix per victim) and
  `docs/EVASION_PHASE0_NOTES.md` with the numbers and the gate decision.
- Run tests + `python scripts/audit_state.py`.

**GATE:** if the transformer does NOT reach roughly the published ~99% on announce/sync captures, do
not proceed — report the numbers and stop for a decision (fallback: attack only our own pipeline).
**STOP.** Report: victim accuracy/confusion per detector, the gate decision, test result, audit output.
Wait for "continue".

---

### STEP 2 — Phase 1: attack harness + pilot on Replay
Detail: DESIGN §3, §5, §9 Phase 1.
- Create `evasion/harness.py`: an attack encoder that edits *attack parameters* (Announce field values,
  injection cadence, magnitude ramp) so every candidate decodes to a realizable PTP sequence. Measure
  effectiveness by replaying through existing `ingest/` + simulator and reading the resulting offset.
- Pilot on the **replay** family only (simplest) to validate the loop end to end.
- Tests + audit.
**STOP.** Report: proof the harness produces realizable attacks whose effectiveness (ns of offset) is
measurable; one worked example; audit output. Wait for "continue".

---

### STEP 3 — Phase 2: perturbation evasion on Announce (the main result)
Detail: DESIGN §3A, §5, §6.
- Create `evasion/optimizer.py`: gradient-free search (evolutionary or Bayesian) maximising stealth
  (1 − detector score) subject to effectiveness ≥ 100 ns. Run against BOTH victims, grey-box then
  black-box (surrogate trained on different sessions).
- Produce the effectiveness-vs-stealth **Pareto fronts** → `results/evasion/pareto_*.csv`.
- Tests + audit.
**STOP.** Report: the Pareto fronts (paste the CSV summary), whether evasion succeeded (branch A-succeeds
vs A-fails per DESIGN §6), audit output. Wait for "continue".

---

### STEP 4 — Phase 3: telemetry-suppression evasion + fail-closed defence
Detail: DESIGN §3B, §6 defence half.
- Create `evasion/suppression.py`: the availability-based evasion (suppress telemetry so the monitor
  consumes stale/last-known values). Run the existing fail-closed gate (`healing/loop.py`) against it.
- Expected: suppression evades the feature detector but is caught by fail-closed → `safe_default`.
- Tests + audit.
**STOP.** Report: does suppression evade the feature detector? does fail-closed catch it? audit output.
Wait for "continue".

---

### STEP 5 — Phase 4: retraining-robustness + write-up
Detail: DESIGN §6 (retraining test), §9 Phase 4.
- Continuously re-train the detector and re-measure the Step-3 evasion (engages the "retraining defeats
  evasion" critique). Suppression (Step 4) should be unaffected — that is the point.
- Summarise results for both outcomes into `docs/EVASION_RESULTS.md`.
- Final tests + audit.
**STOP.** Report: retraining effect on evasion, final summary, audit output. Wait for "continue".

---

When all steps are done and the human approves, they will merge `evasion-module` into `main` and tag a
new restore point. Do not merge yourself.
