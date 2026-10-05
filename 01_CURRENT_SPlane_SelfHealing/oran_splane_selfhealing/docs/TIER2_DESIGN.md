# Tier 2 — Realistic Software Validation (Design)

Tier 1 = the pure-Python emulation prototype (`run_all.py`). Tier 2 closes the
credibility gap **before any hardware**, using only an ordinary Linux box.

## What Tier 2 adds and why

| Piece | Module | Why it matters | Runs where |
|---|---|---|---|
| Multi-seed CIs | `stats/multiseed.py` | Turns single-run point estimates into mean ± 95% CI; kills the "lucky seed" critique | CPU-only, here |
| Leave-one-attack-out | `stats/multiseed.py` | Tests generalization to an attack family never trained on | CPU-only, here |
| Twin validation | `stats/twin_validation.py` | Confirms the twin's action ranking matches the simulator, and that fidelity drops on degraded telemetry | CPU-only, here |
| pcap ingestion | `ingest/pcap_ingest.py`, `ingest/ptp_wire.py` | Consumes real PTP-over-Ethernet captures via the standard IEEE-1588 E2E offset math | CPU-only parse; needs a capture |
| linuxptp ingestion | `ingest/linuxptp_ingest.py` | Parses real `ptp4l`/`phc2sys` servo output into the same schema | CPU-only parse |
| netem harness | `harness/netem_harness.sh`, `harness/run_netem_scenarios.py` | Generates REAL degraded PTP traffic over a veth pair (no PTP NIC) and captures it | Linux + root + linuxptp |

## Key design choice: one canonical schema

`ingest/schema.py` defines `TELEMETRY_COLUMNS`. The simulator and every real-data
adapter emit that exact schema, so `telemetry.features -> discriminator -> twin ->
healing` run **unchanged** on synthetic, pcap, or linuxptp inputs. Switching source
is a config flag (`data_source.backend`), not a code change.

## Honest boundaries (what Tier 2 does NOT claim)

- The netem harness injects benign impairments (delay/jitter/loss/reorder → H0).
  It does **not** inject malicious spoof/replay (H1) — that needs an active attacker
  and is deliberately out of scope.
- Fully *calibrating* twin fidelity against true prediction error needs
  hardware-timestamped ground truth. Tier 2 validates internal consistency and
  intended behaviour, not field calibration.
- A veth + software-timestamping path is realistic for protocol/servo behaviour but
  is not a substitute for a PTP-capable NIC's hardware timestamps (that is Tier 3).

## Reproduce

```powershell
python scripts/run_tier2.py            # full suite -> results/tier2/TIER2_REPORT.md
python -m pytest tests -p no:cacheprovider
```

`run_tier2.py` is resumable: `--step multiseed` caches each seed under
`results/tier2/_seedcache/` so it can finish under a wall-clock cap; `--step rest`
does generalization, twin validation, and the ingestion self-tests.

See `RUN_ON_REAL_LINUX.md` for capturing real traces.
