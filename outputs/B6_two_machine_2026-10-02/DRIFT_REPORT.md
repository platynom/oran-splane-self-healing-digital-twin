# B6 paired oscillator measurement - NOT ESTABLISHED

- Analysis: `pair-drift/1.0.0`, sha256 `7518898ce878a7c4...`
- Generated: 2026-10-02T15:03:47.754647+00:00
- Fault: **B6 oscillator drift / thermal** (BENIGN class)

## Verdict against pre-registered criteria

| ID | Criterion | Result | Detail |
|---|---|---|---|
| C1 | each arm retains >= 600 samples | **FAIL** | A=348, B=658 |
| C2 | common overlap >= 120 min | **PASS** | 142.8 min |
| C3 | no suspend/discontinuity in either retained series | **PASS** | 0 in A, 0 in B |
| C4 | both arms on the same reference, >=95% homogeneous | **PASS** | A=ntp@time.google.com (96.3%), B=ntp@time.google.com (97.4%) |
| C5 | relative-offset 95% CI half-width < 1 ppm | **PASS** | 0.797 ppm |

**Overall: NOT ESTABLISHED** (failed: C1)

## Headline

Relative frequency offset computes to +20.161 ppm  [+19.376, +20.969], but a pre-registered criterion failed, so this is reported as an observation and **must not be promoted as a validated figure**.

## Per-arm crystal offset vs UTC

| Arm | Host | Retained | Duration | ppm (bootstrap 95%) | Theil-Sen | Reference | RTT median |
|---|---|---:|---:|---|---:|---|---:|
| laptopA | Windows-11-10.0.26200-SP0 | 348/900 | 149.8 min | -4.189 ppm  [-4.306, -4.086] | -4.178 | ntp@time.google.com | 54.5 ms |
| laptopB | Windows-10-10.0.26200-SP0 | 658/900 | 146.0 min | -24.351 ppm  [-25.134, -23.565] | -24.371 | ntp@time.google.com | 105.2 ms |

### laptopA rejections
- `R1_source_switch`: dropped 33 (kept source=np.str_('ntp'))
- `R2_server_switch`: dropped 474 (kept server=np.str_('time.google.com'))
- `R3_rtt_outlier`: dropped 72 (rtt > 65.8 ms (median 54.5 ms))

### laptopB rejections
- `R1_source_switch`: dropped 23 (kept source=np.str_('ntp'))
- `R2_server_switch`: dropped 160 (kept server=np.str_('time.google.com'))
- `R3_rtt_outlier`: dropped 82 (rtt > 150.0 ms (median 105.2 ms))

## Relative stability (B6 parameters)

ADEV, TDEV and MTIE of the A-B relative time error. These are the parameters the Parameter Fault Matrix lists for B6 (L4 Servo: Allan deviation / MTIE / TDEV).

| tau (s) | ADEV | TDEV (s) | MTIE (s) |
|---:|---:|---:|---:|
| 10 | 7.802e-04 | 4.505e-03 | 3.918e-02 |
| 20 | 4.888e-04 | 4.216e-03 | 3.918e-02 |
| 30 | 3.517e-04 | 4.187e-03 | 3.918e-02 |
| 40 | 2.817e-04 | 4.150e-03 | 3.918e-02 |
| 60 | 1.882e-04 | 3.558e-03 | 3.918e-02 |
| 90 | 1.239e-04 | 3.304e-03 | 5.168e-02 |
| 130 | 9.764e-05 | 3.429e-03 | 5.168e-02 |
| 190 | 6.663e-05 | 3.639e-03 | 5.168e-02 |
| 280 | 4.797e-05 | 3.663e-03 | 5.168e-02 |
| 420 | 3.411e-05 | 3.693e-03 | 5.168e-02 |
| 630 | 2.309e-05 | 3.846e-03 | 5.168e-02 |
| 940 | 1.604e-05 | 3.755e-03 | 6.228e-02 |
| 1410 | 1.132e-05 | 3.914e-03 | 7.159e-02 |

## Measured instrument floor

- Short-tau ADEV log-log slope: **-0.79** (-1.0 = white phase noise, i.e. NTP/WiFi limited)
- ADEV at tau=10s: 7.802e-04
- No departure from the noise floor was detected in the measured tau range: over this run the pair is **floor-limited**, and only the frequency offset (not its instability) is measurable.

## Scope limits (carry these into any slide)

- Software timestamping over NTP/WiFi. The floor is milliseconds, roughly 10^5 above G.8273.2 cTE limits (50/20/10 ns). No ns-scale or mask-compliance claim is supported.
- Both hosts carry uncompensated consumer-grade quartz (not OCXO/TCXO/Rb). The measured envelope is a worst-case consumer figure, not a telecom-class holdover curve.
- No PTP ran between the two machines. This measures the physical premise of B6 (two crystals diverge, by how much, how steadily); it is NOT an end-to-end B6 detection test.
- Temperature was not controlled. Without the temp log, the benign thermal-correlation discriminator in the Parameter Fault Matrix (L8 Oscillator: temperature) is not evaluated.

## Provenance

- laptopA: `laptopA_20261002-175858_f0886ca920.csv` sha256 `5443796d015ce502...`
- laptopB: `laptopB_20261002-175545_b212d7a623.csv` sha256 `71a34ccc5fe29fbf...`
- Figure: `drift_pair.png`
