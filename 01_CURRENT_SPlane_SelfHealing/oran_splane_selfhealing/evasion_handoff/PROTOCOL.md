# Autonomous Codex <-> Reviewer handoff protocol

No human relays messages. Codex (builder) and the Reviewer (a scheduled Claude session) communicate
ONLY through files in this folder. The human is contacted only when status becomes
`BLOCKED_NEEDS_HUMAN` or `DONE`.

## The single source of truth: `STATE.json`
```
{
  "current_step": <int>,          // 0..5
  "status": "<STATUS>",
  "last_updated_by": "codex" | "reviewer",
  "last_updated_utc": "<iso8601>",
  "note": "<short free text>"
}
```

## Statuses and who sets them
| Status | Set by | Meaning / next action |
|---|---|---|
| `PENDING_CODEX` | reviewer (or setup) | Codex should perform `current_step`. |
| `AWAITING_REVIEW` | codex | Codex finished the step and wrote its report; reviewer must verify. |
| `APPROVED` | reviewer | Step passed. Codex increments `current_step`, sets `PENDING_CODEX`, proceeds. |
| `CHANGES_REQUESTED` | reviewer | Step has fixable problems. Codex reads the review, fixes, re-reports (same step). |
| `BLOCKED_NEEDS_HUMAN` | reviewer | Objective failure or an irreversible decision. Both agents halt; human is notified. |
| `DONE` | reviewer | All steps approved. Human decides the final merge to `main`. |

## File contract
- **Codex, after finishing a step:** write `reports/codex_step_<N>.md` containing everything in the
  "Codex report must contain" list below, then set `STATE.json` to `AWAITING_REVIEW`
  (`last_updated_by:"codex"`, fill `last_updated_utc`). Then POLL `STATE.json` every few minutes.
  - if it becomes `APPROVED`: set `current_step = N+1`, `status = PENDING_CODEX`, do the next step.
  - if `CHANGES_REQUESTED`: read `reviews/review_step_<N>.md`, apply the fixes, overwrite
    `reports/codex_step_<N>.md`, set `AWAITING_REVIEW` again.
  - if `BLOCKED_NEEDS_HUMAN`: stop and wait.
- **Reviewer, when it sees `AWAITING_REVIEW`:** verify (see REVIEWER_CRITERIA.md), write
  `reviews/review_step_<N>.md`, then set the new status. Never edit Codex's report.

## Codex report must contain (every step)
1. Step number and one-line summary of what was done.
2. Files created/modified (paths). Confirm none are in the protected dirs.
3. Full output of `python scripts/audit_state.py`.
4. Output of `python -m pytest tests -q` (pass count).
5. `git branch --show-current` (must be `evasion-module`) and `git log --oneline -3`.
6. The step's key numbers / result files (e.g. victim accuracy, Pareto CSV summary).
7. Anything unexpected or any deviation from the design.

## Hard stops the reviewer will NOT auto-approve (-> BLOCKED_NEEDS_HUMAN)
- `audit_state.py` reports any FAIL, or tests are not all passing.
- Current branch is not `evasion-module`, or any protected/committed file was modified.
- Step 1 (Phase-0 gate): victim transformer does not reach ~99% (below ~95%).
- Step 3: research-branch ambiguity (A-succeeds vs A-fails) that changes the paper's claim.
- The final merge of `evasion-module` into `main` (always human).
