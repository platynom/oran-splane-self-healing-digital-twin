# Canonical experiment and representation map

This map groups verified capture lineages and identifies collections whose individual run relationships remain unresolved. A representation is retained for a stated purpose; it is never automatically an additional independent experiment. The detailed workbook uses explicit unresolved run-linkage identifiers for Netem files rather than asserting a single shared experiment.

| Canonical experiment | Source representations | Purpose retained | Status / eligible claim |
|---|---|---|---|
| Production Announce capture | S026 supplied labels; S027 raw CSV; production PCAP aliases; S038/S039 derived telemetry; S040 upstream label copy | Packet/CSV alignment and PCAP-ingestion audit | Exploratory packet/telemetry description. Supplied labels are not independently verified attack ground truth; no clock-health/recovery claim. |
| Announce capture conflict | S021/S022 labels; S041/S042 CSV aliases; four byte-identical PCAP aliases; S028–S031 projected sessions | Preserve conflict/provenance only | QUARANTINED. One capture, 5,312 label conflicts. Never count twice or use for ground-truth training/testing. |
| Announce session 3 | S023 labels; S043 raw CSV; matching PCAP alias; S032/S033 projected sessions | Packet alignment/provenance | Supplied annotation only. Derived sessions exploratory; no verified attack/clock-health claim. |
| Sync/Follow-Up session | S024 labels; S044 raw CSV; matching PCAP alias; S034/S035 projected sessions | Packet alignment/provenance | Supplied annotation only. Derived sessions exploratory. |
| Single-step Sync session | S025 labels; S045 raw CSV; matching PCAP alias; S036/S037 projected sessions | Packet alignment/provenance | Supplied annotation only. Derived sessions exploratory. |
| Netem software-testbed records | S001–S016 | Software behavior and recorded testbed outputs | Software-testbed analysis only. Default/inferred telemetry fields cannot establish hardware measurement or physical recovery. |
| Synthetic simulator collection | S017/S018 and byte-identical S019/S020 | Simulator training/benchmark provenance; use scenario/run_id to identify constituent runs | Simulated evidence only. S019/S020 are duplicates of S017/S018 and are excluded from independent count. |
| Model/result summaries | S005–S007 and other result CSVs | Provenance of prior software runs | Not input evidence and not independent experiments. |

## Leakage rules

1. Split by canonical experiment/capture before windowing. Never put an alias, raw export, processed telemetry, or overlapping window from one canonical capture across train and test.
2. The default 0.4-second windows with 0.2-second steps overlap. Adjacent windows share observations and are not independent samples.
3. A raw capture, its encoded packet labels, telemetry, features, decisions, and summaries are one evidence lineage. Use the raw form to audit transformations and one canonical analytical form for counts.
4. Keep quarantined sources visible in provenance but exclude them from validated ground truth, claim-supporting aggregates, and model evaluation.

## Why retain more than one representation

Raw PCAP/CSV supports packet parsing and transformation checks. Encoded labels preserve the publisher’s original annotation. Derived telemetry supports only explicitly marked exploratory processing. Summaries preserve a record of software runs. Retention is for traceability, not statistical multiplication.
