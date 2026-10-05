# Attack Roadmap & Live-Source Mapping
*Consolidates the team's Task-2 (attack taxonomy) and Task-3 (standards mapping) research
into an actionable plan. Source PDFs are preserved in `docs/team_research/`.*

## Key decision: self-generate attack data, stop hunting public datasets
Public **labeled S-plane attack** datasets essentially do not exist beyond TIMESAFE (a known
field gap). Benign-only real data (e.g. PTP-DAL) is still worth acquiring — it lowers the real
false-positive rate and aids domain adaptation. But the path to *diverse, full-feature, labeled
attacks* is to **generate them ourselves** on the Linux/lab testbed, captured through the live
`pmc`/`synce4l`/YANG sources mapped below. This simultaneously fixes the dead-feature problem,
the small-sample problem, and the novel-attack gap.

## Attack families (from Task 2) and priority
| # | Family | Status | Priority | Why |
|---|---|---|---|---|
| 1 | Spoofing / GM impersonation (Announce/BMCA) | Covered (H1 "spoof") | — | existing |
| 2 | Replay (Sync/Follow_Up) | Covered (H1 "replay") | — | existing; also native linuxptp `sync_mismatch`/`followup_mismatch` counters |
| 3 | Delay / MITM (asymmetric delay) | Open | Low now | needs redundant-path / cyclic-asymmetry; high engineering cost |
| 4 | **DoS / message flooding** | **Covered (H1 `dos`)** | Completed | self-generated `ptp_dos_flood`, benign `traffic_burst` confounder, and real/simulated message-rate features |
| 5 | **Time-source manipulation (GNSS spoof/jam)** | Open | **2nd (highest value)** | directly stresses H0/H1 novelty — a GNSS spoof looks identical to benign holdover; needs a `gnss-sync-status` feature channel |

## Feature → live source map (from Task 3)
- **Core PTP status** (offset, path delay, GM identity/quality, priority, steps-removed, port
  state): `pmc` — `TIME_STATUS_NP`, `CURRENT_DATA_SET`, `PARENT_DATA_SET`, `PORT_DATA_SET`
  (IEEE-1588 `currentDS/parentDS/portDS`).
- **Replay / DoS counters**: `pmc` — `PORT_SERVICE_STATS_NP` (`sync_mismatch`, `followup_mismatch`,
  `*_timeout`) and `PORT_STATS_NP` (`rxMsgType[]`, `txMsgType[]`).
- **SyncE quality / lock**: `synce4l` — `MSG_GET_QL` / EEC state over its AF_UNIX API (ITU-T G.8264).
- **GNSS status** (critical for family #5): O-RAN M-plane YANG `gnss-status/gnss-sync-status`
  (`ANTENNA-DISCONNECTED`, `ANTENNA-SHORT-CIRCUIT` are tamper indicators, not generic "signal lost").

## Immediate build (no hardware)
1. **DoS/flooding family + message-rate feature — completed.** The simulator now generates a bursty
   H1 flood plus an overlapping benign traffic surge, while PCAP ingestion counts every decoded PTP
   message in a trailing one-second window. The model consumes message-rate mean and variance without
   replacing the original ten features; leave-one-attack-out now includes the `dos` family.
2. **GNSS-spoof (family #5) experiment** — add a `gnss-sync-status` feature channel and a malicious
   GNSS-spoof scenario that mimics benign holdover; measure whether the discriminator separates them.
   This is the flagship test of the project's core novelty.

## Verify before publishing claims
- Confirm current O-RAN WG11 threat-model version at specifications.o-ran.org (supersedes O-R003-v06.00).
- Confirm exact `pmc`/`synce4l` field names against the installed linuxptp v4.0 and the current YANG.
