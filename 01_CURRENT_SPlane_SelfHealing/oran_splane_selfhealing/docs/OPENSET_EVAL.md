# Open-Set / Novelty Evaluation

Isolation Forest is fitted only on known-family training data. A held-out attack is protected when the RF predicts H1 or the novelty detector routes it to UNKNOWN and `safe_default`.

Configured known-window novelty budget: 2.0%.

| domain | held-out family | attack windows | RF-only recall | novelty rate | combined protective rate | benign novelty false alarm |
|---|---|---:|---:|---:|---:|---:|
| simulated | spoof | 179 | 0.894 | 0.553 | 0.972 | 0.021 |
| simulated | replay | 179 | 0.430 | 0.212 | 0.525 | 0.017 |
| simulated | dos | 179 | 0.000 | 0.944 | 0.944 | 0.017 |
| timesafe_real | announce | 6959 | 0.238 | 0.001 | 0.239 | 0.022 |
| timesafe_real | sync_follow_up | 298 | 1.000 | 0.000 | 1.000 | 0.000 |
| timesafe_real | sync_single_step | 298 | 1.000 | 1.000 | 1.000 | 0.019 |

Local TIMESAFE session derivatives were available and evaluated with complete capture isolation.

Unseen simulated DoS improves from 0.0% RF-only recall to 94.4% combined protective coverage. Real held-out Announce changes only from 23.8% to 23.9%, so open-set scoring does not resolve that domain-specific generalization gap. The attack remains in-distribution in the current timing-dominated feature space; BMCA signals such as grandmaster identity changes, priority transitions, clock-class transitions, and steps-removed shifts are needed to make the attack observable.

The 100% novelty rate on the real single-step Sync capture may include a session-level distribution shift rather than attack-specific detection and requires a capture-normalization sanity check. Combined protective rate is a defensive-routing metric, not proof of correct attack-family classification.
