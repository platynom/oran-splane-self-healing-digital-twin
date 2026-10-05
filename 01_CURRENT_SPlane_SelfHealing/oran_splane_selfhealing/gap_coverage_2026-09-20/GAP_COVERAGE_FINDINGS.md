# S-plane coverage-gap closure — detection-logic validation
**Date:** 2026-09-20  ·  **Status:** development (UNFROZEN); not yet campaign-validated

## What this is (and is not)
- **Is:** a controlled test showing (a) three attack classes the frozen rule provably misses, and
  (b) a development extension (`decision_rule_v2`) that catches them without false-positiving on
  real healthy PTP.
- **Is NOT:** live on-wire runs, and NOT a new frozen result. The frozen decision rule
  (`decision_rule.py`, sha256 `c362e11…`) is **unchanged** and hash-verified. `decision_rule_v2`
  is a separate, clearly-labelled development file.

## Why crafted inputs, not live runs
No execution environment was available this session: the linked device VM is unprivileged
(network-namespace creation denied; no `ptp4l`/`scapy`), and the cloud shell is blocked. Rather
than fake a run, each gap was tested by feeding the **frozen rule** crafted deep-CSV inputs that
differ from a conformant G.8275.1 baseline by **exactly one injected signature** — the same
detection-logic method already used by `conformance_neg.py`.

## Result 1 — the three gaps are real (frozen rule, hash-verified)
| Input (only delta from baseline) | Truth | Frozen verdict |
|---|---|---|
| `synth_base` (conformant control) | BENIGN | **BENIGN** ✓ control |
| `synth_item1_removal` — 70% of Sync/Follow_Up/Delay_Resp dropped (O-RAN 11.1.5.3.1) | ATTACK | **BENIGN** ✗ MISS |
| `synth_item2_malformed` — 200 GM frames: version≠2, length<min, control>5 (O-RAN 24.2.1.2) | ATTACK | **BENIGN** ✗ MISS |
| `synth_item3_wholesecond` — leap61=1, UTCoffset 37→0, traceability stripped (IEEE 1588-2019 §7.2.4) | ATTACK | **BENIGN** ✗ MISS |

The control passing while all three attacks pass as BENIGN isolates the blindness to the injected
class — the frozen rule inspects none of: observed-vs-declared rate, frame legality
(version/length/control), or timescale metadata (leap/UTC/traceability).

## Result 2 — `decision_rule_v2` closes them (additive only)
Three standards-grounded detectors, each either fixed by a standard or **self-referential**
(compared to what the sender itself declares — no constant fitted to the crafted inputs):
- **D1 removal:** a *provisioned* source delivering Sync/Announce below 0.5× the rate **it itself declares** → interception/starvation.
- **D2 malformed:** IEEE 1588-2019 field legality — versionPTP=2, control 0–5, legal messageType, message_length ≥ per-type minimum.
- **D3 whole-second:** leap61/59 asserted with no provisioned leap window; currentUtcOffset non-constant or ≠ true offset while declared valid; clockClass ≤6 (claims traceable) yet deasserting traceability.

`decide_v2` runs the frozen rule first and **never turns a frozen ATTACK into BENIGN** — it only
escalates BENIGN/UNKNOWN when a new detector fires.

| Input | v2 verdict | detector |
|---|---|---|
| `synth_base` | BENIGN ✓ (unchanged) | — |
| `synth_item1_removal` | **ATTACK** ✓ | D1 (A_intercept) |
| `synth_item2_malformed` | **ATTACK** ✓ | D2 (A_malformed) |
| `synth_item3_wholesecond` | **ATTACK** ✓ | D3 (A_wholesecond) |

## Result 3 — new detectors do not false-positive on REAL healthy PTP
Run directly on the two real-hardware healthy captures (`netem_baseline`, `netem_pdv`):
**D1, D2, D3 all stay quiet on both.** (They declare logSync −3 and deliver 7.98/s → self-referential
rate check quiet; version=2, control≤5, lengths at minimum; no leap flags; UTC constant 37;
clockClass 248 (>6) so the traceability clause correctly does not apply.)
The additive-only property was also verified: on these captures the frozen base returns ATTACK
(domain-0, out-of-profile by design) and v2 returns the **same** ATTACK — never softened.

## Honest constraints carried forward
1. **v2 is not frozen and not campaign-validated.** Putting D1–D3 into a headline metric requires
   re-freeze + a fresh randomized campaign on the live testbed.
2. **No live on-wire validation this session** (no privileged execution environment).
3. `netem_baseline`/`netem_pdv` are **domain-0** real captures — valid as new-detector FP controls,
   **not** as G.8275.1 benign-classification controls (the frozen base flags them A5 on domain, by design).
4. Items still requiring hardware remain isolated and out of scope (GNSS spoof/jam, holdover, SyncE,
   oscillator drift, delay-attack measurement).

## Files
- `decision_rule.py` — FROZEN, unchanged (sha256 c362e11…)
- `decision_rule_v2.py` — development extension (D1/D2/D3), additive-only
- `gen_gapcheck.py` — deterministic fixture generator (seed 1588)
- `synth_base|item1|item2|item3 .deep.csv` — crafted inputs (+ SHA-256 in GAP_COVERAGE.json)
- `GAP_COVERAGE.json` — machine-readable results
