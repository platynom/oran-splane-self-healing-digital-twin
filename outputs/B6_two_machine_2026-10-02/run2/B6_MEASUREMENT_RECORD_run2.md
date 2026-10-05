# B6 two-machine oscillator measurement — RUN 2 record

**Session tag:** `run2` · 2026-10-02 21:13–00:13 IST · **Verdict: ESTABLISHED**

Governed by `PRE_REGISTRATION_RUN2.md`, frozen before any run-2 data existed.
Analysis `pair-drift/1.0.0`, sha256 `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8`
— **unchanged from run 1**. The analysis that failed run 1 is the one that passed run 2.

---

## 1. Apparatus

| | Arm A | Arm B |
|---|---|---|
| Label | `laptopA` | `laptopB` |
| Platform | Windows-11-10.0.26200 | Windows-10-10.0.26200 |
| Processor | Intel Fam 6 **Model 165** Step 2 | Intel Fam 6 **Model 186** Step 3 |
| node_hash | `720bc97877cf` | `2101a6b98881` |
| Start (UTC) | 15:43:29 | 15:44:01 |
| End (UTC) | 18:43:19 | 18:43:51 |
| Samples ok / failed | 1031 / 49 | 1069 / 11 |
| Retained after rejection | **906** | **846** |

Same two physical machines as run 1 (node hashes match). Start offset 32 seconds.
Probe protocol v2, `drift_probe.py` sha256
`0f5c04b7268425419c8466208d6f00276bc8093a078ee60beb018156dd94f593`.

## 2. Verdict

| ID | Criterion | Result | Detail |
|---|---|---|---|
| C1 | each arm retains ≥ 600 samples | **PASS** | A = 906, B = 846 |
| C2 | common overlap ≥ 120 min | **PASS** | 179.3 min |
| C3 | no suspend/discontinuity | **PASS** | 0 in A, 0 in B |
| C4 | same reference, ≥95% homogeneous | **PASS** | both `ntp@time.google.com`, **100.0% / 100.0%** |
| C5 | relative CI half-width < 1.0 ppm | **PASS** | 0.390 ppm |

**Overall: ESTABLISHED.**

**The v2 fix worked exactly as designed.** Rule R2 (non-modal server) fired on
**zero** samples in either arm, against 474 and 160 in run 1. Reference
homogeneity was 100.0% on both arms, against 96.3% / 97.4%. The only rejections
were R3 RTT outliers (125 on A, 223 on B). Zero suspends.

## 3. Result

| Quantity | Run 2 |
|---|---|
| Arm A crystal vs UTC | **−2.877 ppm** [−3.029, −2.736] |
| Arm B crystal vs UTC | **−23.891 ppm** [−24.240, −23.532] |
| **Relative (A − B)** | **+21.013 ppm** [+20.623, +21.403] |

Over the 179.3 min overlap the two clocks separated by about 230 ms — the
monotonic ramp in `drift_pair.png`, centre panel.

## 4. Comparison with run 1 — the two runs do NOT fully agree

|  | Run 1 (18:00–20:30) | Run 2 (21:13–00:13) | Shift |
|---|---|---|---|
| Arm A vs UTC | −4.189 [−4.306, −4.086] | −2.877 [−3.029, −2.736] | **+1.312 ppm** |
| Arm B vs UTC | −24.351 [−25.134, −23.565] | −23.891 [−24.240, −23.532] | **+0.460 ppm** |
| **Relative A − B** | **+20.161** [19.376, 20.969] | **+21.013** [20.623, 21.403] | **+0.852 ppm** |

The two confidence intervals overlap only over **20.623 to 20.969 ppm**, a window
0.347 ppm wide. They are formally consistent, but only barely. Neither point
estimate falls inside the other run's interval.

**This must not be hidden behind run 2's tighter CI.** The defensible statement
across all the evidence — run 1, run 1's server-subset robustness check
(+18.8 to +20.2), and run 2 — is:

> **The two crystals differ by approximately 19 to 21 ppm.**

Quoting `+21.013 ± 0.390` as the whole truth would overstate what two runs
support. The within-run interval measures sampling noise; it does not capture
run-to-run variation, which is roughly twice as large.

## 5. The run-to-run shift is itself a B6 observation

Arm A moved +1.312 ppm between an early-evening run and an overnight run; arm B
moved +0.460 ppm. A consumer quartz oscillator's frequency is temperature
dependent, and the research catalogue's B-48 (*Temperature transient*) gives the
mechanism: frequency-vs-temperature converted into a frequency-vs-time ramp,
with quartz slope around 10 ppb/°C in the normal range. A shift of this size
between evening and overnight ambient is physically plausible.

**That is a hypothesis, not a finding.** It cannot be claimed, because:

- **No temperature was recorded.** `temp_log.py` ran on arm A for all 1080
  samples and captured **0 temperature values** — the ACPI thermal zone is not
  readable by an unprivileged process on that machine. Only CPU load (mean
  42.9%, median 47.5%) and frequency (2592 MHz, flat) were logged, and neither
  is a temperature.
- Two runs is not a series. Nothing here separates thermal effect from ageing,
  load, supply, or ordinary short-term wander.

What *is* established is narrower and still useful: **the relative frequency
offset between two real crystals is not a fixed constant over hours.** That is
precisely the behaviour B6 describes, and the single-clock software testbed
cannot exhibit it at all.

## 6. Stability still did not resolve

Relative ADEV falls as τ⁻¹ across the whole measured range (short-τ log-log
slope **−0.878**, `crossover_tau_s: null`). The pair remains **floor-limited**:
the run measures frequency *offset* only, not oscillator *instability*.
ADEV at τ=10 s is 1.50e-03.

**No ADEV, TDEV or MTIE figure from either run describes the crystals** — they
describe the NTP-over-WiFi instrument. None may be compared to a G.8273.2 or
G.8261 wander mask. Tripling the duration again would not fix this; the limit is
the measurement path, which would need hardware timestamping.

## 7. Scope limits (unchanged, carried verbatim)

1. **Not an end-to-end B6 detection test.** No PTP ran between the machines; the
   detector never saw this drift. This measures B6's physical premise and yields
   a real parameter in place of a guessed constant.
2. **No ns-scale or mask-compliance claim.** Floor is milliseconds, ~10⁵ above
   G.8273.2 cTE (50/20/10 ns).
3. **Not telecom-grade oscillators.** Uncompensated consumer quartz, not
   OCXO/TCXO/Rb. A worst-case consumer envelope, not a G.8273.2 class.
4. **Temperature uncontrolled and unrecorded** (§5).
5. **Does not unlock B1, B4, A6 or A7**, and adds no hardware timestamping.
6. `ORAN_Fault_Detectability_v2026-09-29.xlsx` row B6 is **not** changed by this
   run. That row describes detectability on the software testbed, which is
   unaffected by either run.

## 8. What would advance this further

- **Temperature**, by any means that works: an admin-elevated run, HWiNFO/
  LibreHardwareMonitor logging, or a cheap USB thermal probe. Without it the
  thermal discriminator — the one the Parameter Fault Matrix names for B6 and
  that catalogue D-12 calls the attack/benign separator — stays unevaluated.
- **More repeats at different times of day**, to turn the run-to-run shift from
  an anecdote into a characterised envelope.
- **Hardware timestamping** (i210/i226-class NIC) to drop the floor from
  milliseconds and make the stability statistics meaningful.
- **PTP between the two hosts**, which is what would make B6 an actual detection
  experiment rather than a parameter measurement.
