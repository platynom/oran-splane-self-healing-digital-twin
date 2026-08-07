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
Full suite: **56 tests passing**.

## Verification beyond unit test

Emulation and unit tests were the first gate. The original trigger — a real `pmc`
outage on a live `ptp4l` pair — was then reproduced directly; see the next section.

## Live verification against real linuxptp (residual limitation closed)

The fix was subsequently validated against **real `ptp4l` 3.1.1 traffic**, not only
emulation. A master/slave pair was run over a veth pair inside an unprivileged user
namespace (rootless: `unshare --user --map-root-user --net --mount`), with
`tc netem` applied to the master link.

**Healthy state** — real `pmc` from a converged slave:

```
offsetFromMaster -1275.0
meanPathDelay     2375.0
gmPresent         true
portState         UNCALIBRATED
```

**Total outage** — `tc qdisc add dev m0 root netem loss 100%` plus master killed:

```
offsetFromMaster  550.0        <-- STALE, still numerically plausible
meanPathDelay    1350.0        <-- STALE
gmPresent         true         <-- STALE
portState         LISTENING    <-- the only honest field
```

This is an important real-world result: after the master disappears, `pmc` does
**not** return zeros or errors — it keeps serving the *last known* values
indefinitely. A collector that trusts the numbers alone would ingest plausible
offsets forever during a complete outage. The zero-valued case seen in earlier
live testing is only one manifestation; staleness is the more dangerous one
because the values look entirely reasonable.

`scripts/live_collect.py` gates on `portState` (and GM presence) rather than on the
numbers, so both manifestations are caught. End-to-end through the real pipeline
(`parse_live_pmc` → `coerce_telemetry` → `window_features` → `choose_action`):

| Real capture | telemetry_valid | Label | Action | Classifier reached |
|---|---|---|---|---|
| Healthy (converged slave) | `True` | `H0` | `failover_lls_c1` | yes |
| Total loss (stale pmc) | `False` | `UNKNOWN` | `safe_default` | **no** |

The classifier and novelty detector are correctly bypassed for invalid telemetry,
and healthy traffic still flows through the full decision path. The residual
limitation recorded above — "needs a privileged Linux re-run to confirm end to
end" — is therefore **closed**.

Reproduce (no root required on a kernel permitting unprivileged user namespaces):

```bash
apt-get download linuxptp && dpkg-deb -x linuxptp_*.deb ./lp
unshare --user --map-root-user --net --mount bash   # then set up veth + ptp4l
```
