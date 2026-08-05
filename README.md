# O-RAN S-Plane Self-Healing Digital Twin

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-18%20passed-2ea44f)](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

An AI-native, CPU-only research prototype for detecting timing anomalies,
distinguishing benign synchronization faults from attacks, verifying recovery
actions in a digital twin, and committing the best response before an O-RAN
fronthaul timing failure.

The project focuses on **integration, reproducible experimentation, and honest
validation**. It does not claim a new fundamental machine-learning algorithm.

## Why this matters

O-RAN Open Fronthaul depends on precise synchronization from PTP (IEEE 1588),
SyncE, and GNSS. Timing manipulation can disrupt a base station in seconds.
Detection alone is not enough: an operational system must determine what
happened, select a recovery action, and verify that the action will keep time
error inside its budget.

```text
PTP / SyncE telemetry
        |
        v
 anomaly detection
        |
        v
 H0 benign fault vs H1 attack
        |
        v
 digital-twin action forecasts
        |
        v
 governed recovery decision
```

Supported recovery actions include source failover, GNSS failover, holdover,
rogue-master isolation, path rerouting, and a conservative safe default.

## Validation snapshot

The current checkpoint contains simulator, Linux/netem, and public TIMESAFE
validation. Real-data evaluation keeps complete capture sessions isolated
between training and testing.

| Evaluation | Benign false-positive rate | Attack true-positive rate |
|---|---:|---:|
| Simulator-trained RF on real captures | 100% | 100% |
| Real-calibrated threshold, session holdout | 2.0% | 100% |
| Real-trained RF, session holdout | 2.0% | 100% |
| Unseen Announce attack family | 0% | 23.8% |
| Unseen Sync/Follow_Up family | 0% | 100% |
| Unseen one-step Sync family | 1.9% | 100% |

Simulator leave-one-attack-family-out results now include the self-generated
DoS/message-flooding family and its benign traffic-burst confounder:

| Held-out simulated family | Attack recall |
|---|---:|
| Spoof | 89.4% |
| Replay | 43.0% |
| DoS/message flooding | 0.0% |

When DoS is represented during training, held-run tests achieve 100% DoS recall
with 0% traffic-burst false positives. A naive 4x-rate rule flags 100% of both,
showing why message-rate mean and variance must be evaluated with other features.
The zero unseen-DoS result remains an explicit open-set generalization gap.

The weak unseen-Announce result is intentional to report: it is the main open
research gap, not a hidden failure. Five independent public captures were used,
so the real-data results are promising but not production certification.

Detailed evidence:

- [Plain-language project status](01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md)
- [Real-feature audit](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/REAL_FEATURES_AUDIT.md)
- [Capture-isolated calibration report](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results/tier2/real_calibration/REAL_CALIBRATION_REPORT.md)
- [Tier 2 statistical report](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results/tier2/TIER2_REPORT.md)

## Quick start

```bash
cd 01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
python scripts/run_all.py
python -m pytest tests -p no:cacheprovider
```

The default Tier 1 workflow is deterministic, CPU-only, and needs no PTP NIC,
O-RU, GPU, paid API, or network connection after dependency installation.

For realistic software validation:

```bash
python scripts/run_tier2.py
```

Linux users can also run the `tc netem`/`linuxptp` harness described in
[RUN_ON_REAL_LINUX.md](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/RUN_ON_REAL_LINUX.md).

## Repository layout

```text
01_CURRENT_SPlane_SelfHealing/
  oran_splane_selfhealing/   active simulator, ingest, ML, twin, healing, tests
  deliverables/              review presentation and project documents
  literature-survey/         indexes and literature-analysis notes

02_PREVIOUS_Work/
  gen1_RRC_PPO/              superseded RRC/PPO direction
  gen2_KPM_FlexRIC_twin/     superseded general KPM/FlexRIC twin direction
```

Raw pcaps, external datasets, virtual environments, caches, and large generated
artifacts are deliberately excluded from Git history. The code can regenerate
the synthetic dataset and benchmark outputs. Public TIMESAFE data is referenced
for reproducibility but is not redistributed here.

## Product direction

The prototype can evolve into a vendor-neutral timing-security validation
service for labs, private 5G operators, and telecom vendors:

- offline pcap and telemetry assessment;
- CI regression tests for timing resilience;
- governed remediation recommendations with an audit trail;
- live O-DU/O-RU integration through linuxptp events and O-RU M-plane
  NETCONF/YANG synchronization telemetry.

Tier 3 still requires a hardware-timestamping NIC, representative O-DU/O-RU or
clock equipment, a real SyncE source, and controlled authorized attack tests.

## Safety and scope

Attack-related tooling is included only for defensive research and authorized
test environments. Do not run timing-manipulation experiments against networks
or equipment you do not own or have explicit permission to test.

See [SECURITY.md](SECURITY.md) for responsible disclosure.

## License

Project-authored code and documentation are released under the [MIT License](LICENSE).
Third-party datasets, papers, standards, and archived upstream material retain
their original licenses and are not relicensed by this repository.
