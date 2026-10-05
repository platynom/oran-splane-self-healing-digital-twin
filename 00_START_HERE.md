# START HERE — AI-Native Self-Healing O-RAN Network using a Digital Twin

Samsung PRISM worklet. Team: Tanmaya Kumar, Raghu Ram K, Munipalle Jaswanth Kumar.
Mentors: Bikas Singh (NovaThink Tech), Navin Kumar (Amrita Vishwa Vidyapeetham).
Folder organised on 2026-10-03, 2026-10-04 and 2026-10-05 (three move lists, all reversible). Full record of that work: `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/verification_records/SESSION_RECORD_2026-10-03.md`. Nothing was deleted; every move is listed in
`99_ARCHIVE_OLDER_AND_SUPERSEDED/MOVE_MANIFEST_2026-10-03.csv` and `MOVE_MANIFEST_2026-10-04.csv`, `MOVE_MANIFEST_2026-10-05.csv`, each reversible with
the matching `UNDO_REORG_*.ps1` in the same folder.

## What the project is, in one paragraph

Radio units in a 5G O-RAN network must agree on time to within nanoseconds. Time is delivered
over Ethernet by the PTP protocol (the "S-plane"). The project asks one question: when timing goes
wrong, is it a benign fault (ride it out) or an attack (isolate the source)? It builds a software
testbed of six real linuxptp daemons, injects 14 fault/attack scenarios, and classifies each run
with a standards-based decision rule, compared against a machine-learning model.

## If you only have 10 minutes

1. Open `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/ORAN_SPlane_PRISM_Review_v8_view.pdf`
   — the current 42-slide deck: the presented deck with corrections, plus 12 slides answering the
   reviewer's questions (slide 3 maps each question to its slide). Not yet presented.
   The deck that was presented is `ORAN_SPlane_PRISM_Review_v7_FINAL_PRESENTED_2026-09-29_view.pdf` (2026-09-29 is its last-save date; the presentation date itself is not recorded).
2. Open `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/ORAN_SPlane_Packets_to_Classification_2026-10-05.xlsx`
   — every one of the 168 runs, what was injected, and what the rule decided.
3. For the automated recovery loop built on 5 Oct, open `03_RECOVERY_LOOP_S-PLANE/README.md`, then `RESULTS_2026-10-05.md`.
4. Plain-language guide to the whole project: `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/SPlane_Project_Story_Guide.pdf`.

## Where each slide's evidence lives

`00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/verification_records/V8_SLIDE_SOURCE_MAP.md` maps every v8 slide (and every v7 slide)
to the files in this folder and the standards it rests on. The reviewer's notes are in the same folder.
Only two decks remain in the project: v7_FINAL_PRESENTED and v8 (all other decks deleted 5 Oct 2026; list in
`99_ARCHIVE_OLDER_AND_SUPERSEDED/DELETION_LOG_2026-10-05_PPT.csv`).

## Folder map

| Folder / file | What it is | Status |
|---|---|---|
| `00_START_HERE.md` | This guide | current |
| `00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/` | v8 deck (current), v7 presented deck, the 5 Oct document set (4 xlsx, 3 pdf: the 29 Sep set plus four new columns — Source, Destination, Attack devices, Consequence; 29 Sep originals in `99_ARCHIVE_OLDER_AND_SUPERSEDED/documents_2026-09-29_superseded_by_10-05/`), the story guide PDF, and `verification_records/` (deck fact-checks, v8 build script, session record, claim-verification script and its output) | **CURRENT — use these** |
| `03_RECOVERY_LOOP_S-PLANE/` | Automated recovery loop (detect → localise → decide → act → verify → rollback) on the same software testbed, built and evaluated 5 Oct: 140 pre-registered runs, loop vs matched no-action control | current — separate from the deck and campaign evidence |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/` | All code, the testbed harness, tests, and the evidence of the 168-run campaign | current (code + evidence) |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/gap_coverage_2026-09-20/corrected_final/` | **The authoritative campaign archive** `splane_campaign_CORRECTED_2026-09-20.tgz` (sha256 6149b4fb…), `EVALUATION_V4.json`, audit | current — source of every headline number |
| `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/ml_comparison_output/` | Rule vs machine-learning comparison on 56 held-out runs (21 Sep) | current |
| `01_CURRENT_SPlane_SelfHealing/PROJECT_STATUS.md` | August-era status of the ML pipeline (kept in place because README links to it) | older; August ML figures were withdrawn on 17 Sep |
| `01_CURRENT_SPlane_SelfHealing/literature-survey/` | Papers and literature index | reference |
| `01_CURRENT_SPlane_SelfHealing/planning/` | Earlier planning notes and agent prompts | reference |
| `outputs/empirical_software_network_pilot_v1/` | 13–14 Sep software pilot: closed-loop detect-and-act trial (S11/S12) and the S15 independent validation | current record; start at `START_HERE_FINAL.md` inside |
| `outputs/B6_two_machine_2026-10-02/` | Latest work (2 Oct): two-laptop crystal drift measurement for fault class B6 | current; run 2 = ESTABLISHED |
| `outputs/manual_dataset_combined/` | Dataset coverage inventory (13 Sep) | reference |
| `dataset/` | Data split into `legitimate/` (real captures) and `illegitimate/` (synthetic/contaminated — never use as evidence). Read `dataset/README.md` | current |
| `research/` | Two long fault catalogues (pasted AI transcripts, unreviewed) | reference only, unverified |
| `02_PREVIOUS_Work/` | Earlier project generations (RRC/PPO, KPM/FlexRIC twin) | historical |
| `99_ARCHIVE_OLDER_AND_SUPERSEDED/` | Old deck versions, 20 Sep document versions, withdrawn August results, build scratch | **do not use for current numbers** |
| `README.md`, `LICENSE`, `Dockerfile`, `.github/` … | Repository housekeeping (README dates from 7 Aug) | unchanged |

