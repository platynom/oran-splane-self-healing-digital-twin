# Active S-Plane Self-Healing Prototype

This directory contains the runnable implementation of an AI-native,
self-healing O-RAN Open Fronthaul synchronization-plane prototype.

```text
detect anomaly
  -> discriminate H0 benign fault vs H1 attack
  -> forecast candidate actions in a digital twin
  -> commit the best verified recovery before the 2 s failure window
```

The contribution is integration, experimental validation, and reproducible
dataset generation. It is not presented as a new fundamental ML algorithm.

## Quick start

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate              # Linux/macOS
# .venv\Scripts\Activate.ps1           # Windows PowerShell

python -m pip install -r requirements.txt
python scripts/run_all.py
python -m pytest tests -p no:cacheprovider
```

`scripts/run_all.py` regenerates the labelled simulator dataset, trains the
discriminator, validates the twin, runs the governed healing benchmark, and
writes results. The default path is deterministic and CPU-only.

## Tier 2: realistic software validation

```bash
python scripts/run_tier2.py
```

Tier 2 adds:

- multi-seed means and 95% confidence intervals;
- leave-one-attack-family-out evaluation;
- capture-level train/test isolation for real-data calibration;
- PTP-over-Ethernet pcap ingestion;
- Announce, Sync, Follow_Up, Delay_Req, and Delay_Resp parsing;
- `ptp4l`, `pmc`, and `synce4l` text ingestion;
- a real `tc netem` plus `linuxptp` harness over Linux veth interfaces;
- digital-twin fidelity and action-ranking validation.

See:

- [Tier 2 design](docs/TIER2_DESIGN.md)
- [Real-feature audit](docs/REAL_FEATURES_AUDIT.md)
- [Real-data validation](docs/REAL_DATA_VALIDATION.md)
- [Linux/netem instructions](RUN_ON_REAL_LINUX.md)
- [Tier 2 report](results/tier2/TIER2_REPORT.md)

## Package map

| Directory | Responsibility |
|---|---|
| `fronthaul_sim/` | Deterministic PTP servo, SyncE aid, GNSS and holdover simulation |
| `faults/` | H0 faults and H1 spoof/replay injection |
| `telemetry/` | Window-level timing and protocol features |
| `discriminator/` | H0/H1 classifier training and evaluation |
| `twin/` | Per-action timing forecasts and fidelity scoring |
| `healing/` | Governed detect/discriminate/verify/commit loop |
| `ingest/` | Pcap, linuxptp, pmc and synce4l adapters |
| `harness/` | Privileged Linux/netem capture experiments |
| `stats/` | Confidence intervals and generalization tests |
| `benchmark/` | Baseline comparison and recovery metrics |
| `tests/` | Unit and integration tests |

## Measured status

- Full test suite: 16 passing tests.
- Real capture features: 9 of 10 non-constant.
- Capture-isolated known-family evaluation: approximately 2% benign FP and
  100% attack TP on the current holdout.
- Unseen Announce-family recall: approximately 24%, the main open limitation.
- Hardware validation: not yet performed.

Raw public datasets and pcaps are intentionally excluded from Git. Use the
documented acquisition and preparation scripts to reproduce external-data
experiments.
