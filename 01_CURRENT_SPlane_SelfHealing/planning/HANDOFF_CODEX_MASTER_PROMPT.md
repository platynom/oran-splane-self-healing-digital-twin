# MASTER PROMPT FOR CODEX — paste this whole file as one prompt (Codex must have access to the project folder)

---

You are an autonomous senior research-software engineer. You have full read/write access to this project folder:

`C:\Users\Admin\Documents\AI-Native Self-Healing O-RAN Network using a Digital Twin`

Build the project below **end to end, A to Z, autonomously**. Do not stop to ask for confirmation. Make reasonable assumptions, record them, and keep going until every phase meets its acceptance test. Work in small commits. If something needs hardware you don't have, build the emulated/simulated equivalent and leave a clearly-labelled TODO stub — never block.

## 0. SOURCE OF TRUTH
The authoritative spec is `Project_Proposal_Fronthaul_SelfHealing.pdf` in this folder. The essential content is restated inline below so you do not need to parse the PDF, but treat the PDF as the canonical description if there is any ambiguity.

## 1. WHAT WE ARE BUILDING (restated)
An **AI-native self-healing loop for the O-RAN Open-Fronthaul Synchronization plane (S-plane)** using a **digital twin**. Timing between O-DU and O-RU uses PTP (IEEE-1588) + SyncE and must stay within a tight time-error budget (~100 ns class). A timing **spoofing attack can crash a base station in ~2 s**. Prior peer-reviewed work (TIMESAFE, ACM ToPS 2025) only **detects** attacks; it does not choose a **recovery action** and does not separate a **malicious attack** from a **benign timing fault**. We close that gap with a governed loop:

**detect sync anomaly → discriminate H0 benign-fault vs H1 attack → verify each candidate recovery action in a digital twin (does it keep time-error in budget and beat the safe default?) → commit the best action before the failure window.**

Recovery action space: sync-source failover across LLS-C1..C4 (incl. GNSS), clock holdover, isolate rogue master, reroute path, and a conservative safe-default baseline.

Contribution type (be honest in all docs): **integration + experimental validation + a released labelled dataset** — NOT a new fundamental algorithm.

## 2. ENVIRONMENT & HARD CONSTRAINTS
- Target: a normal laptop. **Must run with no special hardware** (no PTP NIC, no O-RU). Prefer WSL/Ubuntu; must also degrade to pure-Python if Linux tooling is absent.
- Timing realism tiers: **(A)** pure-Python physics simulator of the PTP/SyncE clock servo (always works, the default); **(B)** if `linuxptp` (`ptp4l`), `tc netem`, and a spare Ethernet/veth link are available, use them for higher realism; **(C)** real PTP hardware = optional, stub only.
- If reachable, you may reference the released baseline repo `github.com/genesys-neu/s-plane_security` (TIMESAFE: attack scripts, data-collection, trained detectors, pcap dataset) as a comparison/baseline and to shape realistic feature/attack definitions. If not reachable, synthesize equivalents from the physics simulator. Do not hardcode any dependency on it.
- Python 3.10+, CPU-only, deterministic (fixed seeds), config-driven (YAML), no GPU, no paid APIs, no network needed after initial setup.

## 3. TARGET CODE STRUCTURE (create under a NEW top-level dir)
```
oran_splane_selfhealing/
  README.md
  requirements.txt
  config/                 # yaml configs (scenarios, thresholds, seeds)
  fronthaul_sim/          # S-plane emulator/simulator (PTP servo, SyncE, holdover, GNSS)
  telemetry/              # feature extraction: offset, mean path delay, PDV, seq/msg-type, ESMC QL
  faults/                 # injectors: holdover, PDV, SyncE-degrade (H0) + spoof, replay (H1) with timestamped auto-labels
  discriminator/          # H0-vs-H1 model(s) + training + isolated evaluation (ROC/confusion)
  twin/                   # digital twin of the S-plane: clock-servo + holdover drift model + fidelity score + per-action forecast
  healing/               # governed loop: detect -> discriminate -> twin-verify -> commit; action space; real-time budget
  dataset/               # generated labelled datasets + datasheet
  benchmark/              # our loop vs baselines; metrics + plots + results tables
  scripts/                # run_all.py (one-command reproduction), individual phase runners
  tests/                  # pytest unit/integration tests
  results/                # PROGRESS.md, metrics tables, figures, SUMMARY.md
```

## 4. BUILD PHASES (do in order; each MUST pass its acceptance test before moving on; log to results/PROGRESS.md and git-commit after each)

**P0 — Setup + cleanup.** Create the structure above, `requirements.txt`, `README.md`, git init if absent. Do the file-cleanup in Section 5. Acceptance: folder tree exists, `pip install -r requirements.txt` succeeds, garbage organized with a manifest.

**P1 — S-plane simulator.** Physics model of a slave clock disciplined by PTP offset/path-delay with SyncE frequency aid; supports GNSS reference and holdover. Emits a time-series of sync telemetry at a fixed cadence. (Use linuxptp/netem if available; else pure-Python.) Acceptance: healthy run produces a stable time-error trace within budget; unit test checks servo convergence.

