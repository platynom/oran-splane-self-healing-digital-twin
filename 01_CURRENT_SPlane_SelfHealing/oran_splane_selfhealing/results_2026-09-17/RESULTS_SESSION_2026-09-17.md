# S-Plane Attack-vs-Benign — Validated Results (session 2026-09-17)

Generated 2026-09-17T06:34:46.113821Z. Decision rule frozen at 2026-09-17T04:49:33Z; 18 artefacts SHA-256 hashed; verify_frozen passed before every run.

## 1. Randomised validation campaign (the headline)

- Admissible replicates: [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41]
- **Sensitivity (attack recall):** 1.000 [0.940, 1.000]  (TP=60 FN=0)
- **Specificity, decidable-benign:** 0.800 [0.682, 0.882]  (TN=48 FP=12)
- **Abstention correctness (ambiguous benign -> UNKNOWN):** 1.000 [0.757, 1.000]  (correct=12 over-claim=0 false-alarm=0)
- **Attack attribution (correct fault id):** 0.817 [0.701, 0.894]
- Per-fault attribution: A1=8/12  A2=12/12  A3=12/12  A5=12/12  A8=5/12

Key difference from the prior session: every replicate now uses randomised attacker
identities, priorities, timings and burst sizes (run/randparams.py, seeded by rep), so the
runs are genuinely independent and the CIs are honest rather than optimistic.

## 2. Cross-domain validation on REAL TIMESAFE hardware captures

The frozen rule (built only on the software testbed) applied to real hardware attack
captures it never saw:

- **5/6 detected by standards/protocol rules ALONE** (no allow-list, nothing fitted):

  - `2024-10-16-announce_attack` (81969 Announce): YES  — IEEE1588 Table5 clockClass<6 x24653; G.8275.1 priority1!=128 x24653
  - `15min_announce_attack` (15104 Announce): no (needs provisioned context)
  - `prod_successful_announce_attack_ptp` (1964 Announce): YES  — IEEE1588 Table5 clockClass<6 x39
  - `2024-10-08-announce_attack_1` (1688 Announce): YES  — IEEE1588 Table5 clockClass<6 x457; G.8275.1 priority1!=128 x457
  - `2024-10-08-sync_attack_1` (622 Announce): YES  — IEEE1588 sequenceId regression x2500
  - `2024-10-08-sync_attack_singlestep_1` (730 Announce): YES  — IEEE1588 sequenceId regression x2455

The single miss is a *healthy-looking spoof* (conformant fields, no sequence regression) —
the theoretically-predicted hard case; it requires provisioned context. Reported, not hidden.

## 3. Conformance-negative tests (Class-A, standards-defined pass criteria)

- 7/7 pass, each firing on its own cited clause (IEEE 1588 Table 5, G.8275.1 priority1, UNH PWR.c.2.4/c.2.5, domain/multicast).

## 4. Honest limitations (unchanged rule, reported not patched)

- **B_bc_replacement -> ATTACK (false positive).** The frozen context schema supports a
  single `expected_bc_identity`; a *provisioned* BC swap cannot be expressed, so it is
  flagged as a rogue BC (A8). All decidable-benign specificity failures are this one
  scenario. Fix = BC allow-LIST; requires re-freeze + re-run -> future work, NOT folded in.
- Software timestamping (us floor), shared kernel clock (no independent-clock/oscillator
  faults), no GNSS/SyncE. Hardware-dependent faults isolated and left, per instruction.
- Self-authored attacks; provisioned allow-list handed to the rule (narrows the claim to
  'detect unprovisioned/non-conformant clocks', not 'from traffic alone').
