# Pilot evasion findings (reviewer-run, our own detector, feature-space)

Quick CPU pilot against OUR OWN pipeline (RF + group-wise open-set), small dataset (6 scenarios/type,
1 seed). Attacker = keep the clock broken (offset_abs_max >= 100 ns budget) while disguising the other
features. **These are feature-space results = an attacker-favorable UPPER BOUND**, not a realizable
deployment rate. Treat as a lead, not a conclusion.

## Numbers
| Attacker | Fooled the RF | Open-set caught those | Fully evaded (both layers) |
|---|---|---|---|
| Naive random (±25%, few features) | 0/60 = 0% | — | 0% |
| Guided (±80%, RF-important features) | 8/40 = 20% | 0/8 | 20% |
| Guided + push damage to the 100 ns boundary | 35/40 = 88% | 2/35 | **82%** |

## Why (diagnostic)
RF top features: `drift_vs_declared_state_residual` (0.23), `offset_abs_max` (0.11),
`msg_rate_std` (0.11), `msg_rate_mean` (0.09). The classifier does NOT key mainly on raw damage
magnitude — it keys on a consistency residual the attacker can shape. So an attack that crosses the
budget by a hair and disguises the consistency/message-rate features flips the label.

## The two real signals
1. Weak attacks fail (0%) — the detector is not trivially broken.
2. A guided, minimal-damage attacker evades BOTH the classifier and the open-set safety net at high
   rate in feature space. **The open-set net did not rescue it** (caught ~0–6%).

## Concrete lead for Codex (Steps 2–3)
- Focus perturbation on `drift_vs_declared_state_residual`, `msg_rate_std/mean`, `offset_step_vs_drift_ratio`.
- Use minimal-magnitude (boundary) attacks — hardest for the detector.
- The open-set layer is the weak point, not a backstop — test it explicitly.
- **Realizability is the open question:** must confirm these feature vectors correspond to REAL PTP
  packet sequences that still break the clock. The feature-space 82% will likely shrink under that
  constraint — measuring by how much is the actual contribution.
