# S-Plane detection — audit, corrections, and final validated results
**Date:** 2026-09-20 (overnight) · **Status:** corrected and re-validated · **Supersedes** all earlier 2026-09-20 result sheets

## Why this document exists
A cross-check audit of the same day's work found **four defects, two of them fabricating data**. Everything
below is the corrected position. Earlier numbers issued on 2026-09-20 (`v2 sensitivity 1.000 [0.962,1.000]`,
`specificity 0.800`, `C1/C2/C3 12/12`) are **withdrawn**. Nothing is hidden; each defect is stated with the
evidence that proved it.

---

## The four defects

### D1 — 36 "replicates" were one capture copied 12 times *(fabricated data)*
`run_gap.sh` was created mode **644** but invoked as `./run/run_gap.sh`, returning **exit 126
(Permission denied)**, silenced by `>/dev/null 2>&1`. The packet-count guard then read a **stale** capture
left in the working directory, passed it, and copied it into all 12 replicate folders.

*Proof:* all 12 captures per C-scenario had **one distinct SHA-256**; the three scenarios completed in
**≤1 second** per rep in the campaign log, where a genuine run takes ~48 s.
*Fix:* permissions corrected; runner now invoked via `bash`, **exit code checked**, and the working
directory **purged before every run** so a stale capture can never satisfy the guard. All 36 runs re-executed.

### D2 — `B3_pdv_congestion` never injected anything *(fabricated scenario, also affects the earlier campaign)*
This kernel has no `sch_netem` (`tc ... netem` → *"Specified qdisc kind is unknown"*), and `scenarios.sh`
swallowed the failure with `2>/dev/null||true`. B3 was a **baseline run wearing a congestion label**.

*Proof:* B3 PDV was statistically identical to baseline (ru1 median 62.4 ms / sd 36.0 ms vs 61.7 / 35.5),
and identical to the untouched ru3 control.
*Fix:* replaced with a **physical congestion model** — a `tbf` bottleneck on the BC→RU timing path plus
competing **non-PTP** background traffic through it, so PTP queues behind data-plane traffic. Deep queue ⇒
packets are *delayed, not dropped*. Sync PDV now rises from **0.07 ms to 5.6–857 ms**. All 12 reps re-run.
**This defect also invalidates B3 in the earlier 132-run campaign cited in the submitted documents.**

### D3 — the v2 detector produced false positives and destroyed an honest abstention
v2's rate-starvation detector (D1) had **no minimum-sample and no transient guard**. A boundary clock that
merely appears briefly during BMCA start-up (3–5 frames) was read as "rate starved."

*Proof (upstream captures):* `B2_gm_failover` **BENIGN → ATTACK**; `B_unplanned_failover` **UNKNOWN → ATTACK**,
i.e. it overwrote the deliberate abstention. Trigger: 3 frames → 0.06 Hz vs 16 Hz declared.
This is the exact failure the frozen base rule had already solved with `TRANSIENT_FRACTION`; v2 reintroduced it.
*Fix:* **`decision_rule_v3.py`** (frozen `aa9417b7`) adds a minimum-frame floor and a persistence requirement
(a source must be active across ≥50 % of the window before its rate is judged), includes the provisioned
*replacement* BC identity, and requires a UTC-offset change to be sustained. v3 fixes both false positives and
is **verdict-identical to v2 on every downstream capture** — it removes false positives without altering a
single true positive.

### D4 — the evaluator overstated and under-checked
`evaluate_v3.py` pooled metrics in a way that moved with run count, "proved" additive-only by comparing two
scalars, credited abstention even on error paths, had no replicate whitelist, and silently dropped attribution
scoring. Replaced by **`evaluate_v4.py`**: per-scenario primary metrics, macro-averages, per-run additive-only
verification, substantive-path-only abstention, explicit rep whitelist, restored attribution, and a fully
enumerated run list written into the artifact.

### Disclosure — frozen-manifest changes
`run/randparams.py` and `run/scenarios.sh` no longer match the 2026-09-17 manifest (`verify_frozen.sh` will
flag them). Reasons are recorded in `FROZEN_HARNESS_EPOCH2.json`. **The decision rules themselves are
unchanged and still match their original hashes** — only the experiment apparatus changed.

---

## Corrected results — 168 live runs (12 reps × 14 scenarios), all three rules on the same runs

