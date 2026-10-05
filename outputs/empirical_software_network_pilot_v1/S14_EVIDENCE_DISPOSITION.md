# S14 evidence disposition

## Status

`S14_BROADER_EXPERIMENT_PROTOCOL.json` is a frozen historical protocol. Its original byte-exact copy and SHA-256 are preserved in [the correction archive](documentation_correction_archive_20260913T225000Z/MANIFEST.md). The live protocol, runners, scripts, and run files were not modified by this correction.

Existing S14 material is **descriptive and unvalidated for harmfulness**. Its condition and `expected_classification` strings are raw expected-condition labels, not ground-truth harmfulness labels. A detector trigger, netem setting, commanded link change, `FAULTY` state caused by that command, or post-action takeover does not establish original harm.

There is no retrofit preregistration. No numerical criteria are added after collection to label an existing S14 run, calculate validation performance, or establish action benefit.

## What may be described

Subject to each run's preserved records and integrity status, describe only:

- configured condition labels;
- packet observations made by the existing detector;
- independently measured receiver/interface observations that demonstrably precede an action;
- commands and their direct effects; and
- post-action outcomes.

Use `UNKNOWN` for harmfulness unless independent pre-action impact evidence supports the specific claim. The `160 us` threshold is provisional engineering configuration. Rate envelopes are unvalidated testbed choices. The detector uses eight matched Sync/Follow_Up arrival-gap samples per block and requires two high, disjoint blocks within three seconds; those blocks are not required to be consecutive or exactly one second long.

## Metadata-only inventory snapshot

At `2026-09-13T17:08:48Z`, without reading live run contents, `s14_runs` contained nine directories: `20260913_s14_asf1`, `20260913_s14_base1`, `20260913_s14_base2`, `20260913_s14_bng1`, `20260913_s14_bng2`, `20260913_s14_jact1`, `20260913_s14_jact2`, `20260913_s14_jnoact1`, and `20260913_s14_jnoact2`.

Eight directories had `source_manifest.sha256`; `20260913_s14_jnoact2` had no manifest and was active/unsealed in that snapshot. The inventory was changing while the batch was running. It is neither a final batch inventory nor acceptance of any run.

## Required next evidence

Before any independent validation claim, create a future prospective protocol that fixes the labels, independent pre-action impact measurements, clock/timing alignment, analysis plan, and acceptance criteria before data collection. Do not reuse current S14 runs as independent validation after detector or policy tuning.