**P2 — Fault + attack injectors + dataset.** Timestamped, auto-labelled scenarios: H0 = GNSS-loss/holdover ramp, congestion PDV burst, SyncE quality-level drop; H1 = PTP spoof (forged Announce/Sync, abrupt offset step), replay (duplicate/out-of-order sequence IDs). Acceptance: a labelled dataset (CSV/Parquet) with per-window H0/H1/healthy labels + a datasheet; label integrity test passes.

**P3 — Fault-vs-attack discriminator.** Feature engineering from telemetry (offset stats, path-delay, PDV, PTP sequence/message regularity, ESMC QL). Train + evaluate a classifier with an honest train/test split. Report ROC, confusion, precision/recall. Provide a **detection-only baseline** (single "anomalous" bit) to beat. Acceptance: results table saved; discriminator beats the detection-only baseline on the held-out set; **do not fabricate perfect scores** — report real numbers.

**P4 — Digital twin.** Compact model that, given current state + a candidate recovery action, forecasts the time-error trajectory; includes a **fidelity score** (discount its advice when telemetry is degraded/out-of-sync). Acceptance: twin forecast error vs simulator is bounded on healthy data; per-action forecasts produced.

**P5 — Governed self-healing loop.** Implement detect → discriminate → twin-verify (action vs safe-default) → commit, with the action space, an auditable reason per decision, and a real-time budget check (must decide well inside the ~2 s window). Acceptance: on injected scenarios the loop commits a recovery that restores time-error within budget in the simulator; integration test passes.

**P6 — Benchmark.** Compare the full loop against baselines: (i) detection-only/no-response, (ii) always-holdover, (iii) always-failover. Metrics: discrimination accuracy, recovery-success rate, peak/steady time-error vs budget, **MTTR vs the 2 s window**, wrong-action rate. Generate results tables + plots (matplotlib). Acceptance: `results/` contains a reproducible comparison table + figures showing the loop reduces wrong-action rate / avoids outage vs baselines.

**P7 — Release + reproducibility.** Package the dataset + datasheet; write `scripts/run_all.py` that regenerates dataset → trains discriminator → builds twin → runs benchmark → writes all results with one command. Complete README (what/why/how-to-run), requirements pinned, all tests green. Acceptance: fresh `python scripts/run_all.py` runs end-to-end on CPU with no manual steps.

**P8 — Summary.** Write `results/SUMMARY.md`: what was built, the headline numbers, honest limitations (emulation vs hardware), and how each phase maps to the proposal. Acceptance: SUMMARY.md exists and is accurate.

## 5. CLEANUP / GARBAGE RULES (move, NEVER delete)
Create `_GARBAGE/` at the project root with subfolders `regenerable/`, `old_direction/`, `duplicates/`, and a `_GARBAGE/MANIFEST.md` that logs every moved file, its original path, and why. **Move (do not delete) only these:**
- `regenerable/`: `node_modules` (and its symlink), any `__pycache__`, `.venv`/`.project-python` caches, build artifacts, `.pytest_cache`.
- `duplicates/`: obvious duplicate/auto-saved exports (e.g. files ending `[Auto-saved]`, `(1)`, `(2)` copies) and stale duplicate outputs.
- `old_direction/`: the superseded RIC/KPM-direction docs — `PROBLEM_STATEMENT_SPECIALIZED.md`, `SPECIALIZATION_Fault_vs_Spoof_Discriminator.md`, `DIRECTION_Try_Before_You_Touch_SelfHealing.md`, `Project_Direction_OnePager.docx`, `ARCHITECTURE_and_ROADMAP.md`, and the folder `_local_quarantine/` if present.

**NEVER move or delete (KEEP whitelist):** `.git/`, `papers/`, `Project_Proposal_Fronthaul_SelfHealing.pdf`, `ORAN_BROAD_PROBLEM_SCAN.md`, `TWO_DIRECTIONS_Worked_Comparison.md`, `HANDOFF_CODEX_MASTER_PROMPT.md`, this prompt, and everything you create under `oran_splane_selfhealing/`.
**Ambiguous?** Move the large old codebase `oran_self_healing/` and `oran_twin/` into `archive/` (NOT `_GARBAGE/`) — they are prior work, keep them labelled but out of the way. When unsure, prefer `archive/` over `_GARBAGE/`.
**Rules:** never `rm`/delete anything; only move. Print a summary of everything moved. Note in MANIFEST that `_GARBAGE/` is staged for a future single deletion to reclaim C: space (moving alone does not free space).

## 6. CODING STANDARDS
Typed Python, small focused modules, docstrings, `pytest` tests, fixed random seeds, YAML config (no hardcoded paths), pinned `requirements.txt`, graceful fallback if an optional tool is missing, clear logging. No fabricated results anywhere — if a number isn't measured, don't invent it.

## 7. WORKING PROTOCOL (autonomous)
Proceed phase by phase without asking. After each phase: run its acceptance test, append a dated entry to `results/PROGRESS.md`, and `git commit` with a clear message. If blocked, write a stub + TODO and continue. At the end, ensure `python scripts/run_all.py` reproduces everything and all tests pass. Deliver `results/SUMMARY.md` last.

## 8. DEFINITION OF DONE
All phases green; one-command reproduction works on CPU with no hardware; tests pass; dataset + datasheet + benchmark tables + figures exist in `results/`; `_GARBAGE/` and `archive/` are organized with a manifest and nothing was deleted; README and SUMMARY explain the whole project honestly.

Begin now with P0.
