# Active S-Plane Self-Healing Prototype

Runnable CPU-only implementation of a governed O-RAN Open Fronthaul synchronization-security loop:

```text
detect anomaly -> classify H0/H1 or UNKNOWN -> verify recovery in twin -> act before 2 s
```

## Run

```bash
python -m pip install -r requirements.txt
python scripts/run_all.py
python scripts/run_tier2.py
python -m pytest tests -p no:cacheprovider
```

The complete suite has **39 passing tests**.

## Shipped model

- **28 enabled features:** timing, delay/PDV, protocol regularity, message rate, BMCA transitions, time-source state, and oscillator consistency.
- Group-wise open-set detection with weighted Šidák budget allocation.
- 2-of-3 persistence for UNKNOWN and H1 decisions.
- Digital-twin action forecasts, fidelity discounting, and auditable safe-default routing.
- Deterministic pure-Python simulation by default; pcap, `ptp4l`, `pmc`, `synce4l`, and Linux/netem adapters for Tier 2.

The seven `cross_source` research features are retained but disabled by default in `config/default.yaml`. Enabling the flag produces a 35-feature research model; the dedicated evaluator reproduces why it is not shipped.

## Final protection after 2-of-3 persistence

| Domain | Family | Protection | Within 2 s |
|---|---|---:|---:|
| Simulator | Spoof | 93.30% | 100% |
| Simulator | Replay | 80.45% | 100% |
| Simulator | DoS | 88.27% | 100% |
| Simulator | GNSS jam | 91.57% | 100% |
| Simulator | Strict unseen GNSS spoof | 0.00% | 0% |
| TIMESAFE | Announce | 99.96% | 100% |
| TIMESAFE | Follow-Up | 99.66% | 100% |
| TIMESAFE | Single-Step | 99.66% | 100% |

## Research conclusion

BMCA features, group-wise novelty, persistence, and oscillator consistency produced measurable gains. Receiver status alone and cross-source feature engineering did not solve strict unseen GNSS spoofing. A healthy-looking spoof is in-distribution from a single reference; further progress requires independently trustworthy Tier-3 evidence such as authenticated GNSS or a physical independent clock.

See `docs/SOFTWARE_FEATURE_WORK_CLOSED.md`, `docs/MULTISOURCE_EVAL.md`, and `docs/GNSS_TIMESOURCE_EVAL.md` for the complete evidence and negative results.
