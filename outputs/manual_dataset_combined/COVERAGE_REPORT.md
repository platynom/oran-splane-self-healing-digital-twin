# Repository-wide software read coverage

Date 2026-09-13. Source of every number below: `coverage/full_coverage_inventory.jsonl` (4604 records). Built by `build_coverage_report.py`; no value typed by hand.

Model checkpoints were **never unpickled** - only their ZIP central directory was read. Python files were **never executed** - only parsed with `ast`.

## 1. Files opened, per root

| Root | Files |
|---|---|
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data` | 659 |
| `02_PREVIOUS_Work` | 589 |
| `dataset` | 651 |
| `outputs` | 2705 |

## 2. By handler type

| Type | Files | Parsed successfully |
|---|---|---|
| OPAQUE | 3019 | 0 |
| capture | 205 | 205 |
| json | 507 | 507 |
| model_checkpoint | 291 | 291 |
| python_source | 244 | 244 |
| tabular | 338 | 0 |

## 3. Duplicate groups (the leakage map)

613 sha256 values occur on more than one path, covering 1377 files.

Correctness check on this code: the two Announce session captures are expected to collide. They appear in the map as ["01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_1.pcap", "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_2.pcap", "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DataCollectionPTP/15min_announce_attack.pcap", "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DataCollectionPTP/2024-10-06-announce_attack_UEdata.pcap", "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_1.pcap", "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_2.pcap", "dataset/timesafe/s-plane_security_repo/DataCollectionPTP/15min_announce_attack.pcap", "dataset/timesafe/s-plane_security_repo/DataCollectionPTP/2024-10-06-announce_attack_UEdata.pcap", "dataset/timesafe/timesafe_multi_raw/announce_session_1.pcap", "dataset/timesafe/timesafe_multi_raw/announce_session_2.pcap"].

Largest groups:

| sha256 (first 16) | Files | Paths |
|---|---|---|
| `d2c91b3e4f09a3ec` | 10 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_1.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_2.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DataCollectionPTP/15min_announce_attack.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DataCollectionPTP/2024-10-06-announce_attack_UEdata.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_1.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_2.pcap`<br>…and 4 more |
| `3a9fe69a502f9eef` | 8 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/best_model_tr.3.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.3.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.3.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_tr.3.32.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/best_model_tr.3.32.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.3.32.pth`<br>…and 2 more |
| `778fcd85f68d6c23` | 8 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/best_model_tr_new.3.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr_new.3.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr_new.3.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_tr_new.3.40.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/best_model_tr_new.3.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr_new.3.40.pth`<br>…and 2 more |
| `57f61beb952a9025` | 8 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.16.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.16.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/no_ts/best_model_no_ts_tr.1.16.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_no_ts_tr.1.16.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.16.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.16.pth`<br>…and 2 more |
| `28ed58f15df254ff` | 8 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/no_ts/best_model_no_ts_tr.1.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_no_ts_tr.1.32.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.32.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.32.pth`<br>…and 2 more |
| `75d0dfe63dba75cc` | 8 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/no_ts/best_model_no_ts_tr.1.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_no_ts_tr.1.40.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/Archive/best_model_no_ts_tr.1.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/models_un/best_model_no_ts_tr.1.40.pth`<br>…and 2 more |
| `a59604999f45e14f` | 6 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/.git/logs/HEAD`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/.git/logs/refs/heads/master`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/.git/logs/refs/remotes/origin/HEAD`<br>`dataset/timesafe/s-plane_security_repo/.git/logs/HEAD`<br>`dataset/timesafe/s-plane_security_repo/.git/logs/refs/heads/master`<br>`dataset/timesafe/s-plane_security_repo/.git/logs/refs/remotes/origin/HEAD` |
| `ec254fe8d35d520e` | 6 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.16.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.16.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.16.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.16.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.16.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.16.pth` |
| `d942d3198f0c7af3` | 6 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.32.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.32.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.32.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.32.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.32.pth` |
| `0d4125e3a470d3a9` | 6 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.40.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/best_model_tr.2.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/new/best_model_tr.2.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Digital_Twin/best_model_tr.2.40.pth` |
| `a45f8fcb8888a3b1` | 6 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Transformer/Archive/best_model_tr_updated.3.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Production_Environment/Archive/models_tested/best_model_tr_updated.3.40.pth`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_tr_updated.3.40.pth`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Transformer/Archive/best_model_tr_updated.3.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Production_Environment/Archive/models_tested/best_model_tr_updated.3.40.pth`<br>`dataset/timesafe/s-plane_security_repo/Testbed/PipelineTestDU/PipelineScripts/Models/best_model_tr_updated.3.40.pth` |
| `0690ed95ddc3134e` | 5 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_prod_successful_announce_attack_ptp.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DataCollectionPTP/prod_successful_announce_attack_ptp.pcap`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_prod_successful_announce_attack_ptp.pcap`<br>`dataset/timesafe/s-plane_security_repo/DataCollectionPTP/prod_successful_announce_attack_ptp.pcap`<br>`dataset/timesafe/timesafe_prod_successful_announce_attack_ptp.pcap` |
| `6a03a10bd9f47480` | 5 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_1_labels.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Datasets/Original/15min_announce_attack.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_1_labels.csv`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Datasets/Original/15min_announce_attack.csv`<br>`dataset/timesafe/timesafe_multi_raw/announce_session_1_labels.csv` |
| `840769d5c5c54177` | 5 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_2_labels.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Datasets/Original/2024-10-06-announce_attack_UEdata.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_2_labels.csv`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Datasets/Original/2024-10-06-announce_attack_UEdata.csv`<br>`dataset/timesafe/timesafe_multi_raw/announce_session_2_labels.csv` |
| `c680567aa1f69fdd` | 5 | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/dataset_2026-08-30/timesafe/timesafe_multi_raw/announce_session_3_labels.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/Datasets/Original/2024-10-08-announce_attack1.csv`<br>`01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/timesafe_multi_raw/announce_session_3_labels.csv`<br>`dataset/timesafe/s-plane_security_repo/DU_model/Datasets/Original/2024-10-08-announce_attack1.csv`<br>`dataset/timesafe/timesafe_multi_raw/announce_session_3_labels.csv` |

## 4. Coverage gap: data files under `dataset/` not in the 45-source manifest

237 data files (csv, tsv, pcap, pcapng, pth) are present but not manifested.

| Path | Type | Records / rows |
|---|---|---|
| `dataset/Netem/fail_closed_holdover.pcap` | capture | 22 |
| `dataset/Netem/fail_closed_holdover_after.pcap` | capture | 1 |
| `dataset/Netem/holdover.pcap` | capture | 23 |
| `dataset/Netem/loss2.pcap` | capture | 442 |
| `dataset/Netem/netem_baseline.pcap` | capture | 2670 |
| `dataset/Netem/netem_holdover.pcap` | capture | 17 |
| `dataset/Netem/netem_loss.pcap` | capture | 399 |
| `dataset/Netem/netem_pdv.pcap` | capture | 2590 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/ext_heur7jul_latest_dataset.csv` | tabular | 1076733 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/extended_heuristic_7jul_dataset.csv` | tabular | 561672 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/final_heuristic_dataset.csv` | tabular | 912183 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/final_heuristic_extended_dataset.csv` | tabular | 1342787 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/final_timestamp7jul_dataset.csv` | tabular | 528189 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/heuristic_dataset.csv` | tabular | 515062 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/merged_dataset.csv` | tabular | 912182 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/merged_extended_dataset.csv` | tabular | 1342786 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/t7jul_lat_ext_t9jul1_2_3_4_5_6_final.csv` | tabular | 1746706 |
| `dataset/timesafe/s-plane_security_repo/Archive/Combinations/updated_extended_dataset.csv` | tabular | 913738 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/ext_heur7jul_latest_dataset_no_time.csv` | tabular | 1076733 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/extended_dataset_no_time.csv` | tabular | 430604 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/extended_heuristic_7jul_dataset_no_time.csv` | tabular | 561672 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/final_dataset_no_time.csv` | tabular | 397121 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/final_heuristic_dataset_no_time.csv` | tabular | 912183 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/final_heuristic_extended_dataset_no_time.csv` | tabular | 1342787 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/final_timestamp7jul_dataset_no_time.csv` | tabular | 528189 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/heuristic_dataset_7jul_no_time.csv` | tabular | 131068 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/heuristic_dataset_no_time.csv` | tabular | 515062 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/latest_dataset_no_time.csv` | tabular | 515061 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/merged_dataset_no_time.csv` | tabular | 912182 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/merged_extended_dataset_no_time.csv` | tabular | 1342786 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/timestamp_comp_dataset_7jul_no_time.csv` | tabular | 131068 |
| `dataset/timesafe/s-plane_security_repo/Archive/DatasetNoTimestamp/updated_extended_dataset_no_time.csv` | tabular | 913738 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/BenignTraces.csv` | tabular | 33483 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/heuristic_dataset_7jul.csv` | tabular | 131068 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/latest_dataset.csv` | tabular | 515061 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/t7jul_lat_ext_t9jul1.csv` | tabular | 1116542 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/t7jul_lat_ext_t9jul1_2.csv` | tabular | 1188168 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/t7jul_lat_ext_t9jul1_2_3.csv` | tabular | 1229774 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/t7jul_lat_ext_t9jul1_2_3_4.csv` | tabular | 1272178 |
| `dataset/timesafe/s-plane_security_repo/Archive/Datasets/t7jul_lat_ext_t9jul1_2_3_4_5.csv` | tabular | 1311270 |
| …and 197 more | | |

