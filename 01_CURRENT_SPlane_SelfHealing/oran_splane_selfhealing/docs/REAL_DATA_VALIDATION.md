# Real Data Validation

Date: 2026-07-27

## Data

External capture:

- Repository: `genesys-neu/s-plane_security`
- Pcap: `DataCollectionPTP/prod_successful_announce_attack_ptp.pcap`
- Ingested telemetry: `results/tier2/timesafe_external_telemetry.csv`
- Windows: `results/tier2/timesafe_external_windows.csv`

Ingestion recovered:

| Metric | Value |
|---|---:|
| Telemetry samples | 3910 |
| Duration | 240.714 s |
| Windows | 1195 |
| Offset mean | 13907.367 ns |
| Offset absolute max | 588904.000 ns |
| Path-delay mean | 33722.059 ns |
| Path-delay std | 47046.364 ns |

## Matching Labels

The matching processed TIMESAFE CSV was downloaded from the public GitHub blob:

- `DataCollectionPTP/prod_successful_announce_attack_ptp.csv`
- `DU_model/Datasets/Original/prod_successful_announce_attack.csv`

The PTP CSV has packet fields only. The processed CSV has a binary `Label` column. Using cumulative `Time Interval` as the packet time base, it contains 200 labeled attack packets, all Announce messages (`MessageType == 11`), from approximately 78.507 s to 105.308 s.

Window overlap with labeled attack packets:

| Overlaps Label 1 | Windows |
|---|---:|
| False | 1067 |
| True | 128 |

## Sim-Trained Discriminator Transfer

A discriminator was trained on the current simulator-generated H0/H1 windows using the same model family as `discriminator.model.train_and_evaluate()`:

- `RandomForestClassifier(n_estimators=90, max_depth=6, class_weight="balanced")`
- Features: `telemetry.features.FEATURE_COLUMNS`
- No retraining on TIMESAFE data was performed.

Predictions on 1195 real TIMESAFE windows:

| Metric | Value |
|---|---:|
| Anomalous by 100 ns budget | 1.000 |
| Predicted H1 fraction | 1.000 |
| Mean H1 probability | 0.885 |
| 95th percentile H1 probability | 0.963 |

Alignment with labels:

| Overlaps Label 1 | Predicted H1 Windows |
|---|---:|
| False | 1067 |
| True | 128 |

The model flags the labeled attack interval, but it also flags every non-attack-overlapping window as H1. That is not acceptable real-data transfer; it is a domain-gap result, not a validated production classifier.

## Domain Gap

Feature distribution comparison, simulator windows vs TIMESAFE real windows:

| Feature | Sim Median | Sim P95 | Real Median | Real P95 | Real/Sim Median Ratio |
|---|---:|---:|---:|---:|---:|
| offset_abs_max | 22.175 | 336.400 | 59958.000 | 451354.800 | 2703.848 |
| offset_std | 8.970 | 59.088 | 46366.098 | 221780.527 | 5169.199 |
| path_delay_mean | 50001.008 | 50067.407 | 30516.000 | 92161.124 | 0.610 |
| pdv_std | 18.458 | 35.676 | 16359.987 | 91345.508 | 886.345 |
| seq_regressions | 0.000 | 2.650 | 0.000 | 0.300 | n/a |
| msg_irregularity | 0.000 | 0.000 | 0.000 | 0.000 | n/a |

The real capture is orders of magnitude noisier in offset variation and PDV than the simulator. Because the current discriminator learned mostly offset-magnitude and variance cues, it treats the real baseline noise floor as attack-like.

## Conclusion

The real-data pipeline works mechanically: public pcap download, pcap ingestion, feature windowing, sim-trained inference, and label alignment all run end to end.

The sim-trained discriminator does not transfer cleanly to this TIMESAFE trace. It detects the labeled Announce attack segment, but its false-positive behavior on the rest of the trace means it needs real-feature calibration or retraining before any honest claim of external-data performance.

Recommended next steps, not applied here:

1. Add a calibration split using benign real PTP traces from the same capture environment.
2. Normalize offset and PDV features relative to a per-trace healthy baseline.
3. Add protocol-state features for Announce/source-clock anomalies so attack detection does not depend mainly on raw timing magnitude.
4. Report external validation separately from simulator validation until enough labeled real traces exist for a proper train/test split.
