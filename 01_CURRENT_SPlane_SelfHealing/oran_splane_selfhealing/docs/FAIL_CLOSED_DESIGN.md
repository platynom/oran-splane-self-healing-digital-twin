# Fail-Closed Telemetry Handling

## The defect

Live validation exposed a **fail-open** path. Under severe packet loss `pmc`
returned no timing fields; `scripts/live_collect.py` substituted `0.0`; and
`healing/loop.py::detect()` read `offset_abs_max == 0` as "below threshold" and
returned `label="healthy"` with reason *"no anomaly above configured threshold"*.

Two properties made this serious rather than cosmetic:

1. **It bypassed every safety layer.** The early return fired *before* the
   group-wise novelty detector, the classifier and temporal persistence. The
   open-set protection built over three increments never executed.
2. **It was attacker-inducible.** Flooding the link suppresses `pmc` responses,
   so an adversary could silence the detector precisely while attacking it.

The same pattern existed independently in the digital twin:
`twin/model.py::fidelity_score()` used `window.get(key, 0.0)`, so **absent inputs
produced zero penalty and therefore fidelity 1.0** — maximum trust from no data.
Measured before the fix: `fidelity_score(pd.Series({"offset_abs_max": 300.0})) == 1.0`.
That also disabled the `fidelity < 0.35` conservative fallback in the healing loop.

## The governing principle

> Missing data is a *first-class state*, never a value. A component that cannot
> prove its inputs were observed must refuse to certify health.

"Nothing received" and "perfectly synchronised" are different states and must
never share a representation.

## Implementation

**Provenance in the schema** (`ingest/schema.py`)
`offset_valid`, `path_delay_valid` and `telemetry_valid` are carried per sample.
Absent timing stays `NaN` — it is never filled with `0.0`, so a genuine 0 ns
offset remains distinguishable from an unobserved one.

**Adapters emit truth, not placeholders**
`live_collect.py` (`_number` defaults to `None`), `linuxptp_ingest.py` and
`pcap_ingest.py` propagate NaN plus the validity flags. Collection stays
resilient — it records the gap rather than crashing or inventing a value.

**Windows carry provenance** (`telemetry/features.py`)
Each window exposes `telemetry_valid`, `valid_sample_rate` and
`valid_sample_fraction`. A window is valid only if every sample was observed and
at least three samples exist.

**The decision gate fails closed** (`healing/loop.py::telemetry_is_valid`)
Checked at the *top* of `choose_action`, before `detect()`. A window is rejected
when: it declares `telemetry_valid=False`; its valid fraction is `< 1.0` or NaN;
a required decision feature is missing, NaN or non-finite; **or it carries no
provenance metadata at all**. Invalid telemetry routes to `UNKNOWN` →
`safe_default`, on its own `"invalid"` persistence channel so outages do not
pollute the H1/novelty histories.

The last clause matters: an absent flag is treated as *untrusted*, not trusted.
Assuming validity is the exact convention that caused the original defect —
absence of evidence is not evidence of health.

**The twin fails closed** (`twin/model.py::fidelity_score`)
Returns `MIN_FIDELITY` (0.15) when its inputs are missing, NaN, flagged invalid,
or lack provenance. Post-guard reads are direct (`window["pdv_std"]`) rather than
`.get(..., 0.0)`, so a future regression surfaces instead of hiding.

## Verified behaviour

| Input | Before | After |
|---|---|---|
| All-zero `pmc` window | `healthy` | `UNKNOWN` + `safe_default` |
| NaN offset | *(undefined)* | `UNKNOWN` + `safe_default` |
| Non-finite (`inf`) feature | *(undefined)* | `UNKNOWN` + `safe_default` |
| `telemetry_valid=False` | *(no such state)* | `UNKNOWN` + `safe_default` |
| 50 % sample loss | `healthy` | `UNKNOWN` + `safe_default` |
| Window without provenance | `healthy` | `UNKNOWN` + `safe_default` |
| Genuine healthy traffic | `healthy` | `healthy` (unchanged) |
| `fidelity_score` on missing inputs | **1.0** | **0.15** |
| `fidelity_score` on healthy window | 0.977 | 0.977 (unchanged) |

Pinned by `tests/test_missing_data_safety.py` (10 tests). These were written
**before** the fix and failed against the original code, so they test the defect
rather than the implementation.

## No regression

`run_all.py`: accuracy 0.990, recovery 1.000, MTTR 0.935 s.
Multi-seed (8 seeds): accuracy **0.991 ± 0.002**, ROC-AUC **1.000 ± 0.000**,
recovery **1.000 ± 0.000**, MTTR **0.933 ± 0.008 s**.
Twin vs simulator: Pearson **0.998**, Spearman **0.873**.
Fidelity still degrades correctly with telemetry quality
(corr vs `pdv_std` −0.731, vs `seq_regressions` −0.898; healthy mean 0.901).
pcap ingestion: 797 samples, MAE **14.68 ns**, path delay 49 998 ns.
Full suite: **53 tests passing**.

## Residual limitation

The fix is verified in emulation and by unit test. The original trigger — a real
`pmc` outage under severe loss on a live `ptp4l` pair — needs a privileged Linux
re-run to confirm end-to-end:

```bash
sudo ./harness/netem_harness.sh holdover 90 results/tier2/netem/holdover.pcap
sudo python -m harness.run_netem_scenarios --scenarios loss holdover --duration 90
```

Expected: the zero-valued `pmc` windows that previously read `healthy` now
produce `UNKNOWN`/protective decisions.
