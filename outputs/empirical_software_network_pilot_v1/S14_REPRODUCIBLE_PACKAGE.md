# S14 — Reproducible package and beginner explanation

Date 2026-09-13.

## 1. What this project measured, in plain words

Two computers on a small emulated network exchange PTP timing messages. A third program watches the
messages arrive and asks one narrow question: **are the arrival gaps becoming unusually spread out,
repeatedly, in a short space of time?** If yes, it says so. That is the whole claim. It does not say
the network is broken, attacked, or unhealthy, and it does not fix anything.

## 2. The six questions, for the things that matter

**The dispersion observation**
- WHAT: a standard deviation of 8 consecutive Sync-to-Follow_Up arrival gaps reaching 0.00016 s,
  twice within 3.0 s.
- WHICH: gaps from one source context only (capture, transport, PTP version, domain, source identity).
  Each gap belongs to at most one block; blocks never overlap.
- WHERE: measured at the packet capture point on the slave-facing bridge port, not inside the receiver.
- WHEN: computed as packets arrive, one pass, no lookahead. In V4 it first fired 5.45-8.88 s in.
- WHY these numbers: they are laboratory settings chosen during development, then frozen. No standard
  requires them and no hardware calibration supports them.
- HOW to verify: `python3 evaluate_v4_broader.py` replays every capture and rebuilds the result.

**The source-silence observation**
- WHAT: a source that was sending Announce messages has sent none for 0.75 s.
- WHICH: per source identity, reported once, with a reappearance event if it returns.
- WHERE / WHEN: same capture point, arrival-driven, or on a caller clock tick.
- WHY it is not more: an authorised operator stopping a source looks identical to any other silence.
  Silence is not an attack, not an outage, and not a clock failure.
- HOW: `SOURCE_ANNOUNCE_SILENCE_OBSERVED` in the evaluation JSON, per run.

**The condition labels**
- WHAT: which experiment a run belonged to.
- WHY it matters: labels were used only to group runs when reporting. They were never inputs to the
  detector. `tests/test_live_detection_causality.py` fails if a condition word appears in the engine.

## 3. Environment and versions

- Runner environment: WSL Ubuntu, root, with `ip`, `tc`, `ptp4l`, `tcpdump`. The exact ptp4l version
  is recorded in every run's `run_environment.txt`.
- Analysis environment: Python 3 standard library only, plus `openpyxl` for the spreadsheet view.
- Frozen hashes verified before every replay: v1 engine `1c1d7edfbcc38b6e...`,
  v3 non-overlap engine `ee328876367e6547...`,
  runner `94774063f997e710...`, validator `84afc4ea6045cd41...`.

## 4. Reproduction, in order

From the project root:

```
# 1. structural validation of every V4 run (writes validation.json)
for d in outputs/empirical_software_network_pilot_v1/v4_runs/*/; do
  PYTHONPATH=outputs/empirical_software_network_pilot_v1:01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing \
  python3 outputs/empirical_software_network_pilot_v1/validate_pilot.py "$d"; done

# 2. replay the frozen detector and rebuild the result
cd outputs/empirical_software_network_pilot_v1
PYTHONPATH=.:../../01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing python3 evaluate_v4_broader.py

# 3. causality tests for live use
PYTHONPATH=.:../../01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing \
python3 ../../01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tests/test_live_detection_causality.py

# 4. rebuild the final dataset
python3 build_s13_dataset.py

# 5. NOT YET RUN - needs WSL with root. The pre-registered next experiment:
bash outputs/empirical_software_network_pilot_v1/run_v5_single_variable_batch.sh
```

## 5. Protocols, in force order

| File | Status |
|---|---|
| `V3_NONOVERLAPPING_PROSPECTIVE_PROTOCOL.json` | executed, evaluated |
| `V4_BROADER_VALIDATION_PROTOCOL.json` | executed, evaluated |
| `V5_SINGLE_VARIABLE_PROTOCOL.json` | frozen, **not yet executed** |

V5 uses a new runner and validator (`run_empirical_software_pilot_v5.sh`, `validate_pilot_v5.py`)
because it needs three arms the V4 runner does not implement. The V4 runner and validator were left
byte-identical so V4 remains reproducible; both old and new hashes are recorded in the V5 protocol.

## 6. Final dataset

`s13_dataset/s13_runs.csv` and `s13_runs.xlsx`, 108 rows and 24 columns,
one row per run directory. Reconciliation in `s13_dataset/s13_reconciliation.json`:
108 directories on disk, 108 rows, none omitted,
0 simulated rows. Columns are grouped by evidence layer L1 to L8 so a configured
condition, an observed packet event, and a recovery outcome can never be read as the same thing.
Every recovery column reads NONE or NOT_ESTABLISHED, because no action was ever executed.
