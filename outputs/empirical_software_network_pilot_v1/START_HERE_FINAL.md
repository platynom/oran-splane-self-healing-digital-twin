# Empirical software-network package — current entrypoint

> **Validation status:** S15 completed its 30 frozen independent software-testbed runs. Its pre-specified
> result is **not established**: receiver-above-boundary trigger rate was 14/15 (0.9333), but
> receiver-below-boundary no-trigger rate was 8/15 (0.5333), below the frozen 0.8 criterion. See
> [S15_INDEPENDENT_VALIDATION_EVALUATION.json](S15_INDEPENDENT_VALIDATION_EVALUATION.json). The S14 figures in
> `S14_BROADER_EXPERIMENT_EVALUATION.json` are development-set figures: the receiver statistic and its
> boundary were derived from S14, so S14 cannot validate them. The authoritative status of every milestone
> is the "Current status" table in [REMAINING_WORK_ACCEPTANCE_REGISTER.md](REMAINING_WORK_ACCEPTANCE_REGISTER.md);
> earlier status statements in that file are marked superseded history.
>
> **S14 interpretation boundary:** Read [S14_EVIDENCE_DISPOSITION.md](S14_EVIDENCE_DISPOSITION.md) before using any S14 material. Existing S14 labels are expected conditions, not ground-truth harmfulness labels; the material is descriptive and unvalidated for harmfulness.

Start with [the full packet workbook](s14_dataset/S14_empirical_full_packet_streamed.xlsx).
It has eight sheets, including the 232,403-packet `Packets` sheet and a `Read me` tab.
The lossless source companions are [packets](s14_dataset/s14_packets.csv),
[events](s14_dataset/s14_events.csv), [decisions](s14_dataset/s14_decisions.csv),
[receiver log](s14_dataset/s14_receiver_log.csv), [receiver transitions](s14_dataset/s14_receiver_transitions.csv),
and [outcomes](s14_dataset/s14_outcomes.csv). The run index has 168 empirical software-testbed rows
(143 historical runs plus 25 fresh prospective S14 runs).

This package is separate from the audited historical TIMESAFE workbook:
[ORAN_All_Current_Datasets_FINAL_PCAP_v2_CLASSIFIED.xlsx](../manual_dataset_combined/ORAN_All_Current_Datasets_FINAL_PCAP_v2_CLASSIFIED.xlsx).

## Current scientific scope and policy framework

1. **Acceptance Register & 4-Layer Taxonomy:** Defined in [REMAINING_WORK_ACCEPTANCE_REGISTER.md](REMAINING_WORK_ACCEPTANCE_REGISTER.md).
2. **Behavior & Software Impact Policy:** Defined in [ACCEPTABLE_BEHAVIOR_AND_IMPACT_POLICY.md](ACCEPTABLE_BEHAVIOR_AND_IMPACT_POLICY.md).
3. **S14 development evaluation (not validation):** [S14_BROADER_EXPERIMENT_REPORT.md](S14_BROADER_EXPERIMENT_REPORT.md) and [S14_BROADER_EXPERIMENT_EVALUATION.json](S14_BROADER_EXPERIMENT_EVALUATION.json). These are development-set results. The receiver-side measurement that accompanies them is [RECEIVER_DISPERSION_S14_V2.json](RECEIVER_DISPERSION_S14_V2.json), produced by `measure_receiver_dispersion_v2.py`, which supersedes the exploratory `S14_PRE_ACTION_IMPACT.json`.
6. **Planned independent validation (v3):** [S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json](S15_INDEPENDENT_VALIDATION_PROTOCOL_V5.json), executed by `run_s15_smoke.sh` then `run_s15_validation_batch.sh` and evaluated by `evaluate_s15.py`. Not yet run.
7. **Protocol deviations:** [PROTOCOL_DEVIATION_REGISTER.md](PROTOCOL_DEVIATION_REGISTER.md).
4. **Runner Integrity:** The direct-child drain-and-seal mechanism (`seal_owned_writers_v2.sh`) passed smoke validation in `s14_smoke_run/trial/` and governed all 25 S14 trials with 100% manifest integrity, zero post-seal appending, and zero non-zero process exits.
5. **Software-Only Boundary:** All runs executed in Linux network namespaces with `free_running 1`. Clock adjustment was disabled; no physical clock accuracy, holdover, or hardware profile conformance is claimed.

## Reproduction and checks

Use `prepare_s14_dataset.py` to rebuild the CSV sources and `build_s14_packet_xlsx.py` for the write-only XLSX.
The current reconciliation is [s14_full_detail_reconciliation.json](s14_dataset/s14_full_detail_reconciliation.json).
Evaluation of the 25 S14 runs is executed via `evaluate_s14_broader.py`.
