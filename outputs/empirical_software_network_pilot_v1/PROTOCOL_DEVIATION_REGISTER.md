# Protocol deviation register

Every departure from a frozen protocol, and every action that touched sealed evidence, is recorded
here whether or not it changed a result. Entries are appended, never edited away.

---

## D1 — 2026-09-13 — a result file was written into a sealed S14 run directory

**What happened.** While exercising the code path of the new `check_s15_smoke.py` against an existing
run, the checker was pointed at `s14_runs/20260913_s14_jnoact1`. The checker writes its result as
`SMOKE_CHECK.json` in the target directory, so it added a file to a sealed evidence directory.

**Severity.** Low, and fully reversed. The added file was new; no existing file and no manifest entry
was modified. `source_manifest.sha256` lists expected files with their hashes, so the addition could
not alter any recorded hash, and no analysis reads that directory for file-set membership.

**Reversal and verification.** The file was moved out of the run directory to
`_to_delete/SMOKE_CHECK_stray_from_jnoact1.json` (this environment cannot delete files in the mounted
folder; the file is retained there rather than being destroyed). The run was then re-verified: every
manifest entry present, every hash matching, zero problems.

**Corrective control.** `check_s15_smoke.py` now refuses to run at all, exiting 2 without writing
anything, if its target contains `source_manifest.sha256` and is not directly under `s15_smoke/`.
The guard was tested against the same S14 run and refused as intended.

**Effect on results.** None. No S14 figure derives from directory membership, and no S14 file changed.

---

## D2 — 2026-09-13 — S15 protocol v1 superseded before any run

**What happened.** `S15_INDEPENDENT_VALIDATION_PROTOCOL.json` (v1) was frozen and then found to be
defective before any S15 data existed. It defined the receiver statistic as a maximum over an
unspecified number of servo summary windows, while the boundary it used had been derived from a
single window; it stated no phase-alignment rule, so a window straddling the impairment onset would
have been admitted; it used harm-sounding labels; and it ran the five levels in fixed ascending order
in every repetition, confounding level with batch position.

**Severity.** None to results, because zero S15 runs existed. The absence of any `s15_runs/`
directory was checked immediately before v1 was superseded and again before v2 was written.

**Handling.** v1 was **not deleted**. It is retained in place with `status`
`SUPERSEDED_BEFORE_ANY_RUN` and a `superseded_by` pointer, and a byte-identical archive copy is kept
at `S15_INDEPENDENT_VALIDATION_PROTOCOL_V1_SUPERSEDED.json`. The v1 file's recorded runner hashes are
preserved there, which is why they differ from v2's.

**Consequential changes made before the v2 freeze.** The impaired phase was lengthened from 50 s to
80 s, because S14's 30 s phase produced exactly one wholly-in-phase summary window per run and the
v2 rule requires at least two. The trial order was replaced with a counterbalanced randomised
sequence generated once from seed 20260913 and written literally into the batch script, so the script
and the protocol cannot drift.

---

## D3 — historical deletion claim, not evidenced by the current tree

A claim exists in the working history that a run directory named `20260913_s11_control_r7` was
deleted by an executing agent in violation of the preservation rule. **The current tree does not
support that claim and does not refute it.** `S11_CLOSED_LOOP_PROTOCOL.json` plans five action and
five no-action runs; `s11_runs/` contains exactly those ten. There is no `control` arm in the S11
protocol at all, and every `set3_control_r4` through `set3_control_r8` directory in `runs/` is
present. No planned run is missing from any protocol in this tree.

This entry is recorded so the claim is neither quietly dropped nor asserted as established. If a
reader can produce the protocol or batch script that planned an `s11_control_r7`, this entry should
be reopened.


---

## D4 — 2026-09-13 — detector lifetime did not cover the declared observation period

