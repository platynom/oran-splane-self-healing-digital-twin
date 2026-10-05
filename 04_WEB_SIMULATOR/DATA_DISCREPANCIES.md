# Data discrepancies

**Result: no numeric discrepancy was found between the recomputed values and the project's published results.**
Nothing in `RESULTS_2026-10-05.md` had to be overridden, and the app uses no number that the
recomputation did not reproduce.

How this was checked (all automated, re-runnable):

| Check | Where | Outcome |
|---|---|---|
| sha256 of `recovery_eval_runs_r13-r17.tgz`, `EVALUATION_RL.json` against `results/SHA256SUMS.txt`; campaign archive against its `.sha256` | `ingest/extract.py` (refuses to continue on mismatch) | match |
| Every one of the 140 runs re-scored from `observer.jsonl` with the PREREGISTRATION §4 definitions, compared field by field with `EVALUATION_RL.json` | `ingest/extract.py` (Python) | 140/140 identical |
| The same re-scoring from the PostgreSQL rows (TypeScript, `src/lib/metrics.ts`), compared with the extractor and with `EVALUATION_RL.json`: unhealthy_s, ru3_unhealthy_s, rogue_parent_s, restored_at_end, pre-T0 health, outage_s, first ATTACK verdict, first action | `scripts/ingest.ts`, `tests/unit/results.db.test.ts` | 140/140 identical |
| Headline: A1 38.5 vs 2.0 s, C1 39.0 vs 2.5 s, C3 38.5 vs 2.0 s; H1/H2/H4/control integrity PASS; H3 FAIL with 1/25 (Wilson [0.007, 0.195]); 41 would_act; 35/35 isolations in nft; 6/6 standby with bcs.log | `tests/unit/results.db.test.ts`, `e2e/app.spec.ts` | reproduced |
| 168-run campaign: v3 95/96, 47/60, abstention 12/12, attribution 84/96; base rule 60/96 and 53/96; v2 = v3 on all runs | `ingest/extract.py` vs `EVALUATION_V4.json`; unit tests | reproduced |

## Notes (no number changes, recorded for transparency)

1. **Campaign `context.json` replicate field.** The 36 campaign runs of C1, C2 and C3 carry `"rep": 901` in
   `context.json`, while their directory names give replicates 1–12. `evaluate_v4.py` takes the replicate from the
   directory name; the app does the same (a 1–12 replicate filter on the context field would have dropped these 36 runs).
2. **Rounding ties.** `analyse.py` rounds with Python `round()`, which sends exact binary ties to the even digit
   (round(2.125, 2) = 2.12). A first JavaScript port used `toFixed` (2.13) and differed on one value
   (A3 r16 loop first_action_s 2.12). `src/lib/metrics.ts` now implements Python's semantics; covered by tests.
3. **Known scorer property, already disclosed in RESULTS §5.** For the 15 control runs of A1, C1 and C3 the project
   scorer stops at the last observer sample (about T0 + 39.55 s), under-counting control-arm harm by about 0.44 s per
   run (38.51 vs 38.96 s). The app reproduces the project scorer exactly and states this on the dashboard.
4. **B3 r17 action time.** RESULTS §3 says the standby BC was activated "at T0 + 5.1 s"; the recomputed
   first_action_s is 5.07 s (the same value rounded).
5. **A8 parent samples.** RESULTS §4 reports "160/160 samples on the real BC". The database shows 160/160 in each of
   the five A8 control runs (RU1 + RU2, T0 … T0 + 40 s), i.e. the figure is per run.
6. **Verification latency.** RESULTS §1 says verification passed "within about 1 s". Recomputed: 41/41 verifications
   passed, median 0.31 s, maximum 1.15 s after the action.
7. **Packet-series alignment (app-specific).** tcpdump stamps frames with CLOCK_REALTIME while the loop, observer and
   ptp4l use CLOCK_MONOTONIC. Each run's packet counts are aligned with one anchor (the BC downstream port's first
   Announce vs its ptp4l "to MASTER" line). Validated on 36 independent anchors: median residual 0.1 ms, max 1.0 ms.
8. **Offline rule re-run (app-specific).** The sandbox's window parameter uses the frozen rule re-run on each control
   run's brDN capture (`ingest/rule_windows.py`). At W = 6 s it agrees with the verdicts logged live at 3426/3430
   ticks (99.88 %). The 4 differences are single ticks at attack onset (A3 r14, r17; C2 r13, r17), where a frame lands
   within milliseconds of the evaluation tick and the bridge capture and the per-port live capture see it on opposite
   sides of the tick.
