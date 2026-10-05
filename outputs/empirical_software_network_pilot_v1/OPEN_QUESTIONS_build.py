import json
from pathlib import Path

def build_open_questions():
    root = Path(__file__).resolve().parent
    ra_path = root / 'RUN_ANALYSIS.json'
    rep_path = root / 'REPEATABILITY.json'

    with open(ra_path, 'r', encoding='utf-8') as f:
        ra = json.load(f)

    with open(rep_path, 'r', encoding='utf-8') as f:
        rep = json.load(f)

    int_rep = rep['intervention']['delay_req_outage_s']
    outage_spread = int_rep['spread']
    outage_min = int_rep['min']
    outage_max = int_rep['max']
    
    s1 = ra['runs']['20260911_set2_intervention_r1']['source_change_measurement']
    proto_floor = s1['protocol_detection_floor_s']

    content = f"""# Open Questions and Proposed Future Investigations

This document details unresolved physical and protocol mechanisms identified during the analysis of empirical software pilot test runs, specifies the evidence observations, presents candidate explanations, and outlines additional measurements to separate them.

---

## 1. Outage-Duration Spread Mechanism

### Observation
- **Evidence Reference**: `outputs/empirical_software_network_pilot_v1/REPEATABILITY.json#intervention.delay_req_outage_s`
- **Details**: Across intervention condition repetitions, the measured packet-observable outage duration (`delay_req_outage_s`) exhibits variability across test runs (spread of {outage_spread:.6f} s between minimum {outage_min:.6f} s and maximum {outage_max:.6f} s) beyond the baseline protocol detection floor of {proto_floor:.2f} s (`outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_intervention_r1.source_change_measurement.protocol_detection_floor_s`).

### Candidate Explanations
1. **Host OS Scheduling Jitter**: Software process scheduling delays and thread context switching within the host kernel across network namespaces during `ptp4l` BMCA reselection state processing.
2. **Timer Event Loop Granularity**: Discrepancy in `ptp4l` internal event loop tick resolution and socket unbind/rebind scheduling cadence when resetting port state following missing Announce frames.
3. **Socket Buffer Queueing Delays**: Kernel network stack socket queue buffering delays on virtual ethernet (`veth`) bridge interfaces during master transition.

### Specific Additional Measurement to Separate Explanations
- Instrument low-overhead eBPF kernel socket probes (`kprobe:netif_rx`, `kprobe:udp_recvmsg`) combined with verbose `ptp4l` debug logging (`ptp4l -m -q -v`) to capture microsecond-accurate timestamps for:
  - Socket frame arrival at network interface layer.
  - Process wakeup and socket buffer dequeue in `ptp4l`.
  - BMCA state evaluation execution.
  - Transmission of first `Delay_Req` frame under the new master source.

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
1. **IEEE 1588 EUI-64 Mapping Rule**: The analyzer verifies that `grandmasterIdentity` is a 16-character hexadecimal string formed by taking the 12-character canonical MAC address (lower-case, colons stripped) and inserting `fffe` between the first 6 characters and the last 6 characters (`f"{{mac[:6]}}fffe{{mac[6:]}}"`), without bit inversion. IEEE 1588 clockIdentity inserts `fffe` without inverting the universal/local bit (that inversion belongs to IPv6 SLAAC). Any mismatch indicates non-compliant synthetic packet generation or manual field override.
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
"""

    out_path = root / 'OPEN_QUESTIONS.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully generated {out_path}")

if __name__ == '__main__':
    build_open_questions()