**What happened.** `run_s15_validation_trial.sh` passed a hard-coded `--max-seconds 70` to the live
detector while `SETTLE=12` and `IMPAIR=80`. The detector would have exited roughly 24 s before the
impaired phase ended. Two consequences, not one: observation coverage would have been truncated, so a
run could record NO_TRIGGER purely because nobody was watching; and the capture FIFO would have lost
its reader mid-run, which breaks the graceful drain-and-seal the runner depends on.

**Severity.** Would have invalidated the batch. Caught before any S15 run existed.

**Fix.** The lifetime is now derived from the phase constants rather than hard-coded:
`DET_MAX_SECONDS = DET_SETUP_MARGIN(20) + SETTLE(12) + IMPAIR(80) + DET_DRAIN_MARGIN(60) = 172 s`.
It is a bounded watchdog, not a schedule: the detector normally exits when the sealer closes the FIFO.
`check_s15_smoke.py` now fails the smoke run unless `detector_max_seconds >= settle + impair`, and
unless the detector's own `detector_finished` record is at or after `phase2_end_recorded` with a
`stream_ended` record immediately before it, which distinguishes a graceful close from a watchdog
expiry.

---

## D5 — 2026-09-13 — stated timing precision exceeded the precision actually recorded

**What happened.** The runner recorded phase timestamps from `/proc/uptime` formatted to two decimal
places. That is CLOCK_BOOTTIME at 10 ms resolution. The evaluator excluded summary windows starting
within a fixed **1 ms** of the apply instant, a band ten times finer than the timestamps it was
applied to. The 0.93 ms anchor agreement that appeared to justify it was measured between ptp4l's log
clock and the **detector's** `time.monotonic()`, not against these coarser runner timestamps, so it
never licensed that band.

**Severity.** Would have admitted windows as wholly-in-phase on a precision claim the evidence did not
support. Caught before any S15 run existed.

**Fix, and what it now rests on.** Verified against linuxptp **v3.1.1**, the version recorded in every
`run_environment.txt`:

- `print.c:68` — ptp4l's log timestamp is `clock_gettime(CLOCK_MONOTONIC)`, printed as `%lld.%03ld`
  from `ts.tv_nsec / 1000000`, i.e. **truncated** to 1 ms. A logged time `L` means a true time in
  `[L, L+0.001)`.
- The runner now reads **CLOCK_MONOTONIC** directly at microsecond precision. It is the *same clock*,
  read by the same system call, as ptp4l and as the detector. The alignment claim no longer rests on
  five empirical anchors; those are now corroboration only.
- The impairment command is **bracketed**: `phase2_apply_begin` before `tc`, and
  `phase2_graded_jitter_applied_seg1` after it. The apply instant is an interval, and eligibility uses
  the **later** bound, which can only reject a window that might straddle, never admit one.
- Because a logged ptp4l time is always `<=` the true time, `window_start_logged >= apply_upper_bound`
  guarantees the true start is at or after the true apply instant with **no** arbitrary band. The 1 ms
  band is deleted.
- Eligibility additionally requires **strict containment**: `window_end + 1 ms <= phase2_end_recorded`.
  The impairment persists past that event until teardown, so this rejects some genuinely impaired
  windows — the conservative direction.
- A run recorded by a superseded runner has no begin timestamp; its apply upper bound is padded by the
  10 ms phase-clock quantum and the run is flagged with `apply_basis`.

**Side finding, recorded because it changes why the design works.** The 16 s summary cadence is not
empirical. Under `free_running 1`, linuxptp 3.1.1 returns via `clock_no_adjust()`, which accumulates an
offset sample only once every `1 << (freq_est_interval - logSyncInterval) = 16` Syncs (2 s at
`logSyncInterval -3`), and a summary prints every `1 << (summary_interval - logSyncInterval) = 8`
such samples. 8 x 2 s = **16 s exactly, by construction**. The measured 16.021 s agrees. An 80 s phase
therefore contains five prints and four wholly-contained windows, so the two-window minimum has a
margin of two.

