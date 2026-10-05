# Archive — older and superseded material

Nothing here should be used for current numbers. Current material is in `../00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/`.

| Subfolder | Contents | Why archived |
|---|---|---|
| `decks_superseded/` | July proposal-era decks and PDFs (`july_2026_proposal_era_deliverables/`); August deck + presenter guide; September deck v1–v6; the 06:41 UTC save of v7_FINAL | Replaced by the presented v7_FINAL (29 Sep 08:37) |
| `documents_2026-09-20_superseded_by_09-29/` | 20 Sep versions of the 3 xlsx + 3 pdf; the 28 Sep matrix correction; the "Claude outputs" copy; the 17 Sep walkthrough | Replaced by the 29 Sep revisions. `Claude_outputs_copy_2026-09-21/CAMPAIGN_VALIDATION.pdf` contains WITHDRAWN numbers |
| `august_ML_pipeline_results_withdrawn/` | August results workbook, technical report, team report, provenance check | Figures withdrawn as evidence on 17 Sep (duplicated "unseen" sessions; simulation-only features) |
| `agent_handoffs_and_old_plans/` | Old agent handoff and July reorganisation notes | Historical working notes |
| `build_scratch/` | Deck build scripts, renders, validation receipts, inspection dumps; leftover pytest/codex temp folders from the code tree (`code_tree_test_temp/`) | Tooling output, not deliverables |
| `earlier_cleanup_2026-09-21/` | The 21 Sep cleanup archive (duplicates, large dupes, scratch) | Already archived once |

`MOVE_MANIFEST_2026-10-03.csv` (41 moves) and `MOVE_MANIFEST_2026-10-04.csv` (14 moves) list each original and new path. Run `UNDO_REORG_2026-10-04.ps1` first, then `UNDO_REORG_2026-10-03.ps1`, to restore everything.

**5 Oct 2026:** every .pptx in this archive was deleted at the owner's request (30 files; paths and SHA-256 in
`DELETION_LOG_2026-10-05_PPT.csv`). `decks_superseded/` now holds only PDFs (August presenter guide, July proposal-era PDFs);
the slide renders and text dumps of drafts v2–v6 remain in `build_scratch/`. The undo scripts will report those 9 moved decks as not found.
