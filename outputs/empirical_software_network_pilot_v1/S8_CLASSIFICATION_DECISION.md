# S8 — Evidence-supported classification decision

Date 2026-09-13. Sources: `V4_BROADER_EVALUATION.json` (primary), `V3_NONOVERLAPPING_EVALUATION.json`
(prior, independent batch). Detector and thresholds frozen and hash-verified in both.

## 1. What the detector actually outputs

The frozen engine emits packet-level classifications and, separately, independent events. It never
emits health, attack, outage or recovery labels. The two channels are:

- **Dispersion channel.** Disjoint blocks of 8 consecutive Sync-to-Follow_Up arrival gaps per source
  context. A block whose standard deviation reaches 0.00016 s is a high-dispersion block; two such
  blocks within 3.0 s produce `NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED`.
- **Source-silence channel.** `SOURCE_ANNOUNCE_SILENCE_OBSERVED` when a previously seen Announce
  source has been silent for 0.75 s, deduplicated, with a reappearance event if it returns.

These are independent. A run can produce either, both, or neither.

## 2. Which conditions CAN be classified

**Configured netem delay+jitter+loss versus every non-loss condition tested.**

| Batch | impairment k/n | Wilson 95% | non-impaired k/n | Wilson 95% |
|---|---|---|---|---|
| V3 | 5/5 | [0.5655, 1.0000] | 0/10 | [0, 0.2775] |
| V4 | 5/5 | [0.5655, 1.0000] | 0/20 | [0.0000, 0.1611] |

Two independently frozen batches, 10 impairment runs and 30 non-impaired runs in total, with no
observed overlap. V4 added the condition V3 lacked: benign delay and jitter with no configured loss,
which produced 0/5.

**Authorised source termination.** The silence channel fired in 5/5 termination runs and 0/20
elsewhere, in V4. It reports that a source stopped announcing. Nothing more.

## 3. Which conditions CANNOT be classified

- **Loss versus delay versus jitter.** The impairment condition (delay 1000us, jitter 200us, loss 1%)
  and the benign condition (delay 100us, jitter 20us, no loss) differ in **three parameters at once**.
  The observation tracks the package, not an identified cause. This is the single largest open item
  and is addressed by the pre-registered V5 protocol.
- **Source loss versus attack.** An authorised, operator-initiated termination is not an attack. The
  testbed contains no adversary and V4 makes no attack claim.
- **Receiver harm.** No condition in V3 or V4 demonstrated receiver impact. An injected condition is
  not demonstrated harm.
- **Clock health or timing quality.** Endpoints share one host software clock under free_running 1.
  Packet-arrival dispersion is not a referenced receiver clock-error measurement.
- **Recovery.** No action was executed in any run. Nothing here supports a recovery claim.

## 4. False alarms and misses, as observed

- **Misses (impairment present, not observed):** 0 of 10 across V3 and V4.
- **False observations (non-impaired run producing persistence):** 0 of 30 across V3 and V4.
- **Near-misses that the persistence rule suppressed:** isolated single high-dispersion blocks
  occurred in 3 of the 20 V4 non-impaired runs (one baseline, one benign delay+jitter, one
  no-action control). None met the 2-blocks-within-3.0-s condition. A single-block rule would have
  produced 3 false observations. The persistence requirement is load-bearing, not decorative.
- **Invalid input handling:** 5 of 16,976 V4 records were rejected as arrival-order regressions and
  excluded from blocks. They neither crashed the engine nor silently entered a block.

## 5. Operating limits of any claim built on this

1. n=5 per condition per batch. Wilson intervals are wide; these are feasibility repetitions.
2. Both batches ran in one isolated software environment on one host. No hardware, no second host,
   no independent clock, no traffic load variation, no topology variation.
3. Capture duration was 8 s per phase. Detection at 5.45-8.88 s means the observation is near the
   end of the available window; a shorter phase might not contain two qualifying blocks.
4. The 0.00016 s threshold, block size 8, count 2 and window 3.0 s are chosen laboratory settings.
   No standard mandates them and no physical calibration supports them.
5. Condition labels were used only to group runs for reporting. They were never detector inputs.

## 6. Decision

The dispersion-persistence observation is **accepted as a repeatable software observation** under the
frozen conditions tested, in two independent pre-registered batches. It is **not accepted** as a
detector of packet loss, of attack, of receiver harm, or of any physical timing condition, and it
does not authorise a recovery loop.

Any future revision of the threshold, block rule, or condition set requires a new development
version and a fresh held-out validation batch. V5 below is that next batch and is frozen before any
capture.


---

# AMENDMENT 1 — 2026-09-13, after V5

This amendment is required by `V5_SINGLE_VARIABLE_EVALUATION.json`. It changes two conclusions above.

## A1.1 The observation is attributable to JITTER MAGNITUDE, not to packet loss

V5 varied one netem parameter at a time from a common benign reference. Verified qdisc lines confirm
each arm changed exactly one parameter.

| Arm | change from reference | k/n | Wilson 95% |
|---|---|---|---|
| A reference benign | none | 0/5 | [0.0000, 0.4345] |
| B loss only | + 1% loss | 0/5 | [0.0000, 0.4345] |
| C jitter only | jitter 20us -> 200us | 3/5 | [0.2307, 0.8824] |
| D delay only | delay 100us -> 1000us | 0/5 | [0.0000, 0.4345] |
| E full impairment | all three | 3/5 | [0.2307, 0.8824] |

Pre-specified branch selected: `if_only_C_and_E_positive` - the observation is attributable to
configured jitter magnitude. Adding 1% loss alone produced nothing. Raising mean delay tenfold alone
produced nothing. Section 3 above, which listed loss attribution as unresolved, is resolved: **it is
not loss.** Any wording anywhere in this project that describes this as loss detection is wrong.

## A1.2 The observation is LESS repeatable than V3 and V4 indicated

Arm E is the identical condition V3 and V4 called the impairment condition, run under the identical
frozen detector.

| Batch | k/n |
|---|---|
| V3 | 5/5 |
| V4 | 5/5 |
| V5 arm E | 3/5 |
| **pooled** | **13/15, Wilson 95% [0.6212, 0.9626]** |

Section 6 above accepted the observation as "a repeatable software observation". That wording is
**too strong** and is hereby narrowed: under the identical configured condition the observation
appears in roughly 86 percent of runs, not in every run. The V4 result of 5/5 was optimistic; a
5-run batch cannot distinguish 1.0 from 0.6. Sensitivity is materially below what a detector claim
would require, and no sensitivity figure from a single batch should be quoted again.

## A1.3 What does not change

Specificity remains strong: 0/15 across the three V5 negative arms, on top of 0/30 across
V3 and V4 non-impaired runs. Zero false observations in 45 non-jitter runs.
The source-silence channel is unaffected; V5 contained no termination arm.
