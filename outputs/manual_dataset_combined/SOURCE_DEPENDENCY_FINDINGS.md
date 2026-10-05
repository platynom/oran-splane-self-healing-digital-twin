# Source dependency findings

This is a static/dependency audit, not a claim that every listed code path ran in the current workspace.

## Directly configured or invoked paths

- `config/default.yaml` names `data/external/timesafe_prod_successful_announce_attack_ptp.pcap` for the PCAP backend. It is a 1,086,860-byte byte-identical copy of the source PCAP.
- `scripts/run_tier2.py` passes `data/external/timesafe_sessions` to the real-session evaluator. The ten CSVs are copied from `dataset/timesafe/timesafe_sessions`; their H0/H1 labels came from an interval projection and are now rejected without traceable clock-health evidence.
- `evasion/victim_transformer.py` reads the released raw PCAPs, packet-label CSVs, and operational session exports. It is now rejected unless a hash-verified packet-label validation artifact establishes packet-maliciousness semantics.
- `dataset/build.py`, `scripts/run_all.py`, and the standard training/benchmark path generate synthetic simulator data. They do not load TIMESAFE files by default.

## Duplicate and overlap control

- Project-local `data/external` contains byte-identical copies of source-side TIMESAFE objects. They are representations, not independent experiments.
- The session directory contains ten projected telemetry exports. Adjacent 0.4-second windows with a 0.2-second step overlap by design, so windows must not be counted as independent observations.
- Announce sessions 1 and 2 are one PCAP with conflicting labels; their separate audit quarantines both from independent count, train/test split, and validated-ground-truth use.

## What the audit does not say

No static scan can prove a historical file is unused: a launcher may construct a path dynamically, a user may supply an input at runtime, or an existing result may have been generated earlier. The full machine-readable inventory, hashes, CSV schemas, and static references are in `source_traceability_audit.json`.

## Evidence required before re-inclusion

Clock-health evaluation needs a documented validation method, source hashes, a hash-verified evidence artifact, and semantics explicitly stating `measured_clock_health`. Packet-classification evaluation needs the same traceability but semantics of `packet_maliciousness`. Neither condition is met by a plain metadata flag, a matching filename, a label pattern, or packet/CSV alignment alone.
