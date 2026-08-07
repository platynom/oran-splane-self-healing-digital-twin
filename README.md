# O-RAN S-Plane Self-Healing Digital Twin

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-53%20passed-2ea44f)](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A CPU-only research prototype that detects O-RAN Open Fronthaul synchronization anomalies, distinguishes benign timing faults from attacks, evaluates recovery actions in a digital twin, and selects an auditable response before the approximately two-second failure window.

The contribution is system integration, experimental validation, and reproducible dataset generation, not a new fundamental ML algorithm.

## Final software configuration

The shipped model uses **28 features** across timing, protocol, message rate, BMCA/grandmaster transitions, receiver time-source state, and oscillator physics consistency. Group-wise Isolation Forests use a weighted Šidák budget, and **2-of-3 persistence** is applied independently to UNKNOWN and RF-H1 decisions.

Seven experimental cross-source features and their three-reference simulator remain available behind:

```yaml
features:
  cross_source:
    enabled: false
```

They are disabled by default because the experiment added no combined-protection gain and regressed established families. Default training and benchmarks exclude the research-only multi-source scenarios; `stats/multisource_eval.py` reproduces the comparison explicitly.

## Final validated results

Combined protection means H1 classification or conservative UNKNOWN routing after 2-of-3 persistence.

| Domain | Held-out family | Protection | Episodes within 2 s |
|---|---|---:|---:|
| Simulator | Spoof | 93.30% | 100% |
| Simulator | Replay | 80.45% | 100% |
| Simulator | DoS/message flooding | 88.27% | 100% |
| Simulator | GNSS jam | 91.57% | 100% |
| Simulator | Strict unseen GNSS spoof | 0.00% | 0% |
| TIMESAFE | Announce/BMCA | 99.96% | 100% |
| TIMESAFE | Sync/Follow-Up | 99.66% | 100% |
| TIMESAFE | Single-step Sync | 99.66% | 100% |

On TIMESAFE, 2-of-3 persistence reduced benign false positives from **4.49% to 2.37%** without compromising the two-second deadline.

## What the experiments established

- BMCA transition features moved real unseen Announce protection from 23.9% to approximately 100%.
- Group-wise open set recovered the original unseen-DoS miss from 0% to approximately 94% and improved replay coverage.
- Oscillator consistency solved unseen GNSS jamming but not a healthy-looking unseen GNSS spoof.
- Receiver-reported GNSS status is attacker-influenced and cannot be trusted alone.
- Cross-source features added no incremental protection in this software experiment and remain gated off.
- Coherent compromise of every reference is undetectable by relative agreement; its cross-source gain is 0.00 percentage points.

The standing limit is physical: a spoof that perfectly mimics healthy operation is in-distribution from a single reference. Detection requires independently trustworthy evidence such as authenticated GNSS, a physically independent clock, or Tier-3 hardware cross-checking.

## Reproduce

```bash
cd 01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_all.py
python scripts/run_tier2.py
python -m pytest tests -p no:cacheprovider
```

## Evidence

- [Project status](01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md)
- [Software feature-work closure](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/SOFTWARE_FEATURE_WORK_CLOSED.md)
- [Multi-source negative result](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/MULTISOURCE_EVAL.md)
- [GNSS evaluation](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/GNSS_TIMESOURCE_EVAL.md)
- [Open-set and persistence evaluation](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/OPENSET_EVAL.md)

## Honest limitations

- TIMESAFE has no benign planned-grandmaster-change session, so deployment false positives may be higher.
- Announce-trained closed-set RF tested on Sync sessions has 0% recall.
- SyncE quality requires live `synce4l` or O-RU M-plane telemetry and cannot be recovered from ordinary pcaps.
- Real evaluation contains few independent attack sessions.
- No hardware timestamping NIC, physical clock, authenticated GNSS receiver, O-DU, or O-RU has been validated.

This is a reproducible research prototype, not production certification. The next justified work is Tier 3 hardware validation, not additional single-source feature engineering.
