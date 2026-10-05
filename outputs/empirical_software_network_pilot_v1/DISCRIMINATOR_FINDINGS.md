# Superseded exploratory report — see `CURRENT_ACCEPTANCE_LEDGER.md`

The legacy 96.875% result below is an offline, post-selection leave-one-run exploration, not live-loop or held-out performance. Its reported finite Monte Carlo `p = 0.0000` is not valid; use `(b+1)/(B+1)` with documented exchangeability. The causal replacement is `streaming_discriminator_v1.py`; no detector performance is yet established.

# Empirical Network Impairment and Source Loss Discriminator Findings

## Part 1: Mandatory Scope and Governance Declarations

> [!IMPORTANT]
> **Mandatory Scope and Governance Disclaimer**:
> 1. This evaluation detects a **CONFIGURED SOFTWARE IMPAIRMENT** (Linux kernel `netem` delay, jitter, and loss on an emulated link) and an **AUTHORISED, OPERATOR-INITIATED TIMING SOURCE TERMINATION** (`SOURCE_LOSS`).
> 2. It is **NOT an attack**, and nothing here establishes attack detection, clock health, physical timing quality, or recovery.
> 3. All analytical models operate strictly at Layer L5 (classification predictions out-of-sample) and must never be conflated with Layer L8 (physical outcome measurements).
> 4. An operational manipulation check is **never reported as an anomaly detection capability**.

---

## Part 2: Two-Class Configured Impairment Evaluation

### 1. Operational Scope and Sample Counts
- **Unit of Analysis**: 1 run
- **Positive Class**: `netem_delay_jitter_loss` (n = 8 runs across Set 2 and Set 3)
- **Negative Class**: `baseline_control` and `authorized_source_change_no_action_control` (n = 16 runs across Set 2 and Set 3)
- **Total Sample Size**: N = 24 matched runs evaluated under leave-one-run-out cross-validation
- **Class Imbalance**: Negative-to-positive ratio is 16:8 (16 unimpaired vs 8 impaired runs)
- **Anti-Circularity Architecture**: Ground truth class assignment is fixed by the experiment configuration and confirmed independently by physical kernel `tc -s qdisc` packet drop telemetry (`qdisc_after.txt`). The feature extractor operates solely on raw bytes read from anonymous binary stream objects with explicit programmatic assertions failing loudly if directory or scenario tokens are present.

### 2. Manipulation Check vs. Detection Features
A rigorous evaluation must distinguish between validating that an injection occurred and detecting its network delivery consequences.

- **Manipulation Check (`missing_master_to_slave_seq_count`)**: Direct tally of 16-bit PTP sequence ID gaps across the `$SR` bridge-to-slave interface.
  - Positive class (netem): n = 8, min = 11, median = 19.0, max = 21 dropped frames.
  - Negative class (unimpaired): n = 16, min = 0, median = 0.0, max = 0 dropped frames.
  - Separation margin: 11 frames.
  - *Technical Caveat*: Separating runs by counting the packets the injection intentionally removed confirms that `tc netem loss 1%` was active and delivered to the egress queue. It is an operational delivery confirmation, **NOT** evidence of an anomaly detector.

- **Detection Features (Honest Separation Margins and Medians)**:
| Detection Metric | Role | Lowest Pos Minus Highest Neg (Margin) | Ratio of Class Medians (Pos / Neg) | Impaired Netem Median (n=8) | Unimpaired Median (n=16) | LOO Accuracy | Permutation p-value (N=1000, seed=42) |
|---|---|---|---|---|---|---|---|
| `sync_fu_paired_delay_std_s` | DETECTION_FEATURE | **183.26 us** | **6.59x** | 263.75 us | 40.03 us | 100.0% | p = 0.0000 |
| `sync_interarrival_jitter_s` | DETECTION_FEATURE | **77.52 us** | **2.14x** | 261.58 us | 122.32 us | 100.0% | p = 0.0000 |

---

## Part 3: Three-Class Configured Impairment and Source Loss Evaluation

### 1. Problem Formulation and Class Distribution
- **Classes**:
  - `UNIMPAIRED` (n = 16): `baseline_control` and `authorized_source_change_no_action_control`.
  - `IMPAIRED` (n = 8): `netem_delay_jitter_loss` (10 ms delay, 2 ms jitter, 1% loss).
  - `SOURCE_LOSS` (n = 8): `authorized_source_change_intervention` (operator-initiated master stop).
- **Total Matched Runs**: N = 32 runs across Set 2 and Set 3 (Imbalance: 16:8:8).
- **Ground Truth Independence**: Fixed by experiment design and confirmed by daemon lifecycle logs in `events.log`, completely independent of packet timing features.

