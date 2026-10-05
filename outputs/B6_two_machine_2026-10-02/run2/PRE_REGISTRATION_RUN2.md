# Pre-registration — B6 paired oscillator measurement, RUN 2

**Session tag:** `run2` · Frozen 2026-10-02, before any run-2 data exists.
Supersedes the run-1 pre-registration for this run only; the run-1 document and
its result stand unaltered as the historical record.

## 1. Why there is a run 2

Run 1 (`run1`, 2026-10-02) returned **NOT ESTABLISHED**. Four of five criteria
passed. **C1 failed**: 348 and 658 retained samples against 600 required.

The cause was not the measurement and not the operators. It was rejection rule
R2 (non-modal NTP server) firing on a probe defect that had been **documented in
writing before run 1 was executed**: `drift_probe.py` v1 line 206 reassigned the
NTP server after any single failed sample. In practice it thrashed — 97 server
switches on arm A, 21 on arm B — so arm A's samples split almost evenly between
`time.google.com` (420) and `time.cloudflare.com` (415).

Run 1's measured value was **+20.161 ppm [19.376, 20.969]**, and a post-hoc
robustness check across server subsets gave +18.8 to +20.2 ppm. Run 2 is expected
to reproduce that. **If it does not, run 1's number is not thereby rescued and run
2's is not automatically preferred — both get reported.**

## 2. What changed, and what explicitly did NOT

**Changed — two things only, both in the probe:**

| # | Change | Justification |
|---|---|---|
| 1 | The reference is pinned. No mid-run server switching. A failed sample is recorded `ok=0` and the run continues on the same reference. | Removes the documented v1 defect that caused the C1 failure. The defect was recorded before run 1, so this is not a post-hoc rationalisation. |
| 2 | Duration 150 → 180 min (900 → 1080 samples). Strict startup: the probe refuses to start if the agreed reference is unreachable over NTP, unless `--allow-fallback` is passed explicitly. | Sample margin, and prevention of a silent reference mismatch that cannot be detected until analysis hours later. Adding data cannot bias a result. |

**NOT changed — stated explicitly so it cannot be claimed later:**

- **Every acceptance criterion C1–C5 is byte-identical to run 1.** C1 remains
  ≥ 600 retained samples per arm. It was *not* lowered to fit run-1 data.
- **Every rejection rule R1–R4 is unchanged**, including the R3 RTT rule
  (median + 3·MAD, hard cap 1 s) which dropped 72 and 82 samples in run 1.
- **`pair_drift.py` is unchanged**, hash still
  `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8`. The
  analysis that failed run 1 is the same analysis that will judge run 2.

This is the distinction the project's S15 precedent turns on: fixing an
instrument defect is legitimate; moving a criterion to fit the data is not.

## 3. Verification performed before freezing

`selftest_probe_v2.py` — **24 assertions, all pass**:

- Strict startup refuses to run when the agreed server is unreachable, exits
  rc=2, writes no CSV, and tells the operator to use a hotspot.
- `--allow-fallback` still works when explicitly requested and warns loudly.
- **Key test:** under a simulated 30% sample-failure rate, exactly one server
  appears across every row; failures are recorded `ok=0` with no offset; sample
  indices stay contiguous; meta counts match the CSV.
- CSV header byte-identical to v1, so the frozen analyser reads it unchanged.
- Metadata records `schema: oran-splane-drift-probe/2`, `reference_pinned: true`,
  `mid_run_server_switching: false`, `strict_server: true`.

End-to-end chain test, simulating v2 arms at a known −4.2 / −24.35 ppm with
realistic failure rates (11% arm A, 3% arm B) and run-1's measured RTTs:

```
laptopA: -4.191 ppm   920/1080 retained
laptopB: -24.341 ppm  993/1080 retained
RELATIVE: +20.150 ppm [+20.062, +20.235]     (truth +20.150)
C1 PASS 920/993 · C2 PASS · C3 PASS · C4 PASS 100%/100% · C5 PASS 0.086 ppm
VERDICT: ESTABLISHED
```

