# Dataset — classified by evidential legitimacy

Two folders only. Every file was classified against evidence verified directly from the bytes
on disk, not from filenames. `DATASET_MANIFEST.csv` records the source path, class, destination,
reason and evidence for all 40 moved items.

## The classification rule

The line is **abstention vs. invention**:

| | Meaning | Class |
|---|---|---|
| **Measured** | A real sensor/capture produced the value. | legitimate |
| **Abstention** | No sensor existed, and the file records an honest constant saying so (e.g. `freq_error_ppb = 0.0`, `gnss_sync_status = BOOTING`). The file does not pretend. | legitimate (with caveat) |
| **Invention** | No sensor existed, yet the file contains realistic-looking varying values (e.g. 46,644 unique `freq_error_ppb` values with no oscillator present). The file pretends. | **illegitimate** |
| **Contaminated** | Real measured columns with fabricated columns sitting beside them, indistinguishable to a consumer. | **illegitimate** |

## legitimate/  (1.5 GB)

- `timesafe_real_hardware_captures/` — authentic TIMESAFE hardware captures (.pcap), their direct
  CSV conversions (7 columns, no fabricated fields), the production-environment capture, and
  `attack_app.py`, the tool that generated the ground truth.
- `netem_real_software_testbed/` — telemetry and captures genuinely collected from live `linuxptp`
  runs. `netem_telemetry.csv` = 5,665 rows, matching the 5,665 windows cited in TEAM_REPORT.

**Caveat that must travel with this data:** on the real software testbed the SyncE, GNSS and
oscillator columns are inert constants because those sensors do not physically exist there
(no PHY, no receiver, one shared system clock). They are honest placeholders, not evidence.
Do not train on them and do not cite results derived from them.

**Quarantine flag:** `15min_announce_attack.pcap` and `2024-10-06-announce_attack_UEdata.pcap`
are byte-identical (md5 `5c6fd791a0ccf22a0d6cfe3031443168`) but carry conflicting labels. They are
real, so they stay here, but they must not both enter a training set.

## illegitimate/  (55 MB)

- `synthetic_simulator_output/` — physics-simulator output. Every value generated.
- `mislabelled_duplicates_of_synthetic/` — `splane_telemetry.csv` / `splane_windows.csv` that sat
  inside the Netem folder while being byte-identical copies of the synthetic output
  (md5 `46cf48c95e593b3b8b78b867bcc045df` / `5620250115947b6d6e45c1c71affbbd2`).
- `timesafe_derived_contaminated/` — derived from REAL captures but carrying fabricated constants
  (`synce_ql=1`, `freq_error_ppb=0.0`, `offset_scaled_log_variance=65535`) and a `gnss_available`
  column that is merely a re-encoding of `clockClass`. **Regenerable as legitimate** once
  `pcap_ingest.py` is extended — the underlying pcaps are real.
- `derived_model_artefacts/` — training outputs and caches, not collected evidence.

## Known leak — do not undo this separation

`offset_scaled_log_variance` is the constant **4096** in every synthetic row and **65535** in every
real row. Joining the two folders lets any classifier separate them at 100% on that column alone.

Note: TIMESAFE and the real netem runs **agree** on these constants, so a join of
`legitimate/timesafe_real_hardware_captures` (attacks) with `legitimate/netem_real_software_testbed`
(benign) does **not** suffer this leak.
