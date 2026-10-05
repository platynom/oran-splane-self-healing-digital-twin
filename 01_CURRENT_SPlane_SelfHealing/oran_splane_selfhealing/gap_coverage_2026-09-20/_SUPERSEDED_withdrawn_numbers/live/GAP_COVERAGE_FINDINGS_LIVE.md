# S-plane coverage-gap closure — LIVE on-wire validation
**Date:** 2026-09-20  ·  **Supersedes** the crafted-input version of 2026-09-20 (kept for provenance)
**Frozen rule:** `decision_rule.py` sha256 `c362e11…` — unchanged, hash-verified before every run
**Testbed:** real linuxptp **4.0**, G.8275.1 profile, 6 nodes in Linux network namespaces (GM-A, GM-B, BC, RU1-3)

## What changed since the crafted-input run
The privileged execution environment came back (root, `ptp4l`/`pmc`/`phc2sys`, scapy 2.5.0, working
network namespaces). So the three coverage items were re-run **on the wire** against the real testbed —
not against synthetic CSVs — and repeated twice for reproducibility. Clock-safe throughout: netns only,
software timestamping, host clock never touched.

## Result — reproduced across 2 reps (6 attack runs + 2 baselines)

| rep | scenario | disturbance actually in the capture | frozen | v2 |
|---|---|---|---|---|
| 1,2 | baseline | healthy, ~3960 PTP pkts | BENIGN ✓ | BENIGN ✓ |
| 1,2 | C1 packet removal | BC downstream blackholed; BC Sync **7.33 Hz** vs declared 16 | BENIGN — **MISS** | ATTACK `A_intercept` |
| 1,2 | C2 malformed | **167** on-wire frames version=3 / control=0x63 / msgType=0xF / len<min | BENIGN — **MISS** | ATTACK `A_malformed` |
| 1,2 | C3 whole-second | **170** forged Announce leap61=1, currentUtcOffset=0 (true 37) | BENIGN — **MISS** | ATTACK `A_wholesecond` |

**Aggregate:** frozen rule missed **6/6** attack runs (the three gaps, stable across reps); `decision_rule_v2`
caught **6/6**; **0/2** baseline false-positives for both frozen and v2.

Each fault was produced on the wire:
- **C1** — BC downstream port (`v-bc-dn`) blackholed for ~65% of the window, then restored (re-lock observable).
  `netem` is unavailable in this kernel, so removal is realised as a sustained link blackhole rather than
  probabilistic loss — a faithful selective-interception realisation that produces the rate collapse.
- **C2** — scapy injection of malformed PTP (`inject_malformed.py`) from a spoofed provisioned-GM identity,
  so the *only* anomaly is malformation (provenance checks pass).
- **C3** — scapy injection of forged Announce (`inject_wholesecond.py`) with legal header/clockClass/priority1
  and a legal declared rate, so the *only* anomaly is the abused timePropertiesDS.

## `decision_rule_v2` — UNFROZEN development extension
Additive-only (never turns a frozen ATTACK into BENIGN). Three detectors, each fixed by a standard or
self-referential: **D1** source below 0.5× the rate it itself declares; **D2** IEEE 1588-2019 field legality
(version=2, control 0-5, legal messageType, length ≥ per-type min); **D3** leap without a provisioned window,
UTCoffset non-constant or ≠true while valid, clockClass≤6 yet traceability deasserted. On the live baseline
all three stay quiet (0 false-positives).

## Two fixture defects found and fixed mid-run (recorded, not hidden)
1. First C1 used `tc netem loss` — the kernel has no `sch_netem` (`qdisc kind unknown`), so nothing dropped;
   the capture was healthy and both rules correctly said BENIGN. Fixed by switching to a link blackhole.
2. First C3 injector declared a garbage `logMessageInterval` (123), which tripped the frozen rule's
   rate-consistency clause (A5) — a detection for the wrong reason. Fixed by declaring `-3` (legal 8/s) so
   the whole-second fields are the sole anomaly; frozen then correctly misses and v2 D3 catches.

## Honest constraints that remain
- **v2 is still not frozen and not campaign-validated.** This is a reproduced live demonstration (2 reps),
  not the 132-run-style randomized campaign. Promoting D1-D3 to a headline metric requires re-freeze +
  a fresh randomized campaign.
- Hardware-only items remain isolated: GNSS spoof/jam, holdover, SyncE/EEC, oscillator drift, delay-attack.

## Artifacts (all in `gap_coverage_LIVE_2026-09-20.tgz`, hash in the .sha256)
`results/GAP_COVERAGE_LIVE.json` (verdicts + per-capture SHA-256) · `cap/<scenario>__live_r{1,2}/` (raw
pcaps, 56-col deep CSVs, context.json, decision.json, node logs) · `run/` (frozen rule + v2 + injectors +
`run_gap.sh`/`run_reps.sh`/`clean_all.sh` + analyzers + topology/start/stop). Every verdict reproducible:
`bash run/run_reps.sh 2 && python3 run/analyze_reps.py`.