Projection from run-1's own failure counts (97 and 21 server failures, which
under v2 become recorded failures rather than switches): roughly **860 and 930
retained** against the 600 required. The margin is wide, not marginal.

## 4. Freeze record — run 2

| Artefact | SHA-256 |
|---|---|
| `drift_probe.py` (v2) | `0f5c04b7268425419c8466208d6f00276bc8093a078ee60beb018156dd94f593` |
| `check_setup.py` (v2) | `aebf8af7e0100ee4e96e205090160c4553bc81cfe1a95f08b6684102aee7e19e` |
| `1_CHECK_FIRST.bat` | `f90e3f24934dfa1da6ccee6814f2aa31851bd2f066a2e43a40e81edac9d22393` |
| `2_RUN_MEASUREMENT.bat` (v2) | `0ce449d52464ee0305b033c796d0f981df919d5884fe482ee6d24a94c008128a` |
| `temp_log.py` (unchanged) | `a1ba66f4738c6fe888d6d9bd6d88c9b1d2324cde9072af4501a0a8c54beba2cb` |
| `README.txt` (v2) | `7a3afb0edb41d969ff0efebe71cafac42b18de42ba3bb15147d063b41a660f69` |
| `pair_drift.py` (**unchanged from run 1**) | `7518898ce878a7c4985506b229212b141f815103cd742c8393a4fa0fec573cb8` |

Verify on both machines before starting:
`Get-FileHash -Algorithm SHA256 .\drift_probe.py`

Frozen at (UTC): ______________________

## 5. Acceptance criteria — IDENTICAL to run 1

| ID | Criterion |
|---|---|
| C1 | Each arm retains ≥ 600 samples after rejection |
| C2 | Common overlap ≥ 120 min |
| C3 | Zero discontinuities in either retained series |
| C4 | Both arms on the same reference, ≥ 95% homogeneous, same server |
| C5 | Relative-offset 95% CI half-width < 1.0 ppm |

ESTABLISHED only if all five pass. Any failure yields NOT ESTABLISHED and the
report refuses to promote a headline number, exactly as in run 1.

## 6. Procedure

1. Both arms: extract to Desktop, verify `drift_probe.py` hash against §4.
2. Both arms: `python check_setup.py`. Require **READY** and `time.google.com OK`.
   A NOT REACHABLE result means switch to a phone hotspot — the run will refuse
   to start otherwise, by design.
3. Both arms: plug in; sleep = Never; `powercfg /change standby-timeout-ac 0`.
4. Agree start time. Both start within 10 minutes. Tag `run2`, labels
   `laptopA` / `laptopB`. 180 minutes.
5. Arm A additionally: `temp_log.py` in a second window (optional on arm B).
6. Analyse with the unchanged `pair_drift.py --session run2`.
7. Record the verdict exactly as returned.

## 7. What run 2 still does NOT establish

Unchanged from run 1 §7, repeated so it cannot quietly widen:

1. **Not an end-to-end B6 detection test.** No PTP runs between the machines; the
   detector never sees this drift. It measures B6's physical premise only.
2. **No ns-scale or mask-compliance claim.** Floor is milliseconds, ~10⁵ above
   G.8273.2 cTE (50/20/10 ns). Run 1 was floor-limited (ADEV ∝ τ⁻¹ throughout,
   short-τ slope −0.786, no crossover), so it resolved frequency *offset* only
   and not oscillator *instability*. Run 2 is not expected to change that: the
   limit is the NTP-over-WiFi path, not the duration.
3. **Not telecom-grade oscillators.** Consumer quartz, not OCXO/TCXO/Rb.
4. **Temperature uncontrolled**, and unreadable without privilege on arm A in
   run 1. The thermal-correlation discriminator may remain unevaluated.
5. **Does not unlock B1, B4, A6 or A7**, and adds no hardware timestamping.
6. `ORAN_Fault_Detectability_v2026-09-29.xlsx` row B6 is not changed by this run.
