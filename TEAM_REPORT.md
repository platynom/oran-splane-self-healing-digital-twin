# Team Report: Self-Healing O-RAN Timing Security

This report explains the project in plain language. No telecom or machine
learning background is required.

## What problem are we solving?

A 5G radio network needs its computers and radio units to agree on time with
extreme precision, roughly within 100 nanoseconds. The network distributes time
using PTP, SyncE, and satellite-based GNSS timing. A fault or deliberate timing
attack can disrupt a base station in about two seconds.

Most security systems stop after saying, "something is wrong." This project
continues the process: it estimates whether the event is an ordinary fault, a
known attack, or something unfamiliar; tries recovery choices in a digital
twin; and selects a safe action before the failure window closes.

## What did we build?

The software runs on a normal laptop and includes:

1. A simulator for clocks, network delay, PTP, SyncE assistance, GNSS loss, and
   clock holdover.
2. Benign-fault and attack scenarios, including spoofing, replay, and message
   flooding, plus benign look-alikes that make the tests harder.
3. A detector using **19 measurements**, or features. These include clock error,
   delay variation, message order and rate, and changes in the advertised PTP
   grandmaster.
4. An open-set safety layer. If an event does not resemble known faults or
   attacks, it is labelled UNKNOWN and sent to a conservative response.
5. A digital twin that forecasts whether each recovery choice can keep timing
   within budget.
6. A governed healing loop that records why an action was chosen.

The open-set layer is split into timing, protocol, message-rate, and
grandmaster/BMCA groups. Each group has its own novelty detector, and a weighted
Šidák budget limits their intended combined false-alarm rate. Grandmaster
identity itself is not used as a model input; only changes and plausibility
signals are used, which reduces the risk of memorizing a capture file.

## Why require two votes out of three?

One unusual 0.2-second window can be noise. The current setting requires at
least two positive votes among the latest three windows before declaring an
UNKNOWN event or known attack. This **2-of-3 persistence** roughly halves the
real benign false-positive rate while adding only 0.2-0.4 seconds of average
decision delay.

## Current measured results

"Combined protection" means the system either recognizes an attack or admits
that it is unfamiliar and chooses the safe path.

| Test data | Attack type hidden during training | Combined protection |
|---|---|---:|
| Simulator | Spoof | 83.8% |
| Simulator | Replay | 63.7% |
| Simulator | Message-flooding DoS | 86.0% |
| Public TIMESAFE captures | Announce/grandmaster attack | 99.96% |
| Public TIMESAFE captures | Sync/Follow-Up attack | 99.66% |
| Public TIMESAFE captures | Single-step Sync attack | 99.66% |

On the real TIMESAFE captures:

- benign false positives are **2.37%**, down from 4.49% without persistence;
- every evaluated real attack episode is detected within **0.2 seconds**;
- the worst result across all real and simulated families is **91.7% of attack
  episodes acted on within two seconds**.

The 91.7% case is simulated spoofing. One simulated run is already detected too
late without persistence, so the two-vote rule does not make its two-second rate
worse.

## What does "alarms per hour" mean?

There are two useful counts:

- **Persisted windows/hour** counts every positive 0.2-second window. A long
  event may therefore be counted many times.
- **Operator alarm episodes/hour** combines consecutive positive windows into
  one alarm.

On the short held benign TIMESAFE recordings, 2-of-3 persistence reduces the
weighted window count from about 807 to 427 per hour. After de-duplication, the
operator-facing estimate falls from about 570 to 190 alarm episodes per hour.
These are extrapolations from short recordings, not measurements from a
day-long live network, so they should be treated as comparative research
figures rather than expected production alert volumes.

## How realistic is the evidence?

- **Simulator:** synthetic timing physics and labels, repeatable on a laptop.
- **Linux/netem:** real Linux PTP packets over an emulated impaired network.
- **TIMESAFE:** previously recorded PTP attacks from a public university
  testbed, with complete capture sessions kept separate between training and
  testing.
- **Hardware:** not tested yet.

The project currently has **28 passing automated tests** and a one-command
workflow that rebuilds the dataset, models, digital twin, benchmark, and reports.

## Honest limitations

1. TIMESAFE has no benign session where the legitimate grandmaster changes.
   False positives during planned network re-parenting may therefore be higher
   in deployment than this evaluation suggests.
2. A conventional classifier trained on Announce attacks and tested on Sync
   attacks has **0% recall**. The UNKNOWN safety path protects many unseen
   events, but it does not mean the classifier understands every attack family.
3. SyncE quality cannot be recovered from a normal packet capture. It still
   needs a live `synce4l` feed or synchronization data from a real radio unit.
4. The public evaluation has only a few independent attack recordings.
5. No PTP hardware-timestamping card, physical clock, O-DU, or O-RU has been
   tested. This is a research prototype, not a certified telecom product.

## What comes next?

The highest-value next step is a longer live Linux and hardware study: collect
normal traffic over hours or days, include legitimate grandmaster changes, read
SyncE quality in real time, and then repeat the attack and recovery evaluation
with hardware timestamps and representative O-RAN equipment.

## Bottom line

The software contribution is complete enough to reproduce and evaluate on a
laptop. It now handles known attacks, novel attacks, grandmaster manipulation,
and noisy one-window decisions more safely than the earlier detector-only
version. The remaining gap is external validity: longer independent captures,
live SyncE, and real timing hardware.
