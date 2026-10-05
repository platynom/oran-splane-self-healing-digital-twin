# Part B: Two-Path Mechanism Feasibility Spike Report

## Purpose and Scope

This capability check investigates whether a multi-port rerouting mechanism exists in this testbed.
It evaluates one slave ptp4l instance configured with two ports connected via separate veth pairs
to the bridge, with single-path netem impairment applied after a clean settle period.
**NO closed-loop recovery was executed and NO recovery claim is made.**

## Capability Questions and Evidence-Backed Answers

### Q1: Does one ptp4l instance actually bring up and hold two ports in this namespace?
**Answer**: **YES**

- Evidence file: `slave.log`
- Ports observed in ptp4l log: [0, 1, 2]
- State transitions recorded in slave.log:
  - `ptp4l[354.764]: port 1: INITIALIZING to LISTENING on INIT_COMPLETE`
  - `ptp4l[354.812]: port 2: INITIALIZING to LISTENING on INIT_COMPLETE`
  - `ptp4l[354.812]: port 0: INITIALIZING to LISTENING on INIT_COMPLETE`
  - `ptp4l[356.088]: port 1: LISTENING to UNCALIBRATED on RS_SLAVE`

### Q2: Does PTP traffic flow on both paths before impairment?
**Answer**: **YES**

- Evidence files: `capture_s1.pcap`, `capture_s2.pcap`, `tc_s1_before.txt`, `tc_s2_before.txt`
- Path 1 (S1) pre-impairment packets captured: 517 (total: 1414)
- Path 2 (S2) pre-impairment packets captured: 517 (total: 1421)
- S1 TC before: packets=0, bytes=0, dropped=0
- S2 TC before: packets=0, bytes=0, dropped=0
- Decoded message breakdown on Path 1: {'Announce': 175, 'Sync': 349, 'Follow_Up': 351, 'Delay_Req': 180, 'Delay_Resp': 359}
- Decoded message breakdown on Path 2: {'Announce': 177, 'Sync': 352, 'Follow_Up': 352, 'Delay_Req': 180, 'Delay_Resp': 360}

### Q3: With netem on one path only, does the clean path keep carrying PTP traffic?
**Answer**: **YES**

- Evidence files: `capture_s2.pcap`, `tc_s2_before.txt`, `tc_s2_after.txt`
- Path 2 (clean path) packets captured after impairment: 904
- S2 TC counters: before=0 pkts, after=0 pkts (delta=0 pkts)
- Path 1 (impaired path) TC counters: before=0 pkts, after=676 pkts (dropped=7)

### Q4: Does the slave's port state machine react to the impaired path at all, and how?
**Answer**: **NO: The port state machine did not change port states after the impairment was applied under this configuration and duration.**

- Evidence files: `slave.log`, `pmc_port_states.log`, `events.log`
- Total transitions logged: 4
- No port state transitions occurred following impairment onset during the observation window.

## Artifact Manifest and Verification

The following artifacts were produced by `spike_two_path_topology.sh` and hashed into `source_manifest.sha256`:
- `capture_s1.pcap`
- `capture_s2.pcap`
- `events.log`
- `master_a.conf`
- `master_b.conf`
- `slave.conf`
- `master_a.log`
- `master_b.log`
- `slave.log`
- `tc_s1_before.txt`
- `tc_s1_after.txt`
- `tc_s2_before.txt`
- `tc_s2_after.txt`
- `run_environment.txt`
- `source_manifest.sha256`

## Conclusion and Mechanism Feasibility Assessment

- Dual-port slave topology instantiation: FEASIBLE
- Dual-path traffic concurrency before impairment: CONFIRMED
- Clean path traffic preservation under single-path netem: CONFIRMED

