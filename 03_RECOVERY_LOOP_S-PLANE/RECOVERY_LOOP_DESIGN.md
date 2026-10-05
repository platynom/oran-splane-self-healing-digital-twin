# Recovery loop — design

The loop closes the gap the deck states on slide 38: *"Automated corrective action — none in the 168-run campaign"*. It runs on the same software testbed and uses the same frozen detector. It does not change any frozen artefact.

```
            brDN (radio-unit segment)                       recovery loop (root namespace)
  p-v-bc-dn ─┐                                       ┌──────────────────────────────────────────┐
  p-v-ru1   ─┤   every PTP frame, tagged with its    │ 1 CAPTURE   AF_PACKET per bridge port,   │
  p-v-ru2   ─┼── ingress port ──────────────────────▶│             ingress only, parse_frame()  │
  p-v-ru3   ─┤                                       │             from frozen extractor        │
  p-rogue …  ┘                                       │ 2 DETECT    6 s window → frozen rule v3  │
                                                     │             decide_v2 (hash-checked)     │
  standby BC (bcs) ─ cabled, daemon off              │             + service-continuity check   │
                                                     │ 3 LOCALISE  per-port role conformance    │
  RU1..RU3 ◀── pmc -d 24 (read-only) ──────────────┤ 4 DECIDE    policy table + persistence   │
                                                     │             + safety guard               │
                                                     │ 5 ACT       nft bridge drop / start bcs  │
                                                     │ 6 VERIFY    RU parent + GM via pmc       │
                                                     │ 7 ROLLBACK  undo + escalate on failure   │
                                                     └──────────────────────────────────────────┘
```

## Two detection channels

| Channel | Signal | What it answers | Basis |
|---|---|---|---|
| **1 Packet legality and provisioning** | Frozen `decision_rule_v3.decide_v2` on a 6 s sliding window of segment frames, once per second. The base rule is imported unchanged from `decision_rule.py`. | Is this traffic illegal or unauthorised? (ATTACK / BENIGN / UNKNOWN + fault hint) | IEEE 1588-2019 legality, G.8275.1 profile, provisioned context (the campaign's own rule) |
| **2 Timing-service continuity** | Time since the last Announce from any provisioned master-role port on the segment | Has the segment lost its timing source? | announceReceiptTimeout semantics; RFC 7384 §5.9 redundancy |

Channel 2 exists because channel 1 **cannot see an ongoing total blackhole in a sliding window**. Rule clause D1 requires the starved source to be active over at least half the window, and also requires its delivered rate to fall below half of its declared rate. During a continuous blackhole both conditions cannot hold at once. The 168-run campaign caught C1 only because each capture included the restore tail. This was found while designing the loop, and it is the reason channel 2 was added.

## Localisation: provisioned port roles

`provisioning.json` lists, for each bridge port, the device, its role (master or client) and its provisioned clockIdentity values. The operator owns this inventory; it is not a measurement. In each window, a port violates its provisioning if any of the following holds:
- it is **not provisioned** and originates PTP (rogue GM, rogue BC);
- it is a **client-role port** originating master-role messages (Sync, Follow_Up, Delay_Resp, Announce). This is the master-only / notSlave idea seen from the other side: spoofing, replay, flooding or forged Announce entering from an RU port;
- it carries **source identities not provisioned for that port** (a forged identity);
- it carries **malformed** frames.

## Policy table

| Verdict / signal | Localised port | Action | Verification | Basis |
|---|---|---|---|---|
| ATTACK on ≥ 2 of the last 3 evaluations | Violating port that is not a provisioned master-role port | **ISOLATE**: nft bridge prerouting `iifname <port> ether type 0x88f7 drop` | Every non-isolated RU: parent ∈ provisioned master identities, GM ∈ allow-list, portState ∈ {SLAVE, UNCALIBRATED}, within 20 s; otherwise **rollback** + escalate | RFC 7384 §5.1.1, §5.10.1; acceptable master table / master-only ports (Arnold & Frost); notSlave (G.8275.1) |
| ATTACK | Only provisioned master-role ports, or no violating port | **ESCALATE** (no automatic action) — **safety guard** | — | Isolating a provisioned BC would itself remove timing |
| Service loss > 2 s (10 s if a maintenance window is open) | — | **ACTIVATE STANDBY BC** | As above | RFC 7384 §5.9; Prong C |
| UNKNOWN | — | **ESCALATE** | — | Arnold & Frost "raise alarm" |
| BENIGN | — | **TOLERATE** (nothing) | — | Declared, standards-consistent state change |

## Why the B_bc_replacement false alarm causes no harm here

The base rule still returns ATTACK (A8) when a provisioned replacement BC appears. The loop takes no action because:
- the replacement's port is provisioned in the master role by the maintenance ticket in `state.json`;
- it carries only its provisioned identity, so the localiser finds no violating port.

The result is a single escalation and no disruption. The same holds when the loop's own standby BC is activated. This is a property of the loop's guard. The rule itself is not fixed.

## Oscillator drift (B6)

B6 cannot be produced in namespaces, because all six clocks share one oscillator. The two-laptop measurement of 2 Oct ESTABLISHED a relative crystal offset of +21.013 ppm [20.623, 21.403] (run 2; `outputs/B6_two_machine_2026-10-02/run2/DRIFT_REPORT_run2.md`). Run 1 gave +20.161 ppm but was NOT ESTABLISHED; the 0.852 ppm run-to-run difference is larger than either confidence interval. These are consumer laptop crystals measured against NTP, not telecom-class oscillators.
- **Policy:** benign drift that stays within the declared holdover state is TOLERATE.
- **Implication of the measured offset:** an undisciplined clock pair separates by about 21 µs per second, so a 1.5 µs budget is gone in about 0.07 s.
- **Consequence for recovery:** for drift, "holdover" is only useful with a disciplined (GNSS/OCXO-class) oscillator; the right response is to restore a reference quickly (failover), not to wait.

This is arithmetic on a measured value. The loop does not exercise B6.

## Limits carried forward

- **Clock steering:** `free_running 1` stays on, so the loop restores *who the RUs follow*. Nanosecond time error is not measured.
- **Same detector:** the loop inherits the campaign rule's limits, including interception evasion below about 60 % within a window.
- **Collateral:** isolating the RU3 port (where the testbed's injector lives) also removes RU3's own timing. This is reported, not hidden.
- **No digital twin:** the action is verified after execution on the live testbed, not rehearsed beforehand.
