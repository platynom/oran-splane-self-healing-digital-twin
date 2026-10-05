# Superseded question wording — see `CURRENT_ACCEPTANCE_LEDGER.md`

The proposed `ptp4l -v` debug use, `-f` UTC-format claim, universal MAC/grandmaster identity mapping claim, and protocol-timing causal explanations below are not established by the present records. Treat them as unverified hypotheses, not instructions or standards facts.

# Open Questions and Proposed Future Investigations

This document details unresolved physical and protocol mechanisms identified during the analysis of empirical software pilot test runs, specifies the evidence observations, presents candidate explanations, and outlines additional measurements to separate them.

---

## 1. Outage-Duration Spread Mechanism and Non-Outage Run Differentiation

### Observation
- **Evidence Reference**: `outputs/empirical_software_network_pilot_v1/INTERVENTION_OUTAGE_RECONCILIATION.json#summary`
- **Details**: When evaluated across all n=8 intervention repetitions in Set 2 and Set 3, packet-observable Delay_Req outage duration is variable and not universally present. Under the strict 5x-median interval criterion, an outage is detected in only 1 of 8 runs (`20260911_set2_intervention_r3`, gap 0.656833 s vs median 0.115856 s). Under the nominal 2.5x-median criterion, an outage is detected in 5 of 8 runs (outages ranging from 0.341005 s to 0.656833 s; resumptions from 0.991612 s to 1.336006 s). In 3 of 8 runs (`20260911_set3_intervention_r4`, `r6`, and `r8`), the maximum Delay_Req interval during master handover (0.249719 s to 0.294617 s) is completely indistinguishable from nominal pacing (~0.250 s).

### Candidate Explanations for Outage vs. Non-Outage Discrepancy
1. **Slave State-Machine Phase Alignment at Master Termination**: If the slave's internal Announce receipt timer (`announceReceiptTimeout`, 3 Announce intervals = 0.75 s) expires immediately before a scheduled Delay_Req transmission, BMCA re-selection occurs concurrently without stalling the transmission timer. Conversely, if termination occurs midway between intervals, the slave may suppress Delay_Req until new foreign master Announce qualification completes.
2. **Host OS Scheduling Jitter and Socket Buffering**: Variations in thread context switching across Linux network namespaces during `ptp4l` socket re-binding on virtual ethernet (`veth`) interfaces.
3. **PTP Message Coincidence**: Interleaving between Master B's active Announce arrival and the slave's transmission timer, determining whether port state switches from `SLAVE` to `LISTENING` and back to `SLAVE` within a single polling epoch.

### Specific Additional Measurement to Separate Explanations
- Deploy low-overhead eBPF kernel socket probes (`kprobe:netif_rx`, `kprobe:udp_recvmsg`) combined with verbose `ptp4l` debug logging (`ptp4l -m -q -v`) to capture microsecond-accurate timestamps for:
  - Exact epoch of final Announce frame receipt from the terminating master.
  - Slave internal timer expiration and BMCA state evaluation execution.
  - Transmission epoch of the subsequent Delay_Req frame under the backup master.

---

## 2. Epoch Offset Between ptp4l-log and events.log

### Observation
- **Evidence Reference**: `outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_intervention_r1.setup_epoch_offset_observation`
- **Details**: Non-zero offset observed between timestamps recorded in `ptp4l` stdout logs (`slave.log`) and host script event logs (`events.log`).

### Candidate Explanations
1. **Clock Source Discrepancy**: `ptp4l` process logging uses monotonic clock offset (`CLOCK_MONOTONIC`) or relative process uptime, whereas `events.log` captures host system wall-clock time (`CLOCK_REALTIME`).
2. **I/O Pipe Buffering Latency**: Asynchronous shell pipe stdout buffering and process execution delays between harness invocation (`date +%s.%N`) and `ptp4l` log write operations.

### Specific Additional Measurement to Separate Explanations
- Capture system monotonic clock (`CLOCK_MONOTONIC_RAW`) alongside UTC wall-clock (`CLOCK_REALTIME`) at harness boot initialization.
- Configure `ptp4l` to format log lines with explicit UTC microsecond timestamps (`-f` flag or standard syslog formatting) to bind log entries directly to host epoch time.

---

## 3. EUI-64 MAC-to-GrandmasterIdentity Consistency Validation

### Observation
- **Evidence Reference**: `outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_baseline_r1.announce_analysis_by_source`
- **Details**: Validation check verifying whether source MAC addresses in Ethernet frames match `grandmasterIdentity` values advertised in PTP Announce payloads (`eui64_consistent`).

### Candidate Explanations
1. **IEEE 1588 EUI-64 Mapping Rule**: The analyzer verifies that `grandmasterIdentity` is a 16-character hexadecimal string formed by taking the 12-character canonical MAC address (lower-case, colons stripped) and inserting `fffe` between the first 6 characters and the last 6 characters (`f"{mac[:6]}fffe{mac[6:]}"`), without bit inversion. IEEE 1588 clockIdentity inserts `fffe` without inverting the universal/local bit (that inversion belongs to IPv6 SLAAC). Any mismatch indicates non-compliant synthetic packet generation or manual field override.
2. **Interface Address Aliasing**: Virtual interface MAC address reassignment or packet injection spoofing in testbed frame generators.

### Specific Additional Measurement to Separate Explanations
- Execute automated frame parsing using a standard library Python pcap reader script (`parse_pcap_dynamic`), extracting Ethernet frame headers and PTP Announce payload fields directly using `struct.unpack` to compare Ethernet source MAC addresses against `grandmasterIdentity` values without external dependencies.

---

## 4. Proposed Future Experiment (Unexecuted Proposal)

> [!NOTE]
> **Proposed Experiment**: Non-Intrusive eBPF Tracing for Software Testbed Protocol Delay Separation.
>
> - **Objective**: Measure internal kernel socket queueing and process scheduling latencies during PTP grandmaster failover without modifying host clock settings or altering testbed topology.
> - **Methodology**: Deploy eBPF kernel event probes in the Linux host kernel across network namespaces to record exact microsecond timestamps for socket packet enqueue, process dequeue, and protocol packet transmission.
> - **Scope Limitation**: Operates purely in software network namespace testbed; does not alter system clock (`free_running 1` maintained) or execute physical hardware interventions.
