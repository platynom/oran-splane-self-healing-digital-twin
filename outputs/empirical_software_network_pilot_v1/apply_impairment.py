"""Apply the netem impairment and bracket it with two CLOCK_MONOTONIC timestamps taken in THIS
process, so the recorded apply interval is the width of the tc command itself rather than the width
of two shell round trips.

The superseded runner called a shell mono() helper before and after tc. Each call spawned a python
interpreter costing about 18 ms, so the recorded interval was roughly 20 ms wide and was dominated by
measurement overhead, not by any real uncertainty about when the qdisc changed. Measured overhead
recorded as uncertainty is not conservative, it is just wrong: it makes the instrument look worse
than it is and widens the eligibility exclusion for no reason.

CLOCK_MONOTONIC is the same clock linuxptp print.c reads (clock_gettime(CLOCK_MONOTONIC), truncated
to 1 ms on output) and the same clock the detector records via time.monotonic().

Exits with tc's return code, so `set -e` in the caller still aborts the trial on failure.
"""
from __future__ import annotations
import datetime as dt
import subprocess
import sys
import time


def stamp(run_id: str, arm: str, condition: str, event: str, mono: float) -> str:
    utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (f"run_id={run_id} arm={arm} condition={condition} phase=trial event={event} "
            f"utc={utc} monotonic_s={mono:.6f} status=PASS\n")


def main() -> int:
    events_log, run_id, arm, condition, dev, jitter_us = sys.argv[1:7]
    cmd = ["tc", "qdisc", "replace", "dev", dev, "root", "netem",
           "delay", "100us", f"{jitter_us}us", "distribution", "normal"]
    t_before = time.clock_gettime(time.CLOCK_MONOTONIC)
    proc = subprocess.run(cmd)
    t_after = time.clock_gettime(time.CLOCK_MONOTONIC)
    with open(events_log, "a", encoding="utf-8") as f:
        f.write(stamp(run_id, arm, condition, "phase2_apply_begin", t_before))
        f.write(stamp(run_id, arm, condition, "phase2_graded_jitter_applied_seg1", t_after))
        f.flush()
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
