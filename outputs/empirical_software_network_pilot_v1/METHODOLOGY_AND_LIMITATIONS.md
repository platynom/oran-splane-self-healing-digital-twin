# Methodology and limits

## Chosen method

The implementation creates disposable Linux namespaces joined by a private bridge. It runs two `masterOnly` masters and one `slaveOnly` endpoint with L2 PTP, E2E delay measurement, software timestamping, a short Sync/Delay request interval (`-3`, or 2^-3 seconds), an Announce interval of `-2` (2^-2 seconds), and an Announce receipt timeout of three missed messages. All three configurations use `free_running 1`, so the endpoint observes protocol behavior without adjusting a local clock. Separate invocations provide baseline, netem, source-change no-action control, and preferred-master-stop intervention records.

These values are **chosen laboratory parameters**. They are not a claimed IEEE 1588, ITU-T profile, O-RAN, or deployment requirement. No 100 ns threshold is applied. A future deployment study must state its applicable profile, reference plane, calibrated instrumentation, and acceptance criterion.

The primary implementation reference is the exact tagged [linuxptp 3.1.1 `ptp4l(8)`](https://raw.githubusercontent.com/richardcochran/linuxptp/v3.1.1/ptp4l.8), accessed 2026-09-10: it documents L2 transport, software timestamping, E2E consistency, `slaveOnly`, `masterOnly`, Announce timeout, interval exponents, and `free_running` (“Don't adjust the local clock”). The runner requires exact `ptp4l -v` output before execution. The controlled impairment is recorded as a `tc netem` command and queried qdisc state, rather than treated as a real network fault.

The IEEE standard text and an applicable ITU-T profile were not available in the local evidence package during this bounded task. Consequently, this pilot makes no standards-compliance claim and does not cite a mandatory profile setting. The existing author preprint and TIMESAFE captures may support parser/event-rule comparison only; they do not supply outcomes or labels for this pilot.

## Measurement and label discipline

* PCAP record time is the capture tool’s nanosecond timestamp on a veth interface. PTP origin timestamps, where present, are separate protocol fields.
* Process logs are receiver/software observations; they must be retained even when empty or malformed. A shared-host virtual environment cannot demonstrate independent oscillator behavior.
* `events.log` records run ID, UTC and monotonic phase boundaries, readiness, and command status. It cannot by itself establish impact or recovery.
* “Authorized source change” means a laboratory process stop with a pre-running alternate master. It has a separately executed no-action control. Packet advertisements are not authenticated selected-source state, unauthorized takeover evidence, GNSS/SyncE/oscillator health, or a physical recovery result.
* A future repeated analysis must split by `run_id`. Packet or fixed-window splits from one capture would leak one run across training and test data.

## Execution block and required next evidence

At 2026-09-10, `wsl.exe -d Ubuntu-22.04 -u root` returned `Wsl/Service/E_ACCESS_DENIED`. The preflight could therefore not be run in the current session, and no empirical record exists here. To execute, restore authorised access to the named isolated WSL testbed, run preflight, use a new empty run directory, run `validate_pilot.py`, and retain its capture, qdisc transcript, configuration, logs, and hashes. Hardware/physical conclusions additionally require separate PHC/GNSS/SyncE-capable equipment and calibrated reference measurements.
