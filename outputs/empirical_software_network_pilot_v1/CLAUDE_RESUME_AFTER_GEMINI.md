# Resume note after documentation correction

## Verified state

- The original policy, acceptance register, and frozen S14 protocol have byte-exact copies and SHA-256 entries in [documentation_correction_archive_20260913T225000Z/MANIFEST.md](documentation_correction_archive_20260913T225000Z/MANIFEST.md).
- `S14_BROADER_EXPERIMENT_PROTOCOL.json`, S14 runners, scripts, and run files were not edited.
- Current interpretation limits are in [S14_EVIDENCE_DISPOSITION.md](S14_EVIDENCE_DISPOSITION.md), [ACCEPTABLE_BEHAVIOR_AND_IMPACT_POLICY.md](ACCEPTABLE_BEHAVIOR_AND_IMPACT_POLICY.md), and [REMAINING_WORK_ACCEPTANCE_REGISTER.md](REMAINING_WORK_ACCEPTANCE_REGISTER.md).
- A metadata-only snapshot at `2026-09-13T17:08:48Z` found nine S14 directories, eight with manifests, and one active/unsealed directory. It is not final acceptance.

## Next steps

1. Check active writers and batch state before taking any action; do not start a duplicate batch.
2. After writers stop, make a fresh complete inventory and verify each sealed manifest against its run directory without changing raw evidence.
3. Report S14 only as descriptive, with labels as expected conditions and harmfulness as `UNKNOWN` unless independent pre-action impact evidence supports a claim.
4. If independent validation is needed after tuning, write and freeze a new prospective protocol first. Do not reuse current S14 runs as independent validation.

## Relevant files

- `S14_BROADER_EXPERIMENT_PROTOCOL.json` — frozen historical protocol; do not edit.
- `run_s14_broader_batch.sh`, `run_s14_broader_trial.sh`, `s14_runs/` — live/raw evidence; do not edit during evidence review.
- `S14_EVIDENCE_DISPOSITION.md` — mandatory interpretation boundary.
- `documentation_correction_archive_20260913T225000Z/MANIFEST.md` — archive provenance.
