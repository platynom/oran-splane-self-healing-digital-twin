# Remaining Software Validation Acceptance Register

## 1. Overview and Purpose

This document establishes the acceptance criteria, taxonomy, and operational boundaries for completing the software-only validation milestones (R1 through R7) of the AI-Native Self-Healing O-RAN timing network prototype.

Hardware timing validation, physical clock synchronization, and telecommunication profile conformance (such as ITU-T G.8275.1 / G.8273.2) are explicitly deferred. The focus here is strictly on software-level protocol behavior, packet-arrival statistics, automated anomaly detection, and closed-loop segment failover in an emulated Linux network environment.

---

## 2. Four-Layer Classification Taxonomy

To ensure scientific rigor and prevent invalid inferential leaps (such as mistaking a network emulator configuration for an observed attack or hardware failure), all observations and classifications are strictly partitioned into four explicit layers:

```
+-------------------------------------------------------------------------------+
| Layer 4: Policy Classification                                                |
| (benign-within-policy, harmful-under-policy, UNKNOWN / insufficient evidence) |
+-------------------------------------------------------------------------------+
                                       ^
                                       | evaluates against policy rules
+-------------------------------------------------------------------------------+
| Layer 3: Observed Receiver / Protocol Impact                                  |
| (ptp4l port states: SLAVE, UNCALIBRATED, FAULTY; egress traffic collapse)     |
+-------------------------------------------------------------------------------+
                                       ^
                                       | correlates with protocol effects
+-------------------------------------------------------------------------------+
| Layer 2: Observed Packet Anomaly                                              |
| (Sync dispersion persistence above 160 us, or Announce message silence)       |
+-------------------------------------------------------------------------------+
                                       ^
                                       | detected on raw packet stream
+-------------------------------------------------------------------------------+
| Layer 1: Configured Experimental Condition                                    |
| (netem delay/jitter parameters, clean baseline, authorized source changes)    |
+-------------------------------------------------------------------------------+
```

### Layer 1: Configured Experimental Condition
- **Definition:** The ground-truth configuration applied by the testbed harness.
- **Examples:**
  - `baseline_clean`: Zero netem impairment on all interfaces.
  - `benign_delay_jitter`: Netem delay 100 us, jitter 20 us (normal distribution).
  - `jitter_fault`: Netem delay 100 us, jitter 200 us (normal distribution).
  - `authorized_source_failover`: Controlled switchover of primary master.
- **Rule:** This is what the test harness injected; it is never assumed to be known by the detector.

### Layer 2: Observed Packet Anomaly
- **Definition:** Statistical properties computed strictly from incoming packet timestamps and packet headers by the streaming detector.
- **Examples:**
  - `NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED`: Two consecutive 8-packet Sync/Follow_Up blocks with standard deviation exceeding 0.00016 s within a 3.0-second sliding window.
  - `SOURCE_ANNOUNCE_SILENCE`: Absence of Announce frames from an active source for longer than 0.75 seconds (3 receipt intervals).
  - `NORMAL_NOMINAL`: Statistical dispersion and packet receipt rates within nominal limits.
- **Rule:** The detector sees only raw packet bytes and timestamps from stdin. It has no access to scenario labels, interface names, or ground truth.

### Layer 3: Observed Receiver / Protocol Impact
- **Definition:** The measurable state changes inside the Linux PTP daemon (`ptp4l`) and the Linux kernel network interface queues.
- **Examples:**
  - Port state transitions: `UNCALIBRATED` to `SLAVE`, `SLAVE` to `FAULTY`, `LISTENING` to `UNCALIBRATED`.
  - Standby port takeover: Secondary port becoming the active synchronization target after primary port failure.
  - Egress packet flow collapse: Packet transmission halting on an impaired interface upon link-down command.
- **Rule:** Impact is measured from independent daemon logs (`slave.log`), protocol management queries (`pmc`), and interface counters (`tc -s qdisc`).