## Current headline results (168 live runs, 14 scenarios × 12 replicates)

Source: `EVALUATION_V4.json` and the presented deck.

- Attack sensitivity: 0.990 with rule v3 (pre-frozen base rule: 0.625 on the same runs)
- Benign specificity: 0.783 (0.979 excluding the planned boundary-clock replacement scenario)
- Correct abstention on the ambiguous scenario: 12/12
- Fault attribution: 84/96 = 0.875
- Rule vs ML on 56 held-out runs: rule 51/56, ML 24/56, always-BENIGN baseline 20/56 (ML not statistically distinguishable from the baseline, p = 0.219)

## Not done yet (stated in the deck)

Fault prediction; digital-twin validation of actions; MTTR / availability measurement; hardware
classes (GNSS spoof/jam, holdover, SyncE, oscillator drift on telecom hardware). A corrective action
(port failover) was executed only in the 13 Sep pilot, not in the 168-run campaign.

Update 5 Oct: automated corrective action is now built and evaluated in `03_RECOVERY_LOOP_S-PLANE/` (software testbed only):
rogue grandmaster, interception and whole-second abuse left the radio units off a legitimate parent for ~38.5–39 s of 40 without
action and ~2–2.5 s with the loop (5/5 each); 0 actions on 24 of 25 benign runs and on the ambiguous case. One benign run (B3 r17)
triggered a standby failover during a genuine 16.5 s outage — the pre-registered no-harm hypothesis is therefore reported as FAILED.
The deck was not extended with these results.

## Facts to know before quoting any result (re-verified 5 Oct 2026: 47/47 checks pass)

- Every ptp4l daemon ran with `free_running 1`: offsets were measured, clocks were never steered.
- pmc management telemetry returned no data in any of the 168 runs (cause confirmed 5 Oct: pmc needs `-d 24`).
- Corrected 5 Oct by pmc measurement: in A8 the rogue BC was only a BMCA candidate (RU parent unchanged); in C3 the RUs did re-parent to the forger. v8 slide 12 updated.
- Raw PCAPs and runtime configs are not in the campaign archive (configs are in `results_2026-09-17/g87251_testbed_v2.tgz`).
- C1 interception was a port blackhole that removed every frame.
- Rule v2, frozen before the campaign began, gives the same verdicts as v3 on all 168 runs.
- August ML figures were withdrawn as evidence on 17 Sep; do not quote them.

## Still wrong in the 29 Sep documents and their 5 Oct versions (fixed in v8 deck, not yet in these files; the 5 Oct versions only add four columns)

- `Attack_vs_Benign_Classification_v2026-09-29.xlsx` says interception "evades below ~62%"; correct figure ≈60.5%.
- The audit PDF, Fault Detectability and Parameter Matrix say "one capture copied 12 times"; it was three captures each copied 12 times.
- `Testbed_Configuration_Reference_v2026-09-29.pdf` says verify_frozen.sh passed before every admissible run; that holds only for the withdrawn 132-run campaign.
- `verification_records/V5_*.md` map A4 to "T-SPLANE-05", which does not exist.

The full findings list (17 items) and open actions are in the session record.

## GitHub

The full project is on GitHub: `platynom/oran-splane-self-healing-digital-twin`, branch `full-project-2026-10-05`.
Files of 50 MB or more are not in git; `LARGE_FILES_NOT_IN_GIT.md` lists them with sha256.
