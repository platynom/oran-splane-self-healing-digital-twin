# Pre-registration — B6 paired oscillator measurement

**Fault:** B6 "Oscillator drift / thermal", BENIGN class.
**Status before this run:** `NO — structurally impossible`. All namespaces share one
kernel clock derived from one crystal (`ORAN_Fault_Detectability_v2026-09-29.xlsx`,
sheet DETECTABILITY, row B6).
**Why this run exists:** that same row says *"A 2nd PC SOLVES THIS. This is the
single fault your procurable hardware unlocks."*

This document is frozen **before** the measurement data exists. It fixes the
analysis so the result cannot be tuned after the fact. The S15 specificity miss
is the precedent: a boundary derived on its own validation set is not evidence.

---

## 1. Apparatus

| | |
|---|---|
| Arm A | laptop A (project machine), native Windows Python |
| Arm B | laptop B (teammate's machine), native Windows Python |
| Measurement code | `oran_drift/drift_probe.py`, **byte-identical on both arms** |
| Counter | `time.perf_counter()` → `QueryPerformanceCounter`, undisciplined by Windows |
| Reference | `time.google.com` SNTP, **same reference on both arms** |
| Sampling | 1 sample / 10 s, 150 min planned → 900 samples/arm |
| Thermal covariate | `temp_log.py`, arm A only, read-only, independent process |
| Analysis | `pair_drift.py`, frozen, hash recorded in §6 |

Arm A additionally runs `temp_log.py`. This is an **asymmetry by design**: it is a
per-machine covariate, not a differenced quantity, so one-sided availability
costs nothing. The measurement code itself stays identical across arms.

## 2. Quantity under measurement

Per arm, the accumulated time error of the raw counter against UTC:

```
true_time = wall_clock + ntp_offset            # immune to w32time corrections
TE(t)     = (counter - counter[0]) - (true_time - true_time[0])
ppm       = (1/slope - 1) x 1e6,  slope = d(true_time)/d(counter)
```

Positive ppm means the counter runs fast. The **B6 quantity** is the difference
`ppm_A - ppm_B`: the reference and its systematic error cancel in the
difference, leaving only the two physical crystals.

Secondary (the parameters the Parameter Fault Matrix actually lists for B6 —
*L4 Servo: Allan deviation / MTIE / TDEV*): overlapping ADEV, MDEV, TDEV and
MTIE of the relative time-error series, per ITU-T G.8260 definitions.

## 3. Rejection rules (frozen)

Applied in order, before any fit. Every rejection is counted and reported.

| ID | Rule | Rationale |
|---|---|---|
| R1 | Drop samples whose `source` differs from the arm's modal source | A mid-run fallback from NTP to HTTPS changes the reference's precision class |
| R2 | Drop samples whose `ntp_server` differs from the arm's modal server | `drift_probe.py` line 206 can silently and permanently switch servers after one failure; the reference only cancels if both arms stay on the same one |
| R3 | Drop samples with `rtt > median + 3·MAD`, and any `rtt > 1.0 s` | Under a symmetric-delay assumption the offset error is bounded by rtt/2, so a long rtt is a direct precision penalty |
| R4 | Flag discontinuities: counter step deviating from expected by >1.5×interval, or \|counter step − wallclock step\| > 1 s | Detects sleep/hibernate and wall-clock steps. Both are logged, so a suspend is **detectable after the fact**, not silently fatal |

## 4. Acceptance criteria (frozen)

The verdict is **ESTABLISHED** only if all five pass. Any failure yields
**NOT ESTABLISHED**, and the report explicitly refuses to promote the number.

| ID | Criterion |
|---|---|
| C1 | Each arm retains ≥ 600 samples after rejection |
| C2 | Common overlap ≥ 120 min |
| C3 | Zero discontinuities in either retained series |
| C4 | Both arms on the same reference, ≥ 95% homogeneous, same server |
| C5 | Relative-offset 95% CI half-width < 1.0 ppm |

## 5. Statistical method (frozen)

- Point estimate: OLS slope per arm; relative = `ppm_A − ppm_B`.
- Interval: moving-block bootstrap, 300 s blocks, 2000 draws, seed 20261002.
  Blocks are used because NTP residuals are autocorrelated and a naive OLS
  standard error is optimistic. The relative CI is the percentile interval of
  the **difference of the two arms' independent bootstrap distributions**, not a
  fit to the interpolated difference series — interpolation onto a common grid
  smooths per-arm noise and understates the uncertainty.
- Robustness: Theil–Sen slope reported alongside OLS; the interpolated
  difference slope reported as an independent cross-check.
- Instrument floor: white phase noise gives ADEV ∝ τ⁻¹. The short-τ log-log
  slope is fitted and reported; the τ at which observed ADEV rises a factor of
  2 above that extrapolation is the point above which oscillator instability is
  separable from network noise. Below that τ the measurement sees the network,
  not the crystal.

### Validation of the method before use

`selftest_pair_drift.py` synthesises arms with known ppm and asserts recovery.
All 25 assertions pass. Measured on synthetic data:

| Property | Result |
|---|---|
| Recovery of a known +12.0 / −8.0 ppm pair | within 0.04 ppm mean absolute error |
| 95% CI coverage over 40 independent seeds | 37/40 = 92% (consistent with 95%; binomial sd ≈ 3.5%) |
| ±25 ms injected w32time wander on the wall clock | does not leak into ppm (cancels via the offset term) |
| Arm sleeping 400 s mid-run | detected, C3 fails, NOT ESTABLISHED |
| Arm switching NTP server mid-run | R2 fires, C4 fails |
| Both arms reporting the same host | CRITICAL warning raised |
| 12% sample loss | relative still within 0.3 ppm of truth |
| Coarse `https_date` reference (1 s granularity) | CI half-width **16.9 ppm**, C5 fails, no headline |

That last row is the decisive operational finding: **if either arm falls back to
the HTTPS `Date` header, the run is worthless** — 16.9 ppm of uncertainty against
an expected signal of 10–50 ppm. C5 catches it automatically, but it is cheaper
to check the pre-flight output and switch network before starting.

## 6. Freeze record

Fill in before the run starts. Hashes computed with
`Get-FileHash -Algorithm SHA256`.

| Artefact | SHA-256 |
|---|---|
| `drift_probe.py` (both arms) | `703da1a97126a1d24ed3792a562c2e5a2a236a2aed7c8720141a1888dbb07be6` |
| `check_setup.py` | `2da26bd76c91a5400c89ff81cccd060cef7b61eaa3abb5c03f30e77435a5452a` |
| `1_CHECK_FIRST.bat` | `f90e3f24934dfa1da6ccee6814f2aa31851bd2f066a2e43a40e81edac9d22393` |
| `2_RUN_MEASUREMENT.bat` | `c7b381545fe1381e611ee70a2fcaea4f1d2b31901f87d24db436a2a141fea409` |
| `pair_drift.py` | `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8` |
| `temp_log.py` | `a1ba66f4738c6fe888d6d9bd6d88c9b1d2324cde9072af4501a0a8c54beba2cb` |
| `selftest_pair_drift.py` | `53dd7eb5292143c195d7b932393cfef199ad0c1268fd7c87aefab8a52ecb26fe` |

The first four are the hashes of the measurement code **as sent to laptop B**.
Verify them on both machines before starting (§9 step 2) — that is what makes
"byte-identical on both arms" a checked fact rather than an assumption.

Frozen at (UTC): ______________________  Session tag: ______________

## 9. Run procedure

1. **Both arms:** extract `oran_drift` to the Desktop. Do not run from inside
   the zip.
2. **Both arms:** verify the measurement code hash —
   `Get-FileHash -Algorithm SHA256 .\drift_probe.py` — against the table above.
   Any mismatch stops the run.
3. **Both arms:** run `1_CHECK_FIRST.bat`. Require `READY`. Read the reference
   line: it must say `[ntp, precision: high]`. If it says `https`, switch
   network (phone hotspot) and re-check — see §5, a coarse reference costs the
   whole run.
4. **Both arms:** plug in; set Settings → System → Power & battery → Screen and
   sleep → "When plugged in, put my device to sleep after" = **Never**.
5. **Arm A only:** also set `powercfg /change standby-timeout-ac 0` if Modern
   Standby is present, and start `temp_log.py` in a second window.
6. **Agree the session tag and a start time within 10 minutes of each other.**
   Both type the same tag.
7. **Both arms:** run `2_RUN_MEASUREMENT.bat`, label `laptopA` / `laptopB`,
   same session tag. Leave the window open 150 min.
8. Collect both `results` folders. Run
   `python pair_drift.py --a <A> --b <B> --session <tag>`.
9. Record the verdict as it comes out, including NOT ESTABLISHED.

## 7. What this run does NOT establish

Stated here, in advance, so it cannot be quietly widened afterwards.

1. **This is not an end-to-end B6 detection test.** No PTP runs between the two
   machines. The run measures B6's *physical premise* — that two independent
   crystals diverge, by how much, and how steadily — and yields a real parameter
   to replace a guessed constant. The detector never sees it. Converting B6 from
   `structurally impossible` to `measured` requires ptp4l across the two hosts,
   which is a separate experiment.
2. **No ns-scale or mask-compliance claim.** The floor here is milliseconds,
   roughly 10⁵ above the G.8273.2 cTE limits (50/20/10 ns) and far above any
   G.8261 wander mask. MTIE and TDEV are reported as *measured wander of this
   apparatus*, never as a pass/fail against a standardised mask. This follows
   the project's own Class B rule: express thresholds as multiples of the
   measured floor, never as the standard's absolute ns limits.
3. **Not telecom-grade oscillators.** Both hosts carry uncompensated consumer
   quartz, not OCXO/TCXO/Rb. Per the Parameter Fault Matrix row *"oscillator
   type / holdover spec — defines what envelope 'benign' even means"*, the
   measured envelope is a worst-case consumer figure, not a telecom holdover
   curve. It bounds the problem from the wrong side of the spec, and that is
   still useful, but it is not a G.8273.2 class.
4. **Temperature is uncontrolled**, and may be unavailable entirely. Both
   laptops are in normal use on WiFi. Any thermal correlation is observational.
5. **It does not unlock B1, B4, A6 or A7**, and it does not add hardware
   timestamping. That needs an i210/i226-class NIC, which is what would drop the
   floor from microseconds to tens of ns and make A4/B5 measurable.

## 8. Expected outcome

Consumer crystals typically sit 10–50 ppm from nominal, so a relative offset of
roughly 5–60 ppm is expected, with a CI half-width well under 1 ppm on a clean
NTP run. A relative offset below about 1 ppm would be surprising and would
warrant checking that the two arms really are two machines (the `node_hash`
warning covers the gross case).

The honest headline, if it passes: *two independent consumer crystals were
measured to differ by X.X ± Y.Y ppm over N minutes, on real hardware, which is
a quantity the single-machine software testbed cannot produce by construction.*
