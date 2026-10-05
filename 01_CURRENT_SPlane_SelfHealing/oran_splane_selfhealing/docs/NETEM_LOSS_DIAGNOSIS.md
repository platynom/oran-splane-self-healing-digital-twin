# Netem Loss Diagnosis

Date: 2026-07-27

## Summary

The fixed `harness/run_netem_scenarios.py` no longer lets one failed scenario abort the full live-netem run. On the 90 s rerun, `baseline`, `pdv`, and `loss` succeeded and were written into `results/tier2/netem/netem_telemetry.csv`; `holdover` still failed ingestion because it captured no Delay_Req / Delay_Resp exchange.

`results/tier2/netem/netem_run_status.csv`:

| Scenario | Status | Windows | Detail |
|---|---:|---:|---|
| baseline | ok | 629 | |
| pdv | ok | 625 | |
| loss | ok | 49 | |
| holdover | ingest_failed | 0 | no PTP offset samples recovered from pcap |

Combined telemetry scenarios:

| Scenario | Rows |
|---|---:|
| netem_baseline | 629 |
| netem_pdv | 625 |
| netem_loss | 49 |

## Packet Breakdown

Counts were computed with `ingest.ptp_wire.read_pcap()`, `parse_eth_frame()`, and `decode_ptp_payload()`.

| Pcap | Total | Announce | Sync | Follow_Up | Delay_Req | Delay_Resp | Unparsed |
|---|---:|---:|---:|---:|---:|---:|---:|
| netem_baseline.pcap | 2614 | 42 | 662 | 662 | 624 | 624 | 0 |
| netem_pdv.pcap | 2600 | 42 | 657 | 657 | 622 | 622 | 0 |
| netem_loss.pcap | 335 | 8 | 76 | 70 | 142 | 39 | 0 |
| netem_holdover.pcap | 35 | 4 | 17 | 14 | 0 | 0 | 0 |

## Root Cause

The earlier 60 s loss run captured only 80 packets and failed ingestion because the slave did not stay in a usable synchronized exchange long enough to recover offset samples. The earlier slave log tail ended in `LISTENING to UNCALIBRATED`, and the capture did not contain a complete Sync / Follow_Up plus Delay_Req / Delay_Resp sequence.

The current 90 s run shows the stale namespace/veth cleanup and per-scenario isolation fixes improved the situation: loss captured 335 PTP packets and included all message types needed by `pcap_to_telemetry()`. The low number of `Delay_Resp` messages relative to `Delay_Req` indicates the 5% loss impairment is still severe for this software-timestamped WSL veth setup, but it is no longer a hard loss-ingestion failure.

The remaining holdover failure appears expected for the current harness definition, not a parser bug: `holdover` applies 5 ms delay plus 20% loss, captured only Announce / Sync / Follow_Up, and had no Delay_Req / Delay_Resp messages. Without Delay_Req / Delay_Resp, the E2E path-delay calculation cannot produce offset telemetry.

## Pending Checks

- `/tmp/ptp4l_slave.log` and `/tmp/ptp4l_master.log` could not be read from this Codex process while WSL reported `Wsl/Service/E_ACCESSDENIED`. The scenario log tail from `results/tier2/netem_rerun_90.log` was used for the diagnosis above.
- The requested loss-only command is currently pending in a visible `cmd.exe` / WSL window:

```bash
sudo ./harness/netem_harness.sh loss 120 results/tier2/netem/loss2.pcap
```

Once the sudo prompt is completed, update this document with `loss2.pcap` packet counts and whether 5% loss remains stable over 120 s. If 5% fails, the next controlled check is to change only the loss impairment to 2% and rerun the same 120 s capture.
