# Empirical Software Network Pilot: Introductory Concepts and Retained Conclusions

This document provides an introductory guide to Precision Time Protocol (PTP) concepts and presents four empirical conclusions derived from the software pilot testbed runs.

---

## 1. Fundamentals of PTP and Testbed Concepts

Before examining testbed results, we introduce essential protocol and architecture terms:

- **PTP (Precision Time Protocol / IEEE 1588)**: A network protocol designed to synchronize real-time clocks across nodes in a network to sub-microsecond precision.
- **PTP Message Types**:
  - **Announce**: Transmitted periodically by grandmaster candidates to advertise timing attributes (clock class, priority, accuracy).
  - **Sync**: Transmitted by the grandmaster to initiate time synchronization. In two-step mode, Sync establishes the coarse transmission event, but does not carry the precise egress timestamp ($t_1$); its paired Follow_Up frame carries $t_1$.
  - **Follow_Up**: Transmitted in two-step mode to supply the precise egress timestamp ($t_1$) of the preceding Sync message. Two-step operation is independent of whether timestamping is hardware or software. This pilot uses software timestamping and two-step, which is why Follow_Up frames are present.
  - **Delay_Req**: Transmitted by a slave clock to request link delay measurement, capturing local egress timestamp ($t_3$).
  - **Delay_Resp**: Transmitted by the master in response to Delay_Req, returning the master ingress timestamp ($t_4$).
- **BMCA (Best Master Clock Algorithm)**: The state machine algorithm executed by PTP nodes to select the highest-quality available timing source based on Announce message properties.
- **Grandmaster (GM)**: The primary reference clock selected by BMCA to provide time to the domain.
- **Boundary Clock (BC)**: An intermediate PTP node with multiple ports that acts as a slave to an upstream GM and a master to downstream slaves.
- **clockClass**: An 8-bit attribute in Announce messages denoting GM traceability and stability (for example, class 6 for a GNSS-locked master, class 248 for a default free-running clock).
- **announceReceiptTimeout**: The number of missed Announce intervals required before a slave declares master loss and triggers BMCA reselection (configured to 3 intervals).
- **netem (Network Emulation)**: A Linux kernel queuing discipline module used to emulate packet delay, loss, and duplication on network interfaces.
- **qdisc (Queueing Discipline)**: A Linux kernel packet scheduling structure attached to network interface egress queues.
- **Network Namespace**: An isolated Linux network stack instance containing independent interfaces, routing tables, and socket bindings.
- **free_running Mode**: A `ptp4l` configuration parameter (`free_running 1`) that prevents `ptp4l` from adjusting host system clock frequency or step offset.
- **Software vs. Hardware Timestamping**:
  - **Software Timestamping**: Captures packet timestamps in kernel network stack upon socket buffer processing, subject to OS scheduling and interrupt latency.
  - **Hardware Timestamping**: Captures packet timestamps directly at network interface card (NIC) PHY/MAC layer using dedicated hardware counters, eliminating host scheduling jitter.

---

## 2. Retained Empirical Conclusions

### Conclusion 1: Netem Direction-Match Consistency

- **WHAT**: The observation is a direction-matched consistency between a confirmed netem packet loss injection on the bridge-to-slave path and observed missing PTP sequence numbers in the master-to-slave direction, rather than a causal proof.
- **WHICH**: Evaluated across netem condition repetitions `r1`, `r2`, and `r3` with configured loss rate of 1.0%.
- **WHERE**: Egress queue of interface `$SR` in the root namespace attached to the bridge, facing the slave network namespace.
- **WHEN**: During active netem test condition execution.
- **WHY**: Linux `tc qdisc` netem rules apply exclusively to interface egress buffers. Packets traveling from the bridge in the root namespace to the slave network namespace pass through the impaired qdisc on `$SR`, whereas packets traveling in reverse (slave network namespace to root namespace) bypass the qdisc.
- **HOW**: In run `r1`, `tc qdisc` reported 20 dropped packets while 20 missing sequence numbers were observed in the master-to-slave direction (reverse: 0). In `r2`, `tc qdisc` reported 20 dropped packets while 19 missing sequence numbers were observed (reverse: 0). In `r3`, `tc qdisc` reported 19 dropped packets while 19 missing sequence numbers were observed (reverse: 0). Where counts differ, they agree to within one frame, and a residual of one is expected because an egress drop can fall outside the capture accounting window.

---

### Conclusion 2: Intervention Outage and Resumption with Protocol Detection Floor

- **WHAT**: Terminating the active grandmaster transmitter induces a packet-observable outage duration in `Delay_Req` frame transmission before the slave switches to an alternate grandmaster.
- **WHICH**: Evaluated across intervention repetitions `r1`, `r2`, and `r3`.
- **WHERE**: Network namespace topology during master source failover.
- **WHEN**: Triggered upon unannounced termination of primary master transmitter.
- **WHY**: The slave clock cannot instantly detect source loss. It must await `announceReceiptTimeout` (3 consecutive missed Announce intervals, establishing a protocol detection floor of 0.75 s) before BMCA initiates reselection.
- **HOW**: Measured in capture timestamps, `delay_req_outage_s` yielded 0.486946 s in `r1`, 0.466648 s in `r2`, and 0.656833 s in `r3`. Across repetitions, minimum outage was 0.466648 s, median was 0.486946 s, maximum was 0.656833 s, with a total spread of 0.190185 s.

---

### Conclusion 3: Interpretation of ptp4l Servo Statistics Under Software Timestamping

- **WHAT**: The servo statistics reported in `ptp4l` logs measure host kernel network stack scheduling jitter rather than physical clock offset.
- **WHICH**: `ptp4l` internal clock servo tracking output line in `slave.log`.
- **WHERE**: Generated inside the slave network namespace.
- **WHEN**: Collected continuously throughout test execution (for example, baseline run `r1` record: `ptp4l[22.725]: rms 7425 max 15747 freq   +512 +/- 4414 delay 13512 +/- 2770`).
- **WHY**: Under software timestamping, packet timestamps include Linux kernel socket queueing, context switching, and interrupt servicing delays.
- **HOW**: All endpoints read the same host kernel clock, so there is no independent clock error for the servo to measure; the reported statistic is timestamping and scheduling noise. Note that a non-zero rms is expected under this arrangement and is not a synchronisation error.

---

### Conclusion 4: Limitations Imposed by Shared Host Clock Architecture

- **WHAT**: Virtualized single-host network namespace testbeds cannot measure physical time synchronization error, phase alignment, or frequency stability.
- **WHICH**: Physical clock health and timing accuracy metrics.
- **WHERE**: Single-kernel virtualized network namespace environment.
- **WHEN**: Across all pilot test execution runs.
- **WHY**: All network namespaces share a single shared host kernel clock. Even when `free_running 1` prevents `ptp4l` from adjusting host system time, all nodes read from the same kernel time source.
- **HOW**: Physical synchronization measurement requires independent hardware oscillators, dedicated NIC hardware timestamping (PHCs), and external hardware reference clocks (such as GNSS receivers or rubidium standards) connected over physical links.
