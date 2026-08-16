# Evasion Phase 0 — Victim Reproduction

## Scope and data provenance

These are **real public capture** results from the TIMESAFE repository; they are not simulator or
live-network numbers. Packet features were decoded directly from the five public pcaps and aligned
row-for-row with the released labels. The operational RF victim used the corresponding canonical
telemetry CSVs in `data/external/timesafe_sessions/`.

Complete `capture_id` groups were assigned with `GroupShuffleSplit`; no overlapping packet or
telemetry window crosses train/test. Split candidate 4 retained Announce and Sync attack
families on both sides without inspecting test performance.

- Train sessions: `announce_session_1, announce_session_2, sync_singlestep_session`
- Test sessions: `announce_session_3, sync_followup_session`
- Transformer: 40-packet window, stride 2, five per-packet features (direction, length, sequence ID,
  message type, inter-arrival), two encoder layers, CPU-only, 6 fixed epochs.
- Project victim: existing `discriminator.model.train_and_evaluate` API plus existing open-set detector
  and 2-of-3 persistence; protected modules were imported, not modified.

## Results

| Victim | Accuracy | Confusion matrix `[[TN,FP],[FN,TP]]` |
|---|---:|---|
| TIMESAFE-class Transformer | 0.993606 | `[[1173,0],[46,5975]]` |
| Project RF + open-set + 2-of-3 | 0.864833 | `[[108,113],[0,615]]` |

Per-capture Transformer results are in `results/evasion/victim_transformer_by_capture.csv`.

## Phase-0 gate

**PASS** — the pre-registered reproduction threshold is
95%; observed held-session accuracy is 99.36%.
Step 2 may be considered only after independent reviewer approval of this handoff.

## Deviations and caveats

- The released reference implementation randomly reuses chunks for validation and testing. This
  reproduction instead uses the required complete-session holdout, so its number is intentionally
  leakage-resistant rather than a byte-for-byte recreation of that split.
- Announce sessions 1 and 2 are distinct released pcap paths with identical packet streams but
  different released attack intervals. They remain separate declared capture IDs, and neither appears
  in the test set.
- The existing project victim API cannot stratify a label/scenario stratum containing one window.
  Its adapter excludes the two one-window benign fragments from Announce sessions 1 and 2 during
  training only; no held-session row is removed.
- PyTorch is required only for this CPU-gated research victim. The existing project pipeline remains
  CPU-runnable without enabling the Transformer victim.
