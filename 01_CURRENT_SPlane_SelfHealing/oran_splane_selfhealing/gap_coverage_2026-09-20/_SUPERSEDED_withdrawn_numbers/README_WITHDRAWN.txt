WITHDRAWN 2026-09-20 (late).

The results in these folders are NOT valid and must not be cited.
An audit found four defects in the same day's work, two of which fabricated data:
  * 36 "replicates" were one stale capture copied 12 times (exec-bit bug + silenced exit 126).
  * B3_pdv_congestion never injected anything (no sch_netem; failure swallowed by 2>/dev/null||true).
  * decision_rule_v2 false-positived on upstream captures.
  * the evaluator pooled run-count-dependent metrics.

Superseded by: ../corrected_final/  and ORAN_SPlane_AUDIT_AND_CORRECTIONS_2026-09-20.pdf