## 5. Model checkpoint inventory

291 `.pth` files. **Training-data provenance for these checkpoints is not established by this inventory.** Reading a checkpoint's archive listing says what tensors it holds, not what data produced them.

| Path | Zip archive | Entries | Uncompressed bytes |
|---|---|---|---|
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.1.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.2.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.3.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.5.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.7.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/LSTM/best_model2.9.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/Transformer/best_model_tr.2.16.pth` | True | 34 | 319949 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/Transformer/best_model_tr.2.32.pth` | True | 34 | 418253 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/Transformer/best_model_tr.2.40.pth` | True | 34 | 467405 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/RU_model/Transformer/best_model_tr_new.3.40.pth` | True | 34 | 467405 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.16.pth` | True | 34 | 319949 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.24.pth` | True | 34 | 369101 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.32.pth` | True | 34 | 418253 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.48.pth` | True | 34 | 516561 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.56.pth` | True | 34 | 565713 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/Archive/temp/best_model_t7jul_lat_ext_9jul1_2_3_4_5_6_tr.3.8.pth` | True | 34 | 270797 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/CNN/best_model_CNN.1.pth` | True | 12 | 86311 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/CNN/best_model_cnn.pth` | True | 12 | 86549 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.1.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.10.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.100.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.2.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.3.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.4.pth` | True | 7 | 74716 |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data/external/s-plane_security_repo/DU_model/LSTM/best_model1.5.pth` | True | 7 | 74716 |
| …and 266 more, all recorded in the JSONL | | | |

## 6. Unreadable or unparsed

None. Every file opened either parsed or was recorded as OPAQUE with size and hash.

## 7. What this does and does not close

Closes: every file in the four roots has now been opened by a tool and inventoried, and the duplicate map covers the whole repository rather than one directory.

Does not close: an inventory is not a dependency trace. Knowing a checkpoint's tensor names does not establish which captures trained it. Criterion 2 stays BLOCKED_EXTERNAL for the provenance question; what this removes is the excuse that the files were never read.

