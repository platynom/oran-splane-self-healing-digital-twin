# B6 paired oscillator measurement - ESTABLISHED

- Analysis: `pair-drift/1.0.0`, sha256 `7518898ce878a7c4...`
- Generated: 2026-10-02T19:20:11.214923+00:00
- Fault: **B6 oscillator drift / thermal** (BENIGN class)

## Verdict against pre-registered criteria

| ID | Criterion | Result | Detail |
|---|---|---|---|
| C1 | each arm retains >= 600 samples | **PASS** | A=906, B=846 |
| C2 | common overlap >= 120 min | **PASS** | 179.3 min |
| C3 | no suspend/discontinuity in either retained series | **PASS** | 0 in A, 0 in B |
| C4 | both arms on the same reference, >=95% homogeneous | **PASS** | A=ntp@time.google.com (100.0%), B=ntp@time.google.com (100.0%) |
| C5 | relative-offset 95% CI half-width < 1 ppm | **PASS** | 0.390 ppm |

**Overall: ESTABLISHED**

## Headline

Relative frequency offset between the two physical crystals: **+21.013 ppm  [+20.623, +21.403]** (95% moving-block bootstrap).

## Per-arm crystal offset vs UTC

| Arm | Host | Retained | Duration | ppm (bootstrap 95%) | Theil-Sen | Reference | RTT median |
|---|---|---:|---:|---|---:|---|---:|
| laptopA | Windows-11-10.0.26200-SP0 | 906/1080 | 179.8 min | -2.877 ppm  [-3.029, -2.736] | -2.898 | ntp@time.google.com | 54.2 ms |
| laptopB | Windows-10-10.0.26200-SP0 | 846/1080 | 179.8 min | -23.891 ppm  [-24.240, -23.532] | -23.899 | ntp@time.google.com | 121.5 ms |

### laptopA rejections
- `R3_rtt_outlier`: dropped 125 (rtt > 68.5 ms (median 54.2 ms))

### laptopB rejections
- `R3_rtt_outlier`: dropped 223 (rtt > 185.0 ms (median 121.5 ms))

## Relative stability (B6 parameters)

ADEV, TDEV and MTIE of the A-B relative time error. These are the parameters the Parameter Fault Matrix lists for B6 (L4 Servo: Allan deviation / MTIE / TDEV).

| tau (s) | ADEV | TDEV (s) | MTIE (s) |
|---:|---:|---:|---:|
| 10 | 1.499e-03 | 8.655e-03 | 5.432e-02 |
| 20 | 8.182e-04 | 6.964e-03 | 6.472e-02 |
| 30 | 5.908e-04 | 6.398e-03 | 6.472e-02 |
| 40 | 4.360e-04 | 6.084e-03 | 6.472e-02 |
| 60 | 3.127e-04 | 5.754e-03 | 6.472e-02 |
| 90 | 2.126e-04 | 4.953e-03 | 6.472e-02 |
| 130 | 1.420e-04 | 4.312e-03 | 6.472e-02 |
| 190 | 9.902e-05 | 3.704e-03 | 6.876e-02 |
| 280 | 6.869e-05 | 3.281e-03 | 7.946e-02 |
| 420 | 4.503e-05 | 2.939e-03 | 7.946e-02 |
| 630 | 3.113e-05 | 3.398e-03 | 7.946e-02 |
| 940 | 2.298e-05 | 4.160e-03 | 9.429e-02 |
| 1410 | 1.535e-05 | 4.208e-03 | 1.020e-01 |

## Measured instrument floor

- Short-tau ADEV log-log slope: **-0.88** (-1.0 = white phase noise, i.e. NTP/WiFi limited)
- ADEV at tau=10s: 1.499e-03
- No departure from the noise floor was detected in the measured tau range: over this run the pair is **floor-limited**, and only the frequency offset (not its instability) is measurable.

## Scope limits (carry these into any slide)

- Software timestamping over NTP/WiFi. The floor is milliseconds, roughly 10^5 above G.8273.2 cTE limits (50/20/10 ns). No ns-scale or mask-compliance claim is supported.
- Both hosts carry uncompensated consumer-grade quartz (not OCXO/TCXO/Rb). The measured envelope is a worst-case consumer figure, not a telecom-class holdover curve.
- No PTP ran between the two machines. This measures the physical premise of B6 (two crystals diverge, by how much, how steadily); it is NOT an end-to-end B6 detection test.
- Temperature was not controlled. Without the temp log, the benign thermal-correlation discriminator in the Parameter Fault Matrix (L8 Oscillator: temperature) is not evaluated.

## Provenance

- laptopA: `laptopA_20261002-211329_92214ce7bb.csv` sha256 `37efb32541b9b64b...`
- laptopB: `laptopB_20261002-211401_5897fbe2bc.csv` sha256 `68155ad5830dc430...`
- Figure: `drift_pair.png`
