# Empirical software-network pilot v1

Status on 2026-09-10: **NOT_EXECUTED**. The current WSL service rejected the root testbed entry with `Wsl/Service/E_ACCESS_DENIED`; no namespace, interface, qdisc, `ptp4l`, capture, clock, or host setting was changed. This directory therefore contains reproducible implementation and planned metadata only—not measured data or outcomes.

Run only from the audited isolated Linux environment:

```text
sudo harness/run_empirical_software_pilot.sh --preflight
sudo PILOT_DURATION_SECONDS=30 harness/run_empirical_software_pilot.sh --execute outputs/empirical_software_network_pilot_v1/runs/RUN_ID a1 baseline_control
```

Each invocation is one independent run with a unique short run token. It creates a disposable bridge and three namespaces. Two `ptp4l` masters use priority1 100 and 150; the endpoint uses linuxptp 3.1.1 `slaveOnly 1`. All nodes specify `free_running 1`, which the exact tagged 3.1.1 manual defines as not adjusting the local clock. The four permitted scenarios are a baseline control, a netem delay/jitter/loss intervention, an authorised-source-change no-action control, and the corresponding preferred-master-stop intervention. These are selected pilot settings, not a universal timing threshold, an ITU profile claim, or recovery evidence.

The exact tagged [linuxptp 3.1.1 `ptp4l(8)` manual](https://raw.githubusercontent.com/richardcochran/linuxptp/v3.1.1/ptp4l.8) supports L2 transport, software timestamping, E2E, `slaveOnly`, `masterOnly`, intervals, and `free_running`; preflight also requires actual `ptp4l -v` output of `ptp4l 3.1.1`. The configuration remains an isolated laboratory setup; IEEE 1588 text was not available locally and no standards-compliance claim is made. `tc netem` is a controlled network impairment, not physical-fault proof.

## Labels and observations

| Field | Permitted values / rule |
|---|---|
| `planned_scenario` | One of the four runner scenario names; no-action and source-stop runs are separate control/intervention records. |
| `injection_executed` | `CONFIRMED_COMMAND`, `NOT_EXECUTED`, or `UNKNOWN`—from event/qdisc logs only |
| `observed_impact` | `OBSERVED`, `NOT_OBSERVED`, `UNKNOWN`, or `MISSING`; derived only by a documented check |
| `source-change command` | `preferred_master_stop_confirmed`, `NOT_EXECUTED`, or `UNKNOWN`; never “recovered” |
| `measured_outcome` | a specific measured value/status, `MISSING`, or `UNKNOWN`; never inferred from planned action |

This is free-running protocol observation, not closed-loop clock recovery. Expected source selection can only be assessed from captured Announce fields and receiver process/management evidence. It is not evidence of authenticated receiver state, unauthorized takeover, GNSS health, SyncE quality, independent oscillators, or successful production recovery.

## Data dictionary

| Artifact | What it measures / limitation |
|---|---|
| `capture.pcap` | Nanosecond-format capture timestamps and PTP frames observed on the software veth; capture time is not PTP protocol time and not a calibrated physical reference. |
| `master_a.log`, `master_b.log`, `slave.log` | `ptp4l -m` textual process observations. Their absence/malformed lines must be retained, not defaulted. |
| `events.log` | Exact planned phases, qdisc state, and command timing. It confirms command execution only where recorded. |
| `*.conf` | Actual selected software configuration, with units/interval exponents visible. |
| `source_manifest.sha256` | Integrity manifest for captured, log, configuration, and event files after a completed run. |

## Original evidence boundary

TIMESAFE captures and the C0–C3 classifier remain parser/event-rule comparison material only. They are not relabelled, merged into this pilot, or used to validate outcomes here. Existing workbooks and audited sources remain unchanged.
