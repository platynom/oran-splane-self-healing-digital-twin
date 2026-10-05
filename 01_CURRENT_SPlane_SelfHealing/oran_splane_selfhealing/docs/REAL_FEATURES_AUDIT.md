# Real PTP Feature Audit

## Scope

This audit uses five independent captures from the public
`genesys-neu/s-plane_security` TIMESAFE repository:

- three Announce-spoof sessions;
- one two-step Sync/Follow_Up attack session;
- one one-step Sync attack session.

Packet-level TIMESAFE labels were converted to attack intervals. A normal PTP
packet inside an active attack interval remains attack-labelled because it
carries the affected clock state. Capture identity is retained through feature
generation so no capture contributes windows to both train and test.

## Feature coverage

The pre-change measurement uses the preserved 1,195-window TIMESAFE artifact at
`results/tier2/timesafe_external_windows.csv`. The post-change measurement uses
7,934 windows regenerated from the five captures.

| feature | distinct values before | distinct values after | post-change status |
|---|---:|---:|---|
| offset_mean | 1,192 | 7,899 | live |
| offset_std | 1,195 | 7,934 | live |
| offset_abs_max | 759 | 3,167 | live |
| path_delay_mean | 1,177 | 991 | live |
| pdv_std | 1,169 | 982 | live |
| seq_regressions | 7 | 28 | live |
| msg_irregularity | 1 | 99 | live |
| synce_ql_max | 1 | 1 | **constant** |
| gnss_loss_rate | 1 | 74 | live |
| holdover_rate | 1 | 17 | live |

Measured non-constant features improved from **6/10 to 9/10**. The earlier
qualitative audit described five dead features, but the preserved pre-change
window file shows four constant columns among the exact ten model inputs because
`seq_regressions` already varied. This report uses the measured artifact rather
than repeating the earlier estimate.

Announce parsing activates `gnss_loss_rate` and contributes to
`holdover_rate`. Actual packet types activate `msg_irregularity`. Across the
five captures, decoded clock classes include 0, 6, 248 and time sources include
0x20 (GNSS) and 0xA0 (internal oscillator). No captured Announce advertised
clockClass 7, so clockClass-derived holdover is implemented and fixture-tested
but is not independently exercised by these TIMESAFE sessions.

`synce_ql_max` remains constant because SyncE ESMC quality is not present in a
PTP pcap. `ingest/sync_status.py` now parses live `synce4l` QL logs for this
production-only input. Frequency error likewise requires local servo telemetry,
not the Ethernet PTP payload.

## Leakage-proof calibration

The primary split trained on complete captures `announce_session_1`,
`announce_session_2`, and `announce_session_3`; it tested only on complete
captures `sync_followup_session` and `sync_singlestep_session`.

| method | benign FP | attack TP |
|---|---:|---:|
| sim-trained RF | 245/245 = 1.000 [0.985, 1.000] | 596/596 = 1.000 [0.994, 1.000] |
| fixed 100 ns threshold | 245/245 = 1.000 [0.985, 1.000] | 596/596 = 1.000 [0.994, 1.000] |
| benign-calibrated 26,927 ns threshold | 5/245 = 0.020 [0.009, 0.047] | 596/596 = 1.000 [0.994, 1.000] |
| real-trained RF, session holdout | 5/245 = 0.020 [0.009, 0.047] | 596/596 = 1.000 [0.994, 1.000] |

These numbers remove the previous within-file memorization leak. They do not
establish deployment performance: only five sessions from one testbed are
available, and the class balance is attack-heavy.

## Leave-one-attack-family-out

| held-out family | benign FP | unseen-family TP |
|---|---:|---:|
| Announce | 0/134 = 0.000 [0.000, 0.028] | 1,656/6,959 = 0.238 [0.228, 0.248] |
| Sync/Follow_Up | 0/89 = 0.000 [0.000, 0.041] | 298/298 = 1.000 [0.987, 1.000] |
| one-step Sync | 3/156 = 0.019 [0.007, 0.055] | 298/298 = 1.000 [0.987, 1.000] |

The weak unseen-Announce result is the honest generalization warning. Announce
attacks manipulate source-election metadata and do not always resemble Sync
timestamp attacks in offset/path-delay space. The next defensible improvement
is to add explicit Announce-state features such as clock-class transitions,
grandmaster-identity churn, priority changes, and steps-removed changes, then
evaluate on additional testbeds. That change is not silently applied here.

## Production path

For live Linux validation, parse `pmc GET PARENT_DATA_SET` and
`TIME_STATUS_NP`, plus `synce4l` QL logs. Production collection should use
ptp4l `SUBSCRIBE_EVENTS_NP`; a real O-RAN integration should consume O-RU
M-plane NETCONF/YANG synchronization telemetry. Tier 3 still requires a
hardware-timestamping NIC, O-DU/O-RU or representative clocks, and a real SyncE
source to validate servo frequency and ESMC behavior.
