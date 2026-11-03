# Reactive, preventive and predictive scope

## Direct answer to Q16

The implemented system is **reactive**. It observes executed PTP traffic, detects a violation or timing-service loss, localises the ingress, chooses a bounded action, executes it, verifies the radio-unit parent/grandmaster state, and rolls back or escalates if verification fails. The packet-legality channel requires an ATTACK verdict in at least two of the last three one-second evaluations; the service-continuity channel triggers after more than 2 seconds without Announce from a provisioned master-role port, or 10 seconds during a maintenance window.

The system also contains **preventive provisioning**. Grandmaster and boundary-clock identities, port roles, the maintenance-window state, a cold standby boundary clock and the frozen rule are installed before the event. This reduces the post-event decision space, but it does not predict an attack.

The system is **not predictive**: no forecasting model was implemented or evaluated. The eight attacks are access- and intent-driven events; the captured timing stream does not contain a validated precursor that says when an attacker will inject, replay, remove or fuzz a packet. A slow physical process such as oscillator drift (B6) could in principle be trended, but the present testbed shares one host oscillator and did not evaluate such forecasting.

## Mechanism classification

| Mechanism | Class | Implemented? | Evidence |
|---|---|---:|---|
| Capture → detect → localise → decide → act → verify → rollback/escalate | Reactive | Yes | `03_RECOVERY_LOOP_S-PLANE/RECOVERY_LOOP_DESIGN.md`; `code/recovery_loop.py` |
| Frozen-rule ATTACK persistence: at least 2 of the last 3 evaluations | Reactive | Yes | `03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md` §3; `code/FROZEN_RL.json` |
| Service-continuity trigger: no Announce from a provisioned master for >2 s; 10 s in maintenance | Reactive | Yes | `03_RECOVERY_LOOP_S-PLANE/PREREGISTRATION.md` §3; `RECOVERY_LOOP_DESIGN.md` “Two detection channels” |
| Isolate a violating non-master ingress with an nftables bridge rule | Reactive containment | Yes | `03_RECOVERY_LOOP_S-PLANE/RESULTS_2026-10-05.md` §2 and §5: 35/35 final isolation rules present |
| Activate a pre-cabled cold standby boundary clock after service loss | Reactive recovery enabled by preventive provisioning | Yes | `RESULTS_2026-10-05.md`: C1 restored 5/5, median primary-RU unhealthy time 2.5 s versus 39.0 s control |
| Verify parent, grandmaster allow-list and port state with passive `pmc -d 24` | Reactive assurance | Yes | `PREREGISTRATION.md` §4; `RESULTS_2026-10-05.md` §5 |
| Roll back and escalate if action verification fails | Reactive safety control | Implemented; failure path not exercised in the reported evaluation | `RECOVERY_LOOP_DESIGN.md` policy table; `PREREGISTRATION.md` §3 |
| Provisioned GM/BC allow-list and per-port role inventory | Preventive | Yes | `RECOVERY_LOOP_DESIGN.md` “Localisation”; per-run `provisioning.json` in `results/recovery_eval_runs_r13-r17.tgz` |
| Maintenance-window context and pre-registered expected replacement BC | Preventive | Yes | `RECOVERY_LOOP_DESIGN.md`; per-run `state.json`; B_bc_replacement produced escalation but no isolation |
| Cold standby BC cabled and ready before the fault | Preventive resilience | Yes | `PREREGISTRATION.md` §2; `RESULTS_2026-10-05.md` §2 |
| Pre-registered, hash-frozen rule, parameters and hypotheses | Preventive experimental/control-plane measure | Yes | `code/FROZEN_RL.json`; `PREREGISTRATION.md` |
| Redundant source/path architecture | Preventive design basis | Partly: one standby BC was exercised; independent physical paths were not | RFC 7384 §5.9: “common practices … use redundant masters … or redundant paths”; `CITATION_VERIFICATION_2026-11.md` D08 |
| Attack prediction from timing telemetry | Predictive | No | No prediction code, pre-registration or result exists |
| Trend slow oscillator degradation such as B6 | Predictive future work | No | `RECOVERY_LOOP_DESIGN.md` “Oscillator drift”; no independent telecom oscillator in this testbed |

## Measured reactive timing

Across the 140-run recovery evaluation, detection occurred about 1.1 seconds after fault onset, the first action about 2.1 seconds after onset, and restored parent/grandmaster verification within about one further second. For A1 and C3, the loop reduced median primary-RU unhealthy time from 38.5 seconds to 2.0 seconds and restored 5/5 runs. For sustained C1, it reduced the median from 39.0 seconds to 2.5 seconds and restored 5/5 via the standby BC.

These are protocol-state timings, not nanosecond clock-error recovery. Every daemon used `free_running 1`, so the evaluated outcome was who the radio units followed and whether the expected timing relationship was restored.