Per-scenario is the **primary** metric. Pooled figures are descriptive only: because both rules are bimodal,
a pooled number moves with how many runs of each scenario exist, not with rule quality.

| Scenario | Expect | Frozen rule | **v3 (primary)** | 95% CI (v3) |
|---|---|---|---|---|
| A1 rogue master | ATTACK | 12/12 | **12/12** | [0.757, 1.000] |
| A2 sync spoof | ATTACK | 12/12 | **12/12** | [0.757, 1.000] |
| A3 replay | ATTACK | 12/12 | **12/12** | [0.757, 1.000] |
| A5 DoS flood | ATTACK | 12/12 | **12/12** | [0.757, 1.000] |
| A8 rogue BC | ATTACK | 12/12 | **12/12** | [0.757, 1.000] |
| C1 packet removal | ATTACK | **0/12** | **11/12** | [0.646, 0.985] |
| C2 malformed | ATTACK | **0/12** | **12/12** | [0.757, 1.000] |
| C3 whole-second | ATTACK | **0/12** | **12/12** | [0.757, 1.000] |
| baseline | BENIGN | 12/12 | 12/12 | [0.757, 1.000] |
| B2 GM failover | BENIGN | 12/12 | 12/12 | [0.757, 1.000] |
| B3 congestion *(now real)* | BENIGN | 11/12 | 11/12 | [0.646, 0.985] |
| B7 topology change | BENIGN | 12/12 | 12/12 | [0.757, 1.000] |
| B_bc_replacement | BENIGN | **0/12** | **0/12** | [0.000, 0.242] |
| B_unplanned_failover | UNKNOWN | 12/12 | 12/12 | [0.757, 1.000] |

| Summary | Frozen rule | **v3 (primary)** |
|---|---|---|
| Macro sensitivity (8 attack scenarios) | 0.625 | **0.990** |
| Macro specificity (5 benign scenarios) | 0.783 | **0.783** (identical) |
| Abstention correctness (substantive path) | 1.000 | 1.000 |
| Attribution accuracy | 0.552 | **0.875** |

**Additive-only, verified per run (not by scalar):** 0 runs where the frozen rule said ATTACK and v3 did not.
35 escalations, all on C1/C2/C3. v2 and v3 agree on every downstream run.

### Measured sensitivity limit (this is a real result, not a caveat)
C1 is **11/12**, and the miss is precisely located. D1 fires when delivered rate drops below 0.5× declared:

| blackhole | observed/declared | verdict |
|---|---|---|
| 75 % | 0.366 | caught |
| 70 % | 0.414 | caught |
| 65 % | 0.458–0.462 | caught |
| **60 %** | **0.505** | **missed** (threshold 0.500) |

**D1 detects sustained interception that blackholes ≳65 % of the observation window and evades below ~62 %.**
Short or bursty interception averages out and is not detected.

---

## Known limitations, not fixed
1. **`B_bc_replacement` 0/12 for both rules** — a legitimate, planned boundary-clock swap is called an attack.
   Context carries a single `expected_bc_identity`. It is a deterministic known gap, not a sampling rate;
   it is the entire reason specificity is 0.783 rather than 1.000. Fixing it needs a BC allow-list + re-freeze.
2. **D3 clause (c) will false-positive on real PRTC hardware** — it flags `clockClass ≤ 6` with traceability
   deasserted, which is normal for many production grandmasters. Not exercised here (testbed GMs advertise 248).
3. **`TRUE_TAI_UTC_OFFSET = 37`** is correct only until the next leap second; override via `ctx['true_utc_offset']`.
4. **C-scenario design space is small** — randomisation draws from only 4–5 distinct values, so 12 replicates
   are 12 genuine captures but not 12 independent attack *designs*.
5. **Hardware-only, out of software scope:** GNSS spoof (A6), GNSS jam (A7), delay-attack measurement (A4),
   holdover (B1), SyncE/EEC (B4), oscillator drift (B6).

## Evidence
`splane_campaign_CORRECTED_2026-09-20.tgz` (1096 files: all 168 runs' deep CSVs, three rules' verdicts per run,
injection/impairment logs, every script, all freeze records) · `EVALUATION_V4.json` (fully enumerated run list)
· `FROZEN_HARNESS_EPOCH2.json` (disclosed manifest changes) · `FROZEN_V3.json` (why v3 exists, stated openly).
Reproduce: `python3 run/evaluate_v4.py`.
