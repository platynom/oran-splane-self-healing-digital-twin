# AI-Native Self-Healing O-RAN S-Plane Digital Twin

This repository builds a laptop-runnable research prototype for an AI-native self-healing loop for the O-RAN Open-Fronthaul synchronization plane. It focuses on integration, experimental validation, and a released labelled dataset rather than claiming a new fundamental ML algorithm.

The loop is:

`detect sync anomaly -> discriminate H0 benign fault vs H1 attack -> verify candidate recovery actions in a digital twin -> commit the best action before the 2 s failure window`.

## Quick Start

```powershell
cd "C:\Users\Admin\Documents\AI-Native Self-Healing O-RAN Network using a Digital Twin\oran_splane_selfhealing"
pip install -r requirements.txt
python scripts/run_all.py
python -m pytest tests -p no:cacheprovider
```

No PTP NIC, O-RU, linuxptp, or GPU is required. The default backend is a deterministic pure-Python PTP/SyncE simulator. Hardware and linuxptp integrations are left as labelled stubs.

## Outputs

- `dataset/splane_windows.csv`: generated labelled window dataset.
- `dataset/DATASHEET.md`: dataset provenance and limitations.
- `results/discriminator_metrics.csv`: H0/H1 classifier and detection-only baseline.
- `results/benchmark_results.csv`: full loop vs baselines.
- `results/*.png`: benchmark plots.
- `results/SUMMARY.md`: final phase mapping and headline numbers.

## Monetizable / Resume Positioning

This is packaged as a reproducible network-security validation asset: a labelled S-plane timing dataset, governed self-healing loop, and benchmark harness that can be shown as a deployable research demo for telecom security, digital twins, and AI-native RAN operations.
