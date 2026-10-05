# S14 evidence verification and independent pre-action impact

Date 2026-09-13. Descriptive. Condition strings are **configured expectations**, never harm labels.
No numerical acceptance criterion is applied retrospectively to any S14 run.

## 1. Batch state and integrity (R4, R5)

The batch was **still writing** when this session began. It was allowed to finish; nothing was
stopped, edited or duplicated. It reached quiescence with 25 directories, all sealed.

| Check | Result |
|---|---|
| Run directories | 25 |
| Sealed and internally consistent | **25 / 25** |
| Retained with problems | 0 |
| Manifest entries rehashed against the files | **575** |
| Arms recorded in events.log | {'no_action': 20, 'action': 5} |

Every mandatory entry was present in every run, every run reached `phase_finished`, no `status=FAIL`
event was recorded, and both captures in every run decode to non-zero PTP records. This states that
the bytes are the sealed bytes. It states nothing about harmfulness, detector correctness or benefit.

## 2. An independent pre-action impact measure now exists

**What.** `ptp4l`'s own periodic servo summary reports `delay <mean> +/- <dispersion>` in
nanoseconds — the **receiver's** estimate of path delay and its variability, computed from its own
Sync/Delay_Req exchange.

**Why it is independent.** It is produced by ptp4l, not by the packet detector. The detector plays no
part in it.

**Why the timing is sound.** Servo lines and port-state transitions appear in the *same* ptp4l log,
so "before the action" is decided inside one timebase. **No mapping between ptp4l, capture and
detector clocks is assumed**, and no cross-clock duration is claimed anywhere in this document.

**What is excluded.** The action arm contributes **no** pre-action impact evidence: its later sample
straddles the commanded link-down, so it cannot evidence the condition before the action.
`jitter_fault_action` has 1 usable runs out of 5.

## 3. Receiver-measured values in the impaired window (microseconds)

| Configured condition | netem | runs used | path delay (min – max) | median | dispersion (min – max) | median |
|---|---|---|---|---|---|---|
| baseline_clean | none | 5 | 13.5 – 25.6 | 24.3 | 1.9 – 8.5 | 6.5 |
| benign_delay_jitter | 100us ± 20us | 5 | 95.5 – 106.6 | 97.5 | 17.7 – 24.6 | 19.5 |
| jitter_fault_no_action | 100us ± 200us | 5 | 86.9 – 124.3 | 103.5 | 33.3 – 56.2 | 53.8 |
| authorized_source_failover | none | 5 | 20.1 – 25.6 | 23.8 | 6.0 – 7.6 | 6.9 |

## 4. What separates, and what does not

| Comparison | measure | separable without overlap | margin |
|---|---|---|---|
| baseline vs jitter_fault_no_action | path delay | yes | 61.3 us |
| baseline vs jitter_fault_no_action | dispersion | yes | 24.8 us |
| **benign vs jitter_fault_no_action** | **path delay** | **NO — overlapping** | – |
| **benign vs jitter_fault_no_action** | **dispersion** | **yes** | **8.7 us** |
| baseline vs authorized_source_failover | path delay | no | – |
| baseline vs authorized_source_failover | dispersion | no | – |

Three things follow.

**4.1 Mean path delay cannot tell the two netem conditions apart.** Both are configured with the
same 100 us mean delay, and the receiver measures ~100 us in both. Only the **dispersion** separates
them, which is mechanistically coherent: the two conditions differ only in configured jitter.

**4.2 The "benign" condition is itself a measured departure from baseline.** Its receiver-measured
path delay is roughly four to five times baseline. `BENIGN_WITHIN_POLICY` is therefore a configured
expectation, not a measured boundary — precisely as the corrected policy requires it to be read.

**4.3 The authorized source failover produces no impact signal.** It is indistinguishable from
baseline on both measures, so it does not masquerade as a degraded path.

## 5. What this does and does not establish

**Establishes:** an independently measured, receiver-computed, pre-action protocol degradation that
tracks configured jitter, is separable from the benign condition without overlap, and is obtained
without any cross-timebase assumption and without the detector.

**Does not establish:** harm. No service requirement has been specified in this testbed against which
a path-delay dispersion could be judged harmful, so **harmfulness remains UNKNOWN**. A dispersion of
tens of microseconds is a measured degradation of the receiver's own delay estimate and nothing more.

**Also does not establish:** anything about the detector's accuracy. This measure was *derived from*
existing S14 data. Under the correction policy and ordinary practice, these runs therefore **cannot**
serve as independent validation of a decision rule built on them. Validation requires a new
prospectively frozen protocol — see `S15_INDEPENDENT_VALIDATION_PROTOCOL.json`.

**Scale limits:** one impaired-window servo sample per run, five runs per condition, one host, shared
software clock under `free_running 1`. This is a protocol-level estimate over software timestamps,
not a calibrated physical timing measurement.
