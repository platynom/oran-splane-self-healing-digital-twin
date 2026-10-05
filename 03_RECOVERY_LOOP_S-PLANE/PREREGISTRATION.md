# Pre-registration — S-plane recovery loop evaluation

Written and hash-frozen **before** any evaluation run (replicates 13–17). The only runs that came before it are development runs with replicate 101, which are reported separately and never pooled with the evaluation.

## 1. Question

Does a detect → localise → decide → act → verify loop restore the O-RU timing service faster than doing nothing? Does it do so while taking **no** disruptive action on benign timing faults? The loop is built on the frozen decision rule of the 168-run campaign, used unchanged.

## 2. Apparatus (configured condition)

- **Testbed:** the frozen G.8275.1 harness of the 168-run campaign, used unchanged.
  - Six linuxptp 4.0 daemons in network namespaces: GM-A, GM-B, BC, RU1–RU3.
  - Two bridges: brUP and brDN.
  - `free_running 1`, software timestamping. The host clock is never touched.
- **Addition in every run of both arms:** a cold-standby boundary clock `bcs`, identity `020000fffe0000c5`, cabled to both bridges. Its daemon starts only if the loop executes a failover.
- **Fault mechanisms:** identical to `scenarios.sh` / `run_gap.sh` of the campaign, with these differences:
  - Faults start at **T0 = 20 s** and **persist to the end of the run** (T0 + 40 s).
  - C1 is a sustained blackhole of the BC downstream port that is **not** restored.
- **Two arms**, with the same scenario, replicate and randomised parameters:
  - `control`: the identical loop in observe-only mode. It detects, decides and logs `would_act`, and executes nothing.
  - `loop`: closed loop. It executes the action and verifies it.
- **Replicates:** 13, 14, 15, 16, 17, giving 14 scenarios × 2 arms × 5 = **140 runs**.
- **Run order:** for each replicate, scenarios in a fixed list. The arm order alternates by replicate: odd replicates run control first, even replicates run loop first.

## 3. Loop parameters (fixed in `recovery_loop.py`)

| Parameter | Value | Reason |
|---|---|---|
| Evidence window | 6 s sliding, evaluated every 1 s | Long enough for ≥ 48 Announce / 96 Sync frames at G.8275.1 rates |
| Persistence | ≥ 2 of the last 3 evaluations ATTACK | Single-window transients cannot trigger an action |
| Warm-up | 12 s | BMCA start-up must settle |
| Service-loss trigger | no Announce from any provisioned master port for 2 s; 10 s while a maintenance window is open | Above announceReceiptTimeout (3 × 125 ms); planned work gets a grace period |
| Verification | pmc `-d 24` on every non-isolated RU: parent ∈ provisioned master-role identities, GM ∈ allow-list, portState ∈ {SLAVE, UNCALIBRATED}, within 20 s | The outcome the action must achieve |
| Rollback | undo the action and escalate if verification fails | — |
| Safety guard | a master-role provisioned port (primary BC, standby BC, planned replacement BC) is never isolated automatically | Isolating it would itself remove timing |

## 4. Outcome measurement

Outcomes are measured only by the **passive observer** (`observer.py`), which is identical in both arms:
- It polls pmc `-d 24` PARENT_DATA_SET and PORT_DATA_SET on RU1–RU3 every 0.5 s.
- An RU is **healthy** when its parent clockIdentity ∈ {BC, standby BC, planned replacement BC (B_bc_replacement only)}, its grandmaster ∈ allow-list, and its portState ∈ {SLAVE, UNCALIBRATED}.
- UNCALIBRATED counts as tracking because `free_running 1` keeps the servo in s0.

**Primary nodes are RU1 and RU2.** RU3 shares the attacker's port in A2, A3, A5, C2 and C3, and is the bounced RU in B7. It is reported separately.

| Metric | Definition |
|---|---|
| `unhealthy_s` (primary) | seconds in [T0, T0 + 40] during which RU1 or RU2 is not healthy |
| `restored_at_end` | RU1 and RU2 healthy throughout [T0 + 35, T0 + 40] |
| `rogue_parent_s` | seconds RU1 or RU2 follows a parent that is neither provisioned nor itself |
| Descriptive | detection latency (first ATTACK evaluation after T0), first action time, verification result, RU3 unhealthy seconds |

## 5. Hypotheses and pass criteria (5 replicates per scenario per arm)

- **H1 – restoration.** For every attack scenario (A1, A2, A3, A5, A8, C1, C2, C3), both of the following must hold:
  - loop `restored_at_end` = 5/5;
  - median `unhealthy_s` (loop) ≤ median `unhealthy_s` (control).

  For every attack scenario where the control median `unhealthy_s` ≥ 5 s, the loop median must also be ≤ 50 % of the control median.
- **H2 – containment.**
  - In A1, A2, A3, A5, A8, C2 and C3, the loop isolates an ingress port carrying the attack, with verification passed, in ≥ 4/5 runs.
  - In C1, the standby failover is executed and verified in ≥ 4/5 runs.
- **H3 – no harm on benign faults.** Zero disruptive actions (ISOLATE or ACTIVATE_STANDBY_BC) across all 25 loop runs of baseline, B2, B3, B7 and B_bc_replacement.
- **H4 – honest abstention.** In B_unplanned_failover, zero disruptive actions, and an escalation is logged in ≥ 4/5 loop runs.
- **Control integrity.** No action is executed in any control run. Checked with the final nft ruleset (no `rl` table) and the absence of `bcs.log`.

A hypothesis that fails is reported as failed. Nothing is re-run to change an outcome. A run whose apparatus failed (for example, a daemon did not start, detected as pre-T0 health < 0.8) is reported and excluded **in both arms** for that scenario/replicate pair.

## 6. What this does not establish

- **No physical clock steering.** `free_running 1` stays on, so time-error recovery in nanoseconds is not measured; the parent and grandmaster relationship is.
- **Same software testbed.** No hardware, no real switch ACLs; the nft bridge rule stands in for a switch-port PTP filter.
- **Same detector as the campaign.** The loop inherits its limits, including the 60 % interception evasion band and the base rule's false A8 on a provisioned replacement BC. Here that false A8 is neutralised by the safety guard, not fixed in the rule.
- **Not a digital twin.** No digital twin rehearses the action before it is taken; verification happens after the action, on the live testbed.
