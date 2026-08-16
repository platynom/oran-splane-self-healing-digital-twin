# Codex Brief — Evasion Module, Phase 0 (and how to continue)

You (Codex) have full access to run on this machine. Build the evasion add-on described in
`docs/EVASION_MODULE_DESIGN.md`. Read that file first — it is the spec. This brief tells you exactly
what to do, in what order, and the rules you must not break.

## Non-negotiable guardrails

1. **Do not modify or delete any existing committed code.** The current pipeline is validated and
   tagged. Add new files under a new `evasion/` package and new scripts; do not edit
   `discriminator/`, `healing/`, `telemetry/`, `ingest/`, `twin/`, `faults/`, `fronthaul_sim/`.
2. **Work on a new branch — this is the primary safety net.** First thing:
   `git checkout main && git checkout -b evasion-module`. All your work stays on `evasion-module`.
   `main` must never be modified by you. To undo everything, the human simply runs
   `git checkout main` and deletes the branch — no history is lost.
   - **Do NOT run `git reset --hard` on `main`, and do NOT reset to any old tag** — there are commits
     newer than the `known-good-*` tag, and uncommitted deliverables in the tree; a hard reset would
     destroy them. Recovery is branch-based only (checkout `main`), never reset-to-tag.
   - Before you start, confirm the working tree is committed (`git status` clean). If it is not,
     STOP and tell the human to commit/back up first — do not proceed on a dirty tree.
3. **After every work session run `python scripts/audit_state.py` and paste its full output.** Do not
   report a task complete without it. Do not edit the audit script to make it pass. Commit your work
   on the `evasion-module` branch frequently so progress is never lost.
4. **Never tune a detector or weaken a test to make a number look better.** Report every deviation.
5. **Keep everything CPU-capable if possible;** if you add the transformer (Phase 0) and need a GPU,
   say so explicitly and gate it behind a flag — the rest of the repo must still run CPU-only.
6. **56 tests currently pass** (`python -m pytest tests -q`). They must still pass after your work.
   Add new tests for new code.

## Phase 0 — reproduce the victim detector (THE GATE)

Goal: build a TIMESAFE-class detector and show it reaches ~99% on the public captures, so that later
"we evaded a strong detector" is credible.

Steps:
1. `git checkout -b evasion-module`
2. Create `evasion/victim_transformer.py`: a small Transformer-encoder classifier over PTP
   packet-sequence features (per-packet: direction, packet length, PTP sequence ID, message type,
   inter-arrival time; sliding window, stride 2 — matches the TIMESAFE description in
   `docs/reference_papers` study notes). Keep it small; 2 encoder layers is enough.
3. Train/evaluate on the real captures already in the repo:
   `data/external/timesafe_sessions/*.csv` and the raw pcaps in
   `data/external/s-plane_security_repo/DataCollectionPTP/`. Use the EXISTING session-level split
   discipline (`GroupShuffleSplit` on capture/session id) — attacker and victim never share a session.
4. Report accuracy + confusion matrix. **Gate:** if it does not reach roughly the published ~99% on
   the announce/sync captures, STOP and debug the reimplementation before going further. If it cannot
   be reproduced fairly, fall back to attacking only our own RF+open-set pipeline (weaker claim, still
   valid) and flag this clearly.
5. Also wire our own pipeline (`discriminator/` + `discriminator/openset.py`) as victim #1 via its
   existing API — do not modify it, just import and call it.

Deliverable of Phase 0: `results/evasion/victim_repro.csv` (accuracy, confusion matrix per victim),
plus a short `docs/EVASION_PHASE0_NOTES.md` with the numbers and the gate decision.

## Phases 1–4 (only after Phase 0 gate passes) — see design doc §9

- Phase 1: `evasion/harness.py` — attack encoder that edits *attack parameters* (Announce field
  values, injection cadence, magnitude ramp) so every candidate is a realizable PTP sequence; measure
  effectiveness by replaying through existing `ingest/` + simulator and reading resulting offset.
  Pilot on **replay** first.
- Phase 2: `evasion/optimizer.py` — gradient-free search (evolutionary / Bayesian) maximising stealth
  subject to effectiveness ≥ 100 ns. Run on **announce/BMCA**. Produce effectiveness-vs-stealth Pareto
  fronts → `results/evasion/pareto_*.csv`.
- Phase 3: `evasion/suppression.py` — the telemetry-suppression attack; run the existing fail-closed
  gate (`healing/loop.py`) against it and confirm it routes to `safe_default`.
- Phase 4: retraining-robustness test (continuous re-train, re-measure) + both-outcomes write-up.

## What to hand back after each phase

- The new files, the results CSVs, updated tests, and the `audit_state.py` output.
- A 3-line plain-English summary: what ran, the key number, the gate decision.

## Rules for any writing/reporting
- Peer-reviewed citations only (see `docs/reference_papers/README.md`). No arXiv/thesis in references.
- Distinguish clearly: simulator numbers vs real-capture numbers vs live numbers.
