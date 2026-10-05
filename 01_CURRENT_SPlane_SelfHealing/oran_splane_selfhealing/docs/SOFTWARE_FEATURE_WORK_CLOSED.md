# Software Feature Work Closed

## Decision

The shipped research prototype is frozen at **configuration C**: 28 timing, protocol, rate, BMCA, time-source, and oscillator-consistency features with group-wise open-set detection and 2-of-3 persistence. The seven cross-source research features remain reproducible but are disabled by default because they added no protection and regressed established families.

Further single-source feature engineering has reached diminishing returns. The next scientifically meaningful step is Tier 3 validation with independently trustworthy physical timing evidence.

## What worked

- **BMCA/grandmaster transition features:** relative identity churn, clock-class/priority transitions, and `stepsRemoved` behavior raised real unseen TIMESAFE Announce protection from 23.9% to approximately 100%. Raw grandmaster identity never enters the model.
- **Group-wise open set:** independent novelty detectors recovered unseen DoS from 0% to approximately 94% in the original ablation and materially improved replay protection. The combined Šidák budget limits known-window novelty rather than assigning one global threshold.
- **2-of-3 persistence:** real benign false positives fell from 4.49% to 2.37% without reducing the two-second real-episode deadline result.
- **Oscillator consistency:** declared-state/clock-behavior checks raised unseen GNSS jam protection from 0% to 91.57%, improved replay by 20.7 percentage points in that checkpoint, and produced zero closed-set GNSS confusion.

## What did not work

- **Receiver-reported GNSS status alone:** `gnss_sync_status` is attacker-controlled in the threat model. A spoofed receiver can report `SYNCHRONIZED`, so this channel reduced unseen-family protection to 0% instead of solving it.
- **Strict unseen GNSS spoof:** physics consistency still produced 0% protection. A spoof that preserves plausible disciplined behavior remains in-distribution in every single-reference feature group.
- **Cross-source feature group:** the research configuration added no incremental combined protection and regressed DoS and GNSS-jam results before gating. After deterministic isolation, configuration D remains below configuration C on the related-family single-source experiment. It is disabled by default.
- **Coherent all-source compromise:** relative agreement contributes 0.00 percentage points when all references share the same forgery. Agreement among compromised sources is not evidence of correct time.

## Three negative results

1. Self-reported receiver status is not independent evidence and can make unseen-family generalization worse.
2. Oscillator consistency detects out-of-envelope jamming but cannot identify a healthy-looking unseen spoof.
3. Simulated cross-source features add no incremental protection in the evaluated setup and can dilute established model behavior.

The multi-source run kept related GNSS families in training, so its 92.78% configuration-C single-source figure is RF transfer and is not comparable to the strict unseen-spoof result of 0%.

## Standing conclusion

With one trusted-time claim, a spoof that mimics healthy operation is in-distribution by construction. Detecting it requires evidence the attacked source cannot forge, such as cryptographic GNSS authentication (for example Galileo OSNMA), a physically independent clock, authenticated multi-constellation observations, or hardware-backed cross-checking with known failure independence.

That is a **hardware/Tier-3 question**, not another single-source feature-engineering task. Future work should prioritize hardware timestamps, real receivers and clocks, authenticated GNSS, live SyncE/O-RU telemetry, and controlled independent-reference experiments.

## Final shipped evidence

Under 2-of-3 persistence, the default configuration reproduces: simulated spoof 93.30%, replay 80.45%, DoS 88.27%, GNSS jam 91.57%; real TIMESAFE Announce 99.96%, Follow-Up 99.66%, and Single-Step 99.66%. Every listed family except strict unseen GNSS spoof is detected within the two-second episode window; strict unseen spoof remains 0%.