---

## D6 — 2026-09-13 — I killed a running batch by editing its script mid-execution

**This is my error, and it destroyed a trial and stopped a batch.**

**What happened.** The S15 batch was started on the WSL host at 18:07 UTC under protocol v3: a smoke
run at 18:07:08 that passed all nine checks, then batch trials from 18:10. I was unaware of this. At
18:21-18:22 UTC I wrote protocol v4 and rewrote `run_s15_validation_trial.sh` in place, having checked
for `s15_runs/` earlier in the session and found it absent — I did not re-check immediately before
writing.

Bash reads a script from the file by byte offset as it executes. Rewriting the file in place shifted
every offset under a running interpreter. Trial `20260913_s15_j200_r2` was mid-execution: its
`events.log` ends at `phase2_graded_jitter_applied_seg1` (monotonic 908.541), the last event before
the edited region. The trial never reached `phase2_end_recorded`, never sealed, and the batch loop
died with it. No further trial started.

**Damage.**

- `20260913_s15_j200_r2` — destroyed mid-run, unsealed, no manifest. Preserved in place as a failure.
- The batch stopped after 8 of 30 trials. 22 trials never ran.
- Protocol v4 was written on a false premise and never governed any collection.

**What was NOT damaged.** The seven trials sealed before the edit are intact and verify clean, as does
the smoke run. Their evidence was complete and hashed before the file was touched.

| run | valid windows | first-window dispersion (ns) |
|---|---|---|
| smoke 20260913T180708Z (excluded from estimation) | 4 | 21089 |
| j020_r1 | 5 | 13408 |
| j060_r1 | 4 | 13621 |
| j100_r1 | 4 | 23609 |
| j100_r2 | 4 | 25426 |
| j140_r1 | 4 | 40668 |
| j140_r2 | 4 | 34838 |
| j200_r1 | 4 | 46356 |

**Reversal.** On discovery, `run_s15_validation_trial.sh`, `run_s15_validation_batch.sh`,
`evaluate_s15.py`, `run_s15_smoke.sh` and `check_s15_smoke.py` were all restored to their exact v3
frozen bytes; all five now match the hashes recorded in v3. Protocol v4 is marked
`WITHDRAWN_NEVER_GOVERNED_ANY_RUN`. Protocol v3 is marked as the protocol that governed the aborted
batch. No run directory was moved, renamed or deleted.

**Root cause.** I treated a check made earlier in the session as still true. The correct rule is that
a frozen artefact may be modified only after re-confirming, in the same action, that nothing is
executing — and never by rewriting a file in place while any process may hold it open.

**Control.** Before any future edit to a frozen script: re-check for run directories AND for a live
batch, and write to a new filename rather than rewriting an existing one in place.

**Not yet decided.** Whether to discard the eight trials and re-run the full batch, or to resume.
That decision is the user's; no results have been evaluated and `evaluate_s15.py` has not been run on
this data.

---

## D7 — 2026-09-13 — aborted batch archived, protocol re-issued as v5

Following D6, the aborted batch was moved intact to `s15_aborted_20260913T182252Z/` (runs, smoke run,
console log, and a README stating what happened). Nothing was deleted or edited. `s15_runs/` and
`s15_smoke/` are absent, so the replacement batch starts on a clean path and the archive cannot enter
estimation: `evaluate_s15.py` reads only `s15_runs/`.

Protocol v5 re-issues v4's three corrections with authority, adds resume safety to the batch loop
(skip a sealed trial, stop on an unsealed one, never overwrite), and adds a single gated entry point
`run_s15_complete.sh`. v5 was frozen with `s15_runs` and `s15_smoke` both confirmed absent at the
moment of writing, and the absence is recorded in the file.

The seven clean trials from the aborted batch are NOT pooled with the replacement batch. They were
collected under instrumentation that has since been corrected, and their randomised sequence contains
a corrupted trial.
