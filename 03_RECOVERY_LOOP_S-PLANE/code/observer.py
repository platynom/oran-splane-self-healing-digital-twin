#!/usr/bin/env python3
"""Passive outcome observer, identical in both arms. Polls each RU's PARENT_DATA_SET and
PORT_DATA_SET through pmc every 0.5 s and records them with CLOCK_MONOTONIC timestamps.
pmc GET is read-only management (IEEE 1588-2019 clause 15); it never changes clock state.
NOTE: -d 24 is required. The 168-run campaign's pmc_log.sh omitted it (pmc defaults to
domain 0) and therefore received no responses in any run; this is the corrected call."""
import json, subprocess, sys, time
out, dur = sys.argv[1], float(sys.argv[2])
nodes = ("ru1", "ru2", "ru3")
end = time.monotonic() + dur
with open(out, "w") as f:
    while time.monotonic() < end:
        t = time.monotonic()
        for n in nodes:
            try:
                o = subprocess.run(["ip", "netns", "exec", n, "pmc", "-u", "-b", "0", "-d", "24",
                                    "-s", f"/var/run/p.{n}", "GET PARENT_DATA_SET", "GET PORT_DATA_SET"],
                                   capture_output=True, text=True, timeout=2).stdout
            except Exception:
                o = ""
            r = {"t": round(t, 3), "node": n}
            for line in o.splitlines():
                p = line.split()
                if len(p) == 2 and p[0] in ("parentPortIdentity", "grandmasterIdentity", "portState",
                                             "gm.ClockClass", "stepsRemoved"):
                    r[p[0]] = p[1]
            f.write(json.dumps(r) + "\n")
        f.flush()
        time.sleep(max(0.0, 0.5 - (time.monotonic() - t)))
