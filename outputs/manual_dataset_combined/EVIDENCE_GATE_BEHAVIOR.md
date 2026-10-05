# Evidence-gate behavioral verification

Date: 2026-09-07. Scope: fail-closed behavior of `stats/openset_eval.py` and `evasion/victim_transformer.py`; no dataset source was changed.

## Checks performed

| Case | Result | Why it matters |
|---|---|---|
| Missing metadata | Rejected | The current project has no qualifying manifest, so projected TIMESAFE sessions do not enter real evaluation. |
| Bare `independently_validated` status | Rejected | A boolean/string assertion alone cannot authorize real evaluation. |
| Missing semantics/type/reviewer/date/method/source map | Rejected | Metadata must identify what was validated and its documented review context. |
| Source hash altered to 64 zeroes | Rejected | The declared source map is verified against the actual project file, not read as prose. |
| Evidence path outside project | Rejected | Prevents metadata from escaping the audited workspace. |
| Evidence hash mismatch or missing artifact | Rejected | Evidence integrity is checked. |
| Evidence artifact identical to declared source PCAP | Rejected | A capture or label file cannot validate itself. |
| Evidence artifact identical to an evaluated session CSV | Rejected | An evaluated derived input cannot validate its own clock-health label. |
| Structurally complete fixture | Accepted structurally | A fixture using an existing project document and a matching PCAP hash passed the automatic structure checks. It was deliberately not treated as scientific evidence. |
| Evasion packet-label route with no manifest | Rejected | Prevents the side route from producing real-data metrics without a capture-specific validation artifact. |
| Conflicting Announce capture IDs | Hard-blocked after any manifest check | Sessions 1 and 2 remain quarantined because the same PCAP has conflicting annotations. |

## What automation cannot decide

These checks establish file binding and required documentation fields. They cannot determine whether a reviewer's scientific judgement is correct, whether a launch log is authentic, whether the logged host was unauthorized, whether receiver timing was physically measured correctly, or whether an evidence report was generated circularly from labels under another filename. Those require human review of primary experiment records. A future manifest must name that review and link its source material; it does not create scientific validity by itself.

## Exploratory work

`prepare_timesafe_sessions.py --allow-unvalidated-interval-projection` remains possible only as a quarantine-marked exploratory export. Its generated metadata says `unvalidated_interval_projection`, which the evaluation gates reject.

## Regression correction after independent cross-check

The original gate checked only a generic source map and then inferred H0/H1 from filenames. The consuming real-session loader now requires an `inputs` declaration for every CSV actually present, verifies each CSV hash, canonical capture ID, label semantics, source-map linkage, and allowed recorded label values, and rejects any extra file. It retains the CSV label rather than deriving one from its filename.

On 2026-09-08, a reproduced list-valued `evidence_artifact` reached path construction and raised `TypeError`. Both consumers now validate metadata field types and hexadecimal SHA-256 values before filesystem operations. A subsequent circularity bypass used an evaluated fixture CSV as the evidence artifact while retaining an upstream-PCAP source map; the real-session gate now rejects an artifact matching any declared evaluated-input hash as well as upstream source hashes. The packet route now requires the source map to include every fixed label CSV and PCAP that `load_capture_sessions` will consume, and rejects any of those hashes as the evidence artifact. Actual-module regression checks cover controls and negatives for both bindings, plus unrelated source maps, altered/undeclared files, missing and partially missing labels, malformed `run_id`/metadata fields, a renamed quarantined-content hash, quarantined identity, and H0-label preservation. Fixtures prove mechanics only, never scientific authenticity.

## 2026-09-08 independent continuation checks

The actual-module regression suite was rerun with `C:\Python314\python.exe`; all cases passed. `evidence_gate_regression_results.json` preserves the interpreter and results.

Additional defects found and corrected: list-valued evidence_type raised a set-membership TypeError; a missing source_sha256 could raise KeyError; evaluate_real still called the deleted historical _pre_row helper; and an evaluation with no eligible family attempted to concatenate no traces. The loader also now rejects missing per-row labels and malformed run_id types rather than silently dropping labels or failing during conversion.

Tests distinguish gate behavior from evaluator orchestration. The latter uses explicit fitting/scoring stand-ins to reach the relevant control flow; it is not an end-to-end scientific evaluation. Packet-consumer malformed metadata checks patch manifest I/O only and execute the actual consumer. No mechanical fixture establishes authentic launch logs, labels or receiver measurements.
