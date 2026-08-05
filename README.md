# O-RAN S-Plane Self-Healing Digital Twin

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-28%20passed-2ea44f)](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/tests)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A CPU-only research prototype for detecting O-RAN fronthaul synchronization
anomalies, distinguishing benign timing faults from attacks, checking recovery
actions in a digital twin, and selecting a governed response before the
approximately two-second failure window.

The contribution is **system integration, experimental validation, and a
released labelled synthetic dataset**. It is not presented as a new fundamental
machine-learning algorithm.

## System

O-RAN Open Fronthaul timing depends on PTP (IEEE 1588), SyncE, and GNSS. The
implemented loop is:

```text
PTP / SyncE / GNSS telemetry
          |
          v
 anomaly detection
          |
          v
 known H0 fault / known H1 attack / UNKNOWN novel event
          |
          v
 digital-twin recovery forecasts and fidelity check
          |
          v
 governed action or conservative safe default
```

The action space includes timing-source and GNSS failover, holdover,
rogue-master isolation, path rerouting, and a safe default.

## Current validated checkpoint

- **19 model features** cover timing error, delay/PDV, protocol sequence and
  message regularity, message rate, GNSS/holdover/SyncE state, and relative BMCA
  transitions such as grandmaster churn, clock-class changes, priority changes,
  and `stepsRemoved` changes. Raw grandmaster identity is never a model feature.
- A **group-wise open-set ensemble** fits independent Isolation Forests to
  timing, protocol, rate, and BMCA feature groups. A weighted Šidák allocation
  keeps their intended combined known-window novelty budget near 2%.
- **2-of-3 temporal persistence** is applied independently to UNKNOWN and RF-H1
  decisions. This suppresses isolated votes while adding 0.2-0.4 s mean latency
  in the recommended setting.
- Evaluation uses deterministic simulation, real `linuxptp`/netem traffic, and
  public TIMESAFE captures with complete capture sessions isolated between
  training and testing.
- **28 pytest tests pass** on the current checkpoint.

### Protection after 2-of-3 persistence

Combined protection means a window is either classified H1 or safely routed as
UNKNOWN.

| Domain | Held-out family | Combined protection |
|---|---|---:|
| Simulator | Spoof | 83.8% |
| Simulator | Replay | 63.7% |
| Simulator | DoS/message flooding | 86.0% |
| TIMESAFE | Announce/BMCA | 99.96% |
| TIMESAFE | Sync/Follow-Up | 99.66% |
| TIMESAFE | Single-step Sync | 99.66% |

Weighted TIMESAFE benign false positives fall from 4.49% at 1-of-1 to **2.37%**
at 2-of-3. All evaluated real attack episodes are detected within **0.2 s**.
The worst fraction detected and acted on inside the 2.0 s window is **91.7%**,
from simulated spoof; one run is already late under 1-of-1, so persistence does
not reduce that within-window rate.

Window alarms/hour counts every persisted positive window. Contiguous positives
are one operator-facing episode: on the short held TIMESAFE benign captures,
weighted episode alarms/hour fall from about 570 at 1-of-1 to about 190 at
2-of-3. These hourly figures are extrapolations, not long-duration field rates.

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
python scripts/run_tier2.py
python -m pytest tests -p no:cacheprovider
```

Tier 1 needs no PTP NIC, O-RU, GPU, paid API, or network after dependency
installation. Tier 2 uses local captures by default and can optionally use a
Linux `tc netem`/`linuxptp` environment described in
[RUN_ON_REAL_LINUX.md](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/RUN_ON_REAL_LINUX.md).

## Evidence

- [Current project status](01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md)
- [Open-set, BMCA, persistence, and episode evaluation](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/OPENSET_EVAL.md)
- [Real-feature audit](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/docs/REAL_FEATURES_AUDIT.md)
- [Capture-isolated calibration report](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results/tier2/real_calibration/REAL_CALIBRATION_REPORT.md)
- [Tier 2 statistical report](01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/results/tier2/TIER2_REPORT.md)

## Repository layout

```text
01_CURRENT_SPlane_SelfHealing/
  oran_splane_selfhealing/   active simulator, ingest, ML, twin, healing, tests
  deliverables/              review presentation and project documents
  literature-survey/         literature indexes and analysis notes

02_PREVIOUS_Work/            superseded directions, retained read-only
```

Raw pcaps, external datasets, virtual environments, caches, and large generated
artifacts are excluded from Git history. Public TIMESAFE data is referenced for
reproducibility but is not redistributed.

## Honest limitations

- TIMESAFE contains no benign planned grandmaster-change session. The measured
  real benign false-positive rate is therefore optimistic for deployments with
  legitimate re-parenting.
- Closed-set specialization remains: an RF trained on Announce sessions and
  tested on Sync sessions has **0% recall**. Open-set safe routing mitigates but
  does not solve family classification.
- SyncE quality level cannot be reconstructed from pcaps and still requires a
  live `synce4l` reader or O-RU M-plane NETCONF/YANG telemetry.
- There is no hardware validation yet. Tier 3 needs hardware timestamps, a real
  SyncE source, representative clock/O-DU/O-RU equipment, and controlled
  authorized attack experiments.
- The real evaluation has few independent attack sessions. Reported percentages
  are research evidence, not production certification.

## Product direction

The prototype can evolve into a vendor-neutral timing-security validation tool
for telecom labs, private 5G operators, and equipment vendors: offline capture
assessment, resilience regression tests, governed remediation recommendations,
and auditable live synchronization monitoring.

Attack tooling is for defensive research on systems the operator owns or is
authorized to test. See [SECURITY.md](SECURITY.md). Project-authored code and
documentation are released under the [MIT License](LICENSE).
