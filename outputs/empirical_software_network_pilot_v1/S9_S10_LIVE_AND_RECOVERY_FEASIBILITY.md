# S9 live-detection readiness and S10 recovery-mechanism feasibility

Date 2026-09-13.

## S9 — Live software detection: READY, with two porting requirements

The frozen engine was already written as a single-pass streaming consumer. Seven falsifiable tests
were written and run against real V4 captures (`tests/test_live_detection_causality.py`), **7/7 pass**:

| Test | What it would catch |
|---|---|
| `test_no_lookahead_prefix_determinism` | Outputs for the first k packets compared against the same k packets from the full run, at five cut points across four captures. Any future dependence changes a prefix. |
| `test_no_end_of_file_dependence` | Appending trailing frames must not alter earlier outputs. |
| `test_capture_identity_does_not_change_classifications` | The stream id partitions context only; it must not shift any decision. |
| `test_no_filename_or_scenario_reaches_the_engine` | Engine signature is `(capture_id, ts, frame)`; engine source contains no scenario or condition word. |
| `test_timestamp_regression_is_rejected_not_crashed` | Out-of-order arrival is rejected as invalid, not consumed. |
| `test_state_is_bounded_over_a_long_stream` | Six concatenated captures; pending pair and block state stay bounded. |
| `test_tick_emits_silence_without_fabricating_a_packet` | Silence during an arrival gap requires a caller clock tick and must not invent a packet. |

**Porting requirement 1 — stream identity.** `capture_id` is currently a capture file hash. Live use
has no file. Supply a stable per-stream identifier instead; the tests confirm the value does not
change any classification.

**Porting requirement 2 — a clock tick.** Source silence is arrival-driven. With no arrivals, nothing
fires until the next packet. A live deployment must call `tick()` on a timer (at most every 0.75 s,
the silence threshold) or silence detection is delayed by the arrival gap itself.

Not established by S9: detection latency under live load, behaviour under packet reordering at rates
above those observed, or any performance claim. These tests prove the engine is *causally usable*,
not that it is accurate.

## S10 — Recovery mechanism feasibility: NEGATIVE for the detected condition

Actions configured in `healing/loop.py` were checked against what the isolated testbed can actually do.

Topology, from the runner: one Linux bridge, three namespaces, and **exactly one veth pair per
namespace**. The slave has a single link.

| Configured action | Executable in this testbed? | Why |
|---|---|---|
| `reroute_path` | **No** | The slave has one interface. There is no alternate path to route to. |
| `failover_gnss` | **No** | No GNSS receiver exists, real or emulated. |
| `failover_lls_c1` / `c2` / `c3` | **No** | No LLS-C interfaces exist in the testbed. |
| `holdover` | **No meaning** | All endpoints share one host clock under `free_running 1`. There is no local oscillator to hold over. |
| `isolate_rogue_master` | **No target** | Both masters are authorised. The testbed contains no adversary. |
| `safe_default` | Trivially | A no-op. Not a remedy. |
| Stop / start a master process | **Yes** | Already exercised as the source-change condition. |
| Change master preference at runtime (`pmc` SET priority1) | **Plausible, untested** | Requires verification that `pmc` is present and the UDS socket is reachable in the namespace. Not yet attempted. |
| Remove the injected netem qdisc | **Yes, but** | This is undoing our own laboratory injection. It is not a production repair and must never be reported as autonomous recovery. |

**The finding.** The condition the detector actually observes — dispersion persistence under
configured netem on the slave's single ingress link — has **no available remedy in this topology**.
Every action that could plausibly remediate a degraded path requires a second path, a second clock
source, or hardware that does not exist here. The only action with a genuine mechanism, switching the
timing source, addresses source loss, which the dispersion channel does not detect (V4: 0/5
persistence in termination runs).

**Consequence for S11 and S12.** A closed-loop experiment cannot be run honestly against the netem
condition in the current testbed. Two options, neither yet chosen:

1. **Extend the topology** so `reroute_path` becomes real: give the slave a second veth to the bridge
   (or a second bridge), impair only one path, and let the action switch paths. This is a genuine
   mechanism and would make S11 and S12 meaningful. It requires a new runner version and a new frozen
   protocol.
2. **Re-scope the loop to source switching**, where a mechanism already exists, and accept that the
   trigger is the silence channel rather than the dispersion channel.

Until one is chosen and executed, S11 and S12 remain NOT STARTED, and no recovery claim of any kind
is supported.
