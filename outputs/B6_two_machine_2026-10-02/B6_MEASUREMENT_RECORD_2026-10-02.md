# B6 two-machine oscillator measurement — record

**Session tag:** `run1` · **Date:** 2026-10-02 · **Verdict: NOT ESTABLISHED (C1 failed)**

Governed by `PRE_REGISTRATION.md`, frozen before any data existed.
Analysis `pair-drift/1.0.0`, sha256 `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8`.

---

## 1. Apparatus (configured condition)

| | Arm A | Arm B |
|---|---|---|
| Label | `laptopA` | `laptopB` |
| Platform | Windows-11-10.0.26200-SP0 | Windows-10-10.0.26200-SP0 |
| Processor | Intel64 Fam 6 **Model 165** Step 2 | Intel64 Fam 6 **Model 186** Step 3 |
| node_hash | `720bc97877cf` | `2101a6b98881` |
| Counter resolution | 1e-07 s | 1e-07 s |
| Start (UTC) | 12:28:58 | 12:25:45 |
| End (UTC) | 14:58:48 | 14:55:36 |
| Samples ok / failed | 894 / 6 | 900 / 0 |

Different `node_hash` and different CPU models confirm two distinct physical machines. The
same-machine warning did not fire. Measurement code byte-identical on both arms
(`drift_probe.py` sha256 `703da1a9…be6`, verified on arm A before the run).

## 2. Observation

Accumulated time error of each raw counter against UTC, and their difference. The difference
cancels the time reference and leaves only the two crystals.

| Quantity | Value |
|---|---|
| Arm A crystal vs UTC | **−4.189 ppm** [−4.306, −4.086] |
| Arm B crystal vs UTC | **−24.351 ppm** [−25.134, −23.565] |
| **Relative (A − B)** | **+20.161 ppm** [+19.376, +20.969], half-width 0.797 ppm |
| Independent cross-check (interpolated difference series) | +20.027 ppm (Δ 0.134 ppm) |

Both counters run slow against UTC; arm A's crystal runs about 20 ppm faster than arm B's.
Over the 142.8 min overlap the two clocks separated by roughly 180 ms — visible as a clean
monotonic ramp in `drift_pair.png`, centre panel.

## 3. Verdict against the pre-registered criteria

| ID | Criterion | Result | Detail |
|---|---|---|---|
| C1 | each arm retains ≥ 600 samples | **FAIL** | A = 348, B = 658 |
| C2 | common overlap ≥ 120 min | PASS | 142.8 min |
| C3 | no suspend/discontinuity | PASS | 0 in A, 0 in B |
| C4 | same reference, ≥95% homogeneous | PASS | both `ntp@time.google.com`, 96.3% / 97.4% |
| C5 | relative CI half-width < 1.0 ppm | PASS | 0.797 ppm |

**Overall: NOT ESTABLISHED.** Four of five criteria passed. The figure above is therefore an
observation and is **not** promoted to a validated result.

## 4. Why C1 failed

Not sleep, not network loss — only 6 samples failed on arm A and 0 on arm B. The sample loss is
entirely from rejection rule **R2 (non-modal NTP server)**:

| Rule | Arm A dropped | Arm B dropped |
|---|---:|---:|
| R1 non-modal source | 33 | 23 |
| **R2 non-modal server** | **474** | **160** |
| R3 RTT outlier | 72 | 82 |

This is the probe defect recorded in `B6_RUN_PLAN_2026-10-02.md` before the run:
`drift_probe.py` line 206 reassigns the NTP server after any single sample failure. It did not
switch once — it **thrashed 97 times on arm A and 21 times on arm B**:

| Server | Arm A samples | Arm B samples |
|---|---:|---:|
| time.google.com | 420 | 740 |
| time.cloudflare.com | 415 | 91 |
| pool.ntp.org | 32 | 46 |
| HTTPS fallback | 33 | 23 |

R2 exists to prevent a systematic step between references from entering one arm only. What
actually occurred was rapid alternation, which behaves more like added noise than a step — but
the frozen rule does not distinguish the two, and it was not written after seeing this data, so
it stands as applied.

## 5. Post-hoc robustness check (NOT part of the frozen result)

Recomputed on each server subset independently, to test whether the switching biased the answer:

| Subset | Arm A ppm | Arm B ppm | Relative A−B |
|---|---:|---:|---:|
| google only (as frozen) | −5.172 (n=420) | −24.001 (n=740) | **+18.829** |
| cloudflare only | −3.957 (n=409) | −23.530 (n=91) | **+19.573** |
| all NTP servers pooled | −3.987 (n=861) | −23.574 (n=877) | **+19.587** |
| frozen analysis (R1–R3 applied) | −4.189 | −24.351 | **+20.161** |
| pool.ntp.org only (small n) | −10.825 (n=32) | −25.811 (n=46) | — |

The switching did **not** materially bias the result: every defensible subset lands between
**+18.8 and +20.2 ppm**.

**But that 1.33 ppm spread exceeds the frozen CI half-width of 0.797 ppm.** The formal interval
therefore understates the real uncertainty, which is dominated by analysis choice rather than by
sampling noise. The honest statement of the measurement is **approximately +19 to +20 ppm**, not
+20.161 ± 0.797.

## 6. What the stability analysis did NOT yield

The relative ADEV falls as τ⁻¹ across the whole measured range (fitted short-τ log-log slope
**−0.786**, no departure detected, `crossover_tau_s: null`). The pair is **floor-limited**: the
measurement resolves the frequency *offset* but not the oscillators' *instability*.

So **no ADEV, TDEV or MTIE figure from this run describes the crystals** — they describe the
NTP-over-WiFi instrument. Nothing here may be compared to a G.8273.2 or G.8261 wander mask.
ADEV at τ=10 s is 7.80e-04.

Arm A's thermal logger ran but reported `temperature_available: false` — the ACPI thermal zone is
not readable by an unprivileged process on this machine. The thermal-correlation discriminator
(Parameter Fault Matrix, *L8 Oscillator: temperature*) is therefore **unevaluated**.

## 7. Scope limits (carried verbatim from PRE_REGISTRATION.md §7)

1. **Not an end-to-end B6 detection test.** No PTP ran between the two machines, so the detector
   never saw this drift. This measures B6's physical premise and yields a real parameter in place
   of a guessed constant.
2. **No ns-scale or mask-compliance claim.** Floor is milliseconds, ~10⁵ above G.8273.2 cTE
   (50/20/10 ns).
3. **Not telecom-grade oscillators.** Uncompensated consumer quartz, not OCXO/TCXO/Rb. A
   worst-case consumer envelope, not a G.8273.2 class.
4. **Temperature uncontrolled and unrecorded** (see §6).
5. **Does not unlock B1, B4, A6 or A7**, and adds no hardware timestamping.

`ORAN_Fault_Detectability_v2026-09-29.xlsx` row B6 is **not** changed by this run. That row
describes detectability on the software testbed, which is unaffected.

## 8. What would make it ESTABLISHED

A new prospective run with the reference pinned, so R2 cannot fire. This is a **protocol fix, not
a criterion relaxation** — C1 must not be lowered to fit this data. The fix is to stop
`drift_probe.py` switching servers: let a sample fail and be recorded `ok=0` rather than silently
moving to another reference. With arm B's 900/900 success rate, pinning would have retained
roughly 820 samples per arm against the 600 required.

The replacement protocol must be frozen and hashed before the next run, exactly as this one was.