### 2. Feature Causality Annotations
To prevent retrospective circularity in control-loop evaluations, every feature is explicitly classified by its operational causality:
- **ONLINE**: Can be computed continuously from a bounded trailing window during live protocol execution (e.g. `sync_fu_paired_delay_std_s`, `max_delay_req_gap_s`, `sync_interarrival_jitter_s`).
- **RETROSPECTIVE**: Requires the complete capture to have terminated, or inspects distance to end-of-file (e.g. `max_announce_silence_at_end_s`).

> [!WARNING]
> **Retrospective Feature Disqualification**:
> `max_announce_silence_at_end_s` measures the duration from the stopped master's final Announce frame to capture termination. Because the master was terminated midway through the run and capture continued for approximately 30 seconds, this feature measures remaining capture duration. It is a **RETROSPECTIVE MANIPULATION CHECK**, confirming the process stop occurred. **A detector built on a RETROSPECTIVE feature cannot run in an operational self-healing loop**.

### 3. Feature Distributions and Margins Across All Three Classes

| Candidate Feature | Role | Causality | UNIMPAIRED (n=16) min / med / max | IMPAIRED (n=8) min / med / max | SOURCE_LOSS (n=8) min / med / max | Separable Class Pairs (Margin) | Inseparable Class Pairs |
|---|---|---|---|---|---|---|---|
| `max_announce_silence_at_end_s` | MANIPULATION_CHECK | RETROSPECTIVE | 0.024 / 0.150 / 0.216 s | 0.010 / 0.180 / 0.221 s | 29.913 / 30.060 / 30.172 s | SL vs UNIMP (29.70 s)<br>SL vs IMP (29.69 s) | UNIMP vs IMP (both active) |
| `sync_fu_paired_delay_std_s` | DETECTION_FEATURE | ONLINE | 18.3 / 40.0 / 72.2 us | 255.5 / 263.8 / 327.7 us | 20.4 / 38.7 / 64.9 us | IMP vs UNIMP (183.26 us)<br>IMP vs SL (190.60 us) | **UNIMP vs SL (overlap [20.4 us, 64.9 us])** |
| `sync_interarrival_jitter_s` | DETECTION_FEATURE | ONLINE | 80.4 / 122.3 / 160.4 us | 237.9 / 261.6 / 304.4 us | 81.0 / 126.7 / 180.2 us | IMP vs UNIMP (77.52 us)<br>IMP vs SL (57.73 us) | **UNIMP vs SL (overlap [81.0 us, 160.4 us])** |
| `max_delay_req_gap_s` | DETECTION_FEATURE | ONLINE | 0.246 / 0.250 / 0.250 s | 0.247 / 0.249 / 0.250 s | 0.250 / 0.346 / 0.657 s | None | **All pairs overlap** (SL reaches 0.250 s, below UNIMP max 0.250 s) |
| `announce_max_gap_any_source_s` | DETECTION_FEATURE | ONLINE | 0.250 / 0.251 / 0.251 s | 0.500 / 0.501 / 0.501 s | 0.250 / 0.251 / 0.254 s | IMP vs UNIMP (0.249 s)<br>IMP vs SL (0.246 s) | **UNIMP vs SL (surviving master paces at 250 ms)** |
| `num_announce_sources` | DETECTION_FEATURE | ONLINE | 2 / 2.0 / 2 | 2 / 2.0 / 2 | 2 / 2.0 / 2 | None | **Completely invariant** (exactly 2 in all 32 runs) |

---

## Part 4: Core Scientific Finding — Promoted Negative Technical Result

### Promoted Negative Finding: On Every Online Timing Feature, SOURCE_LOSS Overlaps UNIMPAIRED
The empirical evaluation demonstrates an unambiguous negative scientific result: **no online packet-timing feature evaluated cleanly separates operator-initiated source termination from unimpaired operations**.
- `sync_fu_paired_delay_std_s`: SOURCE_LOSS range [20.4 us, 64.9 us] falls entirely within the UNIMPAIRED range [18.3 us, 72.2 us]. Margin = **none (zero separation)**.
- `sync_interarrival_jitter_s`: SOURCE_LOSS range [81.0 us, 180.2 us] overlaps UNIMPAIRED range [80.4 us, 160.4 us]. Margin = **none (zero separation)**.
- `max_delay_req_gap_s`: SOURCE_LOSS minimum (0.250 s) reaches below the UNIMPAIRED maximum (0.250 s). In run `20260911_set3_intervention_r4`, the maximum observed Delay_Req interval during master handover was only 0.250 s, which is completely indistinguishable from nominal unimpaired transmission cadence. Margin = **none (zero separation)**.

