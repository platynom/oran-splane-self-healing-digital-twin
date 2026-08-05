# Team Report: Self-Healing O-RAN Timing Security

## The problem

A 5G radio network needs its computers and radios to agree on time within roughly 100 nanoseconds. Faulty or malicious timing can disrupt service in about two seconds.

This project does more than raise an alarm. It estimates whether the event is a normal fault, a known attack, or something unfamiliar; checks recovery choices in a digital twin; and selects a conservative action before the deadline.

## What we built

The project runs on a normal laptop and includes:

1. A repeatable simulator for PTP, SyncE, GNSS, clock holdover, delay, and oscillator behavior.
2. Benign faults and attacks with realistic look-alike scenarios.
3. A **28-feature** detector covering timing, network behavior, PTP grandmaster changes, receiver status, and oscillator consistency.
4. A novelty layer that sends unfamiliar events to a safe default.
5. A two-out-of-three voting rule that ignores isolated noisy windows.
6. A digital twin that compares recovery choices before the system acts.
7. Real packet-capture readers, public TIMESAFE evaluation, and a Linux PTP/netem test harness.

The automated suite contains **39 passing tests**.

## Final measured results

"Protection" means the attack was recognized or safely treated as unfamiliar.

| Test | Protection | Detected within 2 s |
|---|---:|---:|
| Simulated spoof | 93.30% | 100% |
| Simulated replay | 80.45% | 100% |
| Simulated message-flood DoS | 88.27% | 100% |
| Simulated GNSS jamming | 91.57% | 100% |
| Strict unseen healthy-looking GNSS spoof | 0.00% | 0% |
| Real TIMESAFE Announce attack | 99.96% | 100% |
| Real TIMESAFE Follow-Up attack | 99.66% | 100% |
| Real TIMESAFE Single-Step attack | 99.66% | 100% |

Requiring two positive windows out of three reduced real benign false alarms from **4.49% to 2.37%** without costing the two-second deadline.

## What worked

- Watching how PTP grandmaster attributes change raised real Announce-attack protection from 23.9% to almost 100%.
- Separate novelty detectors recovered attacks that the ordinary classifier missed, especially message flooding and replay.
- The two-out-of-three rule reduced noisy alarms.
- Comparing reported GNSS state with physical oscillator behavior solved most unseen GNSS jamming.

## What did not work

- A GNSS receiver saying it is synchronized cannot be trusted by itself. A spoofed receiver can still report healthy status.
- A spoof that behaves exactly like healthy timing remained invisible when its family was strictly excluded from training.
- Adding simulated comparisons among GNSS, network PTP, and a peer source did not improve total protection and made some established results worse. Those seven experimental features are kept for research but are switched off by default.
- If every time source is compromised in the same way, they still agree with one another. Relative agreement adds **0.00 percentage points** in that case.

The multi-source experiment kept related GNSS attacks in training, so its high configuration-C single-source result does not overturn the strict 0% unseen-spoof result.

## What this means

Software can detect protocol manipulation, unfamiliar traffic, timing jams, and many physics inconsistencies. It cannot prove that a single healthy-looking clock is telling the truth when no independent trusted reference is available.

Solving that last problem requires something the attacker cannot forge, such as authenticated GNSS signals like Galileo OSNMA, a physically independent clock, or hardware-backed comparison between genuinely independent references.

## Honest limitations

- No hardware timestamp card, real clock, authenticated GNSS receiver, O-DU, or O-RU has been tested.
- Public captures contain only a small number of independent attacks and no benign planned grandmaster change.
- SyncE quality still needs a live `synce4l` or radio-unit telemetry feed.
- A model trained on one real attack style can fail completely on another style.
- These are research measurements, not telecom certification.

## Decision and next step

Software feature work is closed because further single-source features now give diminishing returns. The next valuable phase is Tier 3 hardware validation: authenticated GNSS, physical independent clocks, hardware timestamps, longer normal-operation recordings, and controlled authorized attacks.

This next phase also has the clearest application path: a vendor-neutral timing-security validation product for telecom labs, private 5G operators, and equipment vendors, with reproducible resilience tests and auditable recovery recommendations.
