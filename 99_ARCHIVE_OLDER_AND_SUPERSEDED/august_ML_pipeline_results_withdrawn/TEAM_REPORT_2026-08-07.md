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

The automated suite contains **56 passing tests** after the live-validation additions.

## What happened live

We ran the software against real PTP programs and Linux network impairments, not only recordings.

- The recommendation loop ran for **10 minutes** across delay variation, packet loss, and a holdover-style impairment. Average decision time was **0.081 seconds** and the slowest was **0.404 seconds**.
- Live management data made **10 of 28 features** change; packet captures made **14 of 28** change. SyncE quality and physical GNSS status still require real equipment.
- The longest uninterrupted normal session was **87.60 minutes**. The intended two-hour target was interrupted and is not claimed.
- Almost every normal software-timestamped window was marked unfamiliar because laptop/WSL timing was measured in microseconds, not the hardware target of about 100 nanoseconds. This formed one sustained operator alarm rather than thousands of separate alarms.
- A legitimate switch between two PTP masters was never called an attack. However, the session was already unfamiliar before the switch, so this does not prove the false-alarm rate on production timing hardware.
- Under severe loss, the PTP management tool sometimes reported zero timing values, and the detector treated those as healthy. **This has since been fixed** — see below.

## The one real bug we found, and how it was fixed

Live testing exposed a genuine safety flaw. When the network was badly degraded, the
timing tool returned nothing, our software substituted a zero, and a zero looks
exactly like *perfect* synchronisation. So the system reported "healthy" at the
precise moment it had gone blind — and worse, it skipped the entire "is this
unfamiliar?" safety layer on the way. An attacker could have triggered this
deliberately by flooding the link.

The same mistake existed in the digital twin: with no data at all, it reported
**maximum confidence** in its own predictions, which switched off the safeguard
that is supposed to force a cautious response when the twin can't be trusted.

The fix treats *missing data as its own state*, never as a number. The software now
tracks whether each measurement was genuinely observed, and refuses to declare
anything healthy unless it can prove it actually saw the data. Anything missing,
incomplete, or unverifiable is routed to the safe response instead.

| Situation | Before | After |
|---|---|---|
| No timing data received | "healthy" | "unknown" → safe response |
| Half the samples missing | "healthy" | "unknown" → safe response |
| Data with no proof of origin | "healthy" | "unknown" → safe response |
| Normal healthy traffic | "healthy" | "healthy" (unchanged) |
| Twin confidence with no data | 100% | 15% (correctly distrusted) |

Ten tests now lock this behaviour in. They were written *before* the fix and
confirmed to fail against the old code, so they test the actual bug rather than the
patch. Detection accuracy was unaffected (99.1%), and the suite grew to **56 tests**.

**We then proved it on real software, not just our own simulation.** We ran two real
PTP programs talking to each other over a virtual network link, let them synchronise,
then cut the link completely and killed the master clock.

This exposed something worse than the original bug. When the master vanished, the
timing tool did **not** report an error or a zero — it kept confidently reporting the
*last numbers it had seen*, indefinitely. Only one field, the port's connection state,
told the truth. Anything trusting the numbers alone would have believed the network
was fine throughout a total blackout, and those stale numbers look far more convincing
than a zero.

Our software reads that connection state rather than trusting the numbers, so it
caught both versions of the problem:

| Real test | What the system decided |
|---|---|
| Healthy, synchronised link | analysed normally, recommended a recovery action |
| Link cut, master gone | "unknown" → safe response, and it correctly refused to guess |

All four live network impairment scenarios (normal operation, delay variation, packet loss, and master clock outage) were run for 90 seconds each, capturing 5,665 real-world telemetry windows. Across 48 consecutive windows measured right after the master clock was killed, the system produced 47 "unknown" decisions and 1 pending decision awaiting voting — sending every single window to the conservative safe default with zero false "healthy" labels.

This closes the last open item from live testing.

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
- Public captures contain only a small number of independent attacks and no benign planned grandmaster change. A software failover was added, but its laptop timing distribution is not representative of production hardware.
- SyncE quality still needs a live `synce4l` or radio-unit telemetry feed.
- A model trained on one real attack style can fail completely on another style.
- These are research measurements, not telecom certification.
- The continuous baseline reached 87.60 minutes, not the two-hour target.

## Decision and next step

Software feature work is closed because further single-source features now give diminishing returns. The next valuable phase is Tier 3 hardware validation: authenticated GNSS, physical independent clocks, hardware timestamps, longer normal-operation recordings, and controlled authorized attacks.

This next phase also has the clearest application path: a vendor-neutral timing-security validation product for telecom labs, private 5G operators, and equipment vendors, with reproducible resilience tests and auditable recovery recommendations.