### Layer 4: Policy Classification
- **Definition:** The high-level operational determination made by comparing Layer 2 packet observations and Layer 3 impacts against acceptable network behavior policies.
- **Categories:**
  - `BENIGN_WITHIN_POLICY`: Packet metrics and arrival intervals conform to acceptable operating envelopes. No action warranted.
  - `HARMFUL_UNDER_POLICY`: Packet metrics demonstrate sustained dispersion or silence sufficient to impair protocol tracking. Remedial action warranted.
  - `UNKNOWN_INSUFFICIENT_EVIDENCE`: Metrics are abnormal but do not satisfy multi-block persistence criteria, or conflicting telemetry is present. Hold state and continue monitoring without premature action.

---

## 3. Scope Boundaries and Explicit Non-Claims

1. **Software-Only Emulation Boundary:**
   - All masters and slaves execute within isolated Linux network namespaces connected by software bridge devices (`ip link add type bridge`).
   - Clock adjustment is disabled via `free_running 1` in all PTP configuration files.
   - All network namespaces share the single host kernel monotonic and real-time clock. Namespaces do not possess independent hardware quartz oscillators.

2. **No Physical Clock Accuracy Claims:**
   - No claim is made regarding physical phase alignment, Time Error (TE), Maximum Absolute Time Error (max|TE|), or frequency drift.
   - Self-healing actions move the receiver's logical communication binding from one software segment to another; they do not physically discipline an oscillator.

3. **No Attack Attribution:**
   - An anomaly is evaluated strictly by its statistical properties (jitter magnitude, loss, or silence).
   - Packet dispersion caused by network queuing or malicious packet manipulation produces indistinguishable arrival statistics; no claim of cyber-attack detection is made.

---

## 4. Acceptance Register (Milestones R1–R7)

| Milestone | Objective | Key Acceptance Criteria | Status |
|---|---|---|---|
| **R1** | Scope & Acceptance Register | Reconcile the 4 classification layers; define explicit boundaries and non-claims; establish acceptance register. | OPEN |
| **R2** | Acceptable Behavior & Impact Policy | Define approved source parameters, message rate baselines, frozen detector thresholds, and measurable receiver impact criteria. | OPEN |
| **R3** | Broader Experiment Protocol | Freeze 5-condition protocol (`baseline_clean`, `benign_delay_jitter`, `jitter_fault_action`, `jitter_fault_no_action`, `authorized_source_failover`) with cryptographic hashes of all scripts. | OPEN |
| **R4** | Runner Validation (Smoke Test) | Execute isolated smoke trial with revised runner; verify clean direct-child exits ($rc=0$), FIFO drain on EOF, clean manifest sealing, and no post-seal appending. | OPEN |
| **R5** | Broader Experiment Execution | Run independent trials across all 5 conditions; log full packet captures, decision streams, and protocol transitions. | OPEN |
| **R6** | Evaluation Against Controls | Evaluate classification metrics (false alarms, misses, Wilson intervals) and recovery outcomes (action vs matched no-action control separation). | OPEN |
| **R7** | Dataset & Documentation Delivery | Ingest S14 runs into structured CSVs and streamed workbook; update `START_HERE_FINAL.md` and `CURRENT_ACCEPTANCE_LEDGER.md`. | OPEN |

---

## 5. Beginner's Reference Guide

- **What is a "Digital Twin" in this context?**
  A software emulation of the O-RAN synchronization network running on a Linux PC, where network namespaces simulate base stations (O-DUs and O-RUs) and network bridges simulate Ethernet fronthaul switches.
- **What is "Jitter"?**
  Random variation in the arrival time of clock packets. If packets arrive with erratic spacing, the clock receiver cannot easily distinguish true clock drift from transit delay variation.
- **Why is "No Action" necessary as a control?**
  To prove that the self-healing action caused the recovery, we must compare it against an identical test where the fault is injected but the recovery command is deliberately withheld. If the receiver only switches when the command is sent, the action is proven effective.
