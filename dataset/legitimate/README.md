# legitimate/ — real, collected, standards-traceable evidence

Everything here was produced by a real capture or a real live run. Nothing here was generated
by a simulator.

Two caveats that must be carried into any result derived from this folder:

1. **Inert sensor columns.** SyncE, GNSS and oscillator columns are honest constants because those
   sensors do not exist on a software testbed. They carry zero information; excluding them is correct.
2. **Software timestamping.** Servo/timing values are real but sit on a microsecond-scale noise
   floor, not the nanosecond target. Express thresholds as multiples of the measured floor, never
   as absolute timing-budget claims.

Quarantine: `15min_announce_attack.pcap` and `2024-10-06-announce_attack_UEdata.pcap` are
byte-identical with conflicting labels — never use both.