### Candidate Explanations for the Lack of Separation
Without asserting which explanation dominates, the absence of timing degradation during source loss in this testbed is consistent with three physical and architectural factors:
1. **Disabled Clock Stepping (`free_running 1`)**: In accordance with the pilot specification, `ptp4l` runs in `free_running 1` mode to safeguard the host system clock. Consequently, the servo never adjusts the local clock frequency or steps the clock phase, preventing phase-transient jitter or servo-induced packet delay variations during failover.
2. **Shared Host Kernel Clock**: All endpoints (Master A, Master B, and Slave) read timestamps from the same underlying host kernel clock. Because there is no true independent hardware clock oscillator drift or frequency error between sources, switching masters introduces zero real physical timebase discontinuity.
3. **Continuous Availability of Backup Master**: Master B was configured, active, and transmitting Announce and Sync frames concurrently throughout the run. When Master A was terminated, the slave's BMCA state machine transitioned to Master B within 2 milliseconds without an extended period of un-synchronized holdover.

### Requirements to Test Real Source-Loss Timing Degradation
To establish whether timing degradation occurs during source loss in production telecommunications networks, the testbed would require:
- Independent physical hardware clocks (e.g. separate oscillators with distinct temperature drifts and wander characteristics).
- Closed-loop servo operation where the slave adjusts its physical clock hardware to match the active master.
- An external, out-of-band reference instrument (e.g. PPS counter or GNSS reference receiver) measuring true time error and phase transient offset on wire.

---

## Part 5: Cross-Validation Comparisons: Honest Online vs. Retrospective

### 1. Honest Online Detection Evaluation (Strictly ONLINE Features)
Evaluated with leave-one-run-out cross-validation across all 32 runs, fitting decision thresholds on training folds only:
- **Decision Logic**:
  - Fold threshold fit on `sync_fu_paired_delay_std_s` to separate `IMPAIRED` (> ~164 us).
  - Fold threshold fit on `max_delay_req_gap_s` to attempt separating `SOURCE_LOSS` (> ~265 ms) from `UNIMPAIRED`.

#### 3x3 Confusion Matrix (Honest Online Evaluation)
| Ground Truth Class | Pred: UNIMPAIRED | Pred: IMPAIRED | Pred: SOURCE_LOSS | Total Actual |
|---|---|---|---|---|
| **Actual: UNIMPAIRED** | **16** | 0 | 0 | 16 |
| **Actual: IMPAIRED** | 0 | **8** | 0 | 8 |
| **Actual: SOURCE_LOSS** | **1** | 0 | **7** | 8 |

#### Performance Summary (Honest Online Evaluation)
- **Overall Accuracy**: 96.88%
- **Macro-Averaged F1-Score**: 0.9677
- **Misclassification**: Run `20260911_set3_intervention_r4` experienced source termination but exhibited a maximum Delay_Req interval of only 0.250 s (below the training threshold of 264.9 ms), causing it to be classified as `UNIMPAIRED`.
- **Per-Class Metrics**:
  - `UNIMPAIRED`: Precision = 94.1%, Recall = 100.0%, F1 = 0.9697
  - `IMPAIRED`: Precision = 100.0%, Recall = 100.0%, F1 = 1.0000
  - `SOURCE_LOSS`: Precision = 100.0%, Recall = 87.5%, F1 = 0.9333
- **Permutation Control (1000 Iterations, Fixed Seed 42)**:
  - Empirical p-value: p = 0.0000
  - Null distribution of Macro-F1: min = 0.0404, median = 0.3108, mean = 0.3106, max = 0.6415.

### 2. Retrospective Reference Evaluation (Including Capture-End Silence Check)
- **Warning**: Presented for audit reference only. Incorporates `max_announce_silence_at_end_s` (~30 s silence).
- **Confusion Matrix**:
  - `UNIMPAIRED`: 16/16 correct (100%)
  - `IMPAIRED`: 8/8 correct (100%)
  - `SOURCE_LOSS`: 8/8 correct (100%)
- **Accuracy**: 100.0%, Macro-F1: 1.0000.

---

## Part 6: Reconciliation of Intervention Outage Criterion Across n=8 Runs

The original project acceptance register recorded intervention outage metrics from three exploratory runs (`set2` intervention r1-r3). When evaluated across all **n = 8 intervention runs** in `set2` and `set3`, the physical behavior of Delay_Req timing during master termination demonstrates critical variation:

1. **Strict 5x Median Interval Criterion**:
   - Outage detected (> 5x median): **1 of 8 runs** (`20260911_set2_intervention_r3` with gap 0.657 s vs median 0.116 s).
   - No outage detected (> 5x median): **7 of 8 runs**.
2. **Nominal 2.5x Median Interval Criterion**:
   - Outage detected (> 2.5x median): **5 of 8 runs** (outages between 0.341 s and 0.657 s; resumptions between 0.992 s and 1.336 s).
   - No outage detected (> 2.5x median): **3 of 8 runs** (`set3_intervention_r4`, `r6`, and `r8`).
3. **Register Alignment**:
   - The register criterion has been updated to reflect the full n=8 sample: an observable packet outage is **variable and not universally present across repetitions**. In 3 of 8 runs, Delay_Req transmission continues across the master termination with gap duration indistinguishable from nominal pacing.
