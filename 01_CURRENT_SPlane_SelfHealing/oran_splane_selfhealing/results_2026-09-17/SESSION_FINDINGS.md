# Session 2026-09-17 — execution findings (running record)

## Config defects fixed PRE-FREEZE (verified, not judgement calls)
1. `dataset_comparison G.8275.x` was MISSING from cfg -> linuxptp ran the IEEE-1588 DEFAULT
   BMCA, not the G.8275.1 ALTERNATE BMCA. Cross-checked against linuxptp v4.0's own
   configs/G.8275.1.cfg. A capture cannot reveal this (BMCA algo is not a wire field), so the
   prior "verified by parsing its own capture" could not have caught it. FIXED.
2. `path_trace_enabled 1` -> removed. Real TIMESAFE captures have ZERO TLVs in 522,731 pkts;
   leaving it on makes PATH_TRACE presence a perfect testbed-vs-TIMESAFE separator (4th
   provenance leak, same class as the 16x cadence confound). Caught pre-run by run/leak_check.py.
3. Per-node configs (gma/gmb/bc/ru1..3) were REFERENCED but ABSENT from the tarball -> the
   testbed could not be rebuilt from it. Added run/mkcfg.sh generator (scoping verified against
   linuxptp v4.0 config.c: clientOnly=global, serverOnly=per-port).

## New provenance leak found by run/leak_check.py (systematic generalisation of the audit)
- `minor_version_ptp`: testbed(4.0)=1, real TIMESAFE=0. Compile-time constant in linuxptp 4.0
  (msg.h PTP_MINOR_VERSION), NOT config-fixable. Verified constant=0 across ALL sources in the
  real capture INCLUDING the attacker -> pure apparatus artifact, no attack signal. Decision
  rule confirmed NOT to use it. Must be excluded from any testbed+TIMESAFE join.

## Rule extended PRE-FREEZE (Class-A legality, each verified to fire on its own clause)
- stepsRemoved>=255 discard (UNH PWR.c.2.4) and alternateMasterFlag (UNH PWR.c.2.5) added.
- run/conformance_neg.py: 7/7 pass, each firing on its cited standard clause (fixture bug that
  made 5/6 fire on a spurious sequenceId collision was found and fixed first).

## Cross-domain validation on REAL TIMESAFE hardware captures (frozen rule, never trained on them)
- 5/6 captures detected by STANDARDS/PROTOCOL rules ALONE (no allow-list, nothing fitted):
    2024-10-16    : clockClass<6 x24653 AND priority1!=128 x24653  (IEEE1588 Table5 / G.8275.1)
    prod_success  : clockClass<6 x39
    announce_1    : clockClass<6 x457 AND priority1!=128 x457
    sync_1        : sequenceId regression x2500 (median -70, max -596; attack-window; NOT reorder)
    sync_singlestep: sequenceId regression x2455
- 1/6 (15min_announce_attack): a "healthy-looking spoof" - conformant priority1/clockClass, no
  sequence regression. NOT caught by standards alone; needs the provisioned allow-list. This is
  exactly the theoretically-predicted hard case (catalogue gap: "healthy-looking spoof is
  indistinguishable by attribute inspection alone"). Honest boundary, reported as such.

## LIMITATION discovered in the randomised campaign (rep30) - NOT patched into the frozen result
- B_bc_replacement -> ATTACK/A8 (false positive). The frozen context schema has a single
  `expected_bc_identity`; a PROVISIONED BC swap cannot be expressed, so a legitimate replacement
  is indistinguishable from a rogue BC. Kept as a pre-registered specificity FP (honest). The
  rule was NOT modified to make it pass. Fix (BC allow-LIST) needs re-freeze + re-run -> future
  work, reported separately, never folded into the primary number.
- B_unplanned_failover -> UNKNOWN (correct abstention): GM crash with no maintenance window is
  packet-indistinguishable from a suppression attack; the rule correctly refuses to guess.
