# Original-goal acceptance audit

| Requested goal | Current state | Evidence / remaining requirement |
|---|---|---|
| Isolated software PTP testbed | Implemented, not executed this session | `harness/run_empirical_software_pilot.sh`; current WSL entry was denied before mutation. |
| Baseline, impairment, authorised source change | Implemented as a single minimum pilot sequence | Acceptance criteria 2–4; fresh run artifacts still required. |
| Exact configuration, command, timing, capture provenance | Implemented | runner writes configs, event/environment logs, pcap, and SHA-256 manifest. |
| Separated scenario/injection/impact/action/outcome labels | Defined and enforced in documentation | README label table; validator refuses to manufacture outcome labels. |
| Measured receiver selection/servo/clock error | Not yet executed; limited even when run | Process logs/capture are planned observations; management socket sampling and calibration would be needed for stronger receiver/servo evidence. |
| Repeated control/action trials and independent splits | Not yet executed | repeat each execution with unique `run_id`; split by run. |
| Physical GNSS, SyncE, oscillator, O-RAN conclusions | Excluded | no physical hardware evidence in this software testbed. |
