# Tier 2 — Realistic Software Validation Report

Generated: 2026-08-04T16:40:12  |  seeds: [1588, 2026, 7, 42, 101, 900, 31415, 27182]

This report upgrades the single-run prototype numbers to multi-seed confidence intervals, tests generalization to unseen attacks, validates the digital twin, and proves the real-trace ingestion path — all CPU-only, no hardware.

## 1. Multi-seed metrics (mean ± 95% CI)

- Discriminator accuracy: **0.983 ± 0.007**
- Discriminator macro-F1: **0.982 ± 0.007**
- Discriminator ROC-AUC (H1): **0.999 ± 0.001**
- Governed-loop recovery success: **0.960 ± 0.027**
- Governed-loop wrong-action rate: **0.037 ± 0.026**
- Governed-loop mean MTTR (s): **0.755 ± 0.021**

See `multiseed_summary.csv`, `multiseed_per_seed.csv`, `multiseed_ci.png`.

## 2. Leave-one-attack-out generalization

Discriminator trained with an entire attack family removed, then tested on it (can it catch an attack type it never saw?):

  - held out **spoof** (`ptp_spoof`) -> recall on unseen family: 0.894 (n=179)
  - held out **replay** (`ptp_replay`) -> recall on unseen family: 0.430 (n=179)
  - held out **dos** (`ptp_dos_flood`) -> recall on unseen family: 0.000 (n=179)

## 3. Digital-twin validation

- Twin vs simulator action-ranking: Pearson r = **0.998**, Spearman r = **0.873**, MAE = 54.99 ns (twin action model is consistent with ground-truth simulator physics).
- Fidelity-score behaviour vs telemetry degradation: corr_fidelity_vs_pdv_std=-0.727, corr_fidelity_vs_seq_regressions=-0.902.
  Negative correlations mean fidelity correctly drops as telemetry degrades. See `twin_action_consistency.csv`, `fidelity_behaviour.csv`.

  *Caveat:* fully calibrating fidelity against real twin prediction error needs hardware-timestamped ground truth; this validates internal consistency and intended behaviour.

## 4. Real-trace ingestion self-test (PTP pcap)

- Synthetic PTP-over-Ethernet capture ingested: **797 offset samples** recovered.
- Offset recovery MAE vs injected ground truth: **14.68 ns** (dominated by per-sample path-delay variation, as in real PTP).
- Recovered mean path delay: 49998.2 ns.
  The SAME `pcap_to_telemetry()` consumes a real released capture — set `data_source.backend: pcap` and `pcap_path` in config.

## 5. linuxptp parser self-test

- Parsed **5 servo samples** from a ptp4l log fixture into canonical telemetry.
  On your Linux box: `ptp4l -i eth0 -m -q -s -S > ptp4l.log` then `ptp4l_log_to_telemetry(...)`; or run `harness/run_netem_scenarios.py` for live netem captures.

## What remains before hardware

- Run `harness/run_netem_scenarios.py` on a Linux box (root + linuxptp) to fold REAL netem-degraded captures into the dataset.
- Point `pcap_path` at a released public S-plane/TIMESAFE capture for external-data validation.
