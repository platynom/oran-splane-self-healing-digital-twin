# Evidence-based label taxonomy

| Label / status | What it means | Evidence required | It must not be read as |
|---|---|---|---|
| Supplied packet `Label=1` | Source annotation for a packet claimed to be injected/malicious | Capture-specific label-generation evidence or launch record to call it ground truth | Measured clock health, duration of exposure, recovery success |
| Supplied packet `Label=0` | Source annotation that the packet is not labelled injected | Original label file | A physically healthy clock or benign network state |
| Packet-pattern description | A rule found by inspecting existing labels (for example sender/message type) | The saved label file | Independent reproduction or attacker identity proof |
| `H0` simulated | Non-malicious timing fault in the project simulator | Simulator scenario and deterministic generation | Production or physical O-RAN evidence |
| `H1` simulated | Timing attack in the project simulator | Simulator attack injector and scenario | Real-capture maliciousness or physical impact |
| Projected TIMESAFE H0/H1 | Earlier first-to-last packet-label interval projection | Packet-label timestamps and transform code | Clock-health, precise attack exposure, or ground truth. Quarantined. |
| `healthy` simulated | Simulator’s nominal trace | Simulator configuration | A real clock-health measurement |
| Model `H1`, novelty, `UNKNOWN`, `PENDING` | Classifier/novelty/persistence output | Model and window inputs | Observed attack or clinical/physical diagnosis |
| `safe_default` / action candidate | Software decision or forecast candidate | Healing-loop/twin code | Executed physical action or measured recovery |
| Measured clock health | Receiver timing state / physical clock behavior | Traceable hardware timestamps plus receiver/M-plane status and calibration | Any packet label or default-filled telemetry row |

For a beginner: a packet annotation says something about one message. Clock health describes the receiver’s timing behavior. An attack exposure interval describes what the receiver experienced over time. A recovery outcome needs a recorded action and before/after measurement. They answer different questions and cannot replace one another.
