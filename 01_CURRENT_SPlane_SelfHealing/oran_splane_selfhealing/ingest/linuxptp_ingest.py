from __future__ import annotations

"""Ingest linuxptp (ptp4l / phc2sys) textual output into canonical telemetry.

On a real Linux box you run, e.g.:
    sudo ptp4l -i eth0 -m -q -s -S > ptp4l.log      # -S = software timestamping
and this parses the per-servo lines:
    ptp4l[123.456]: master offset  -42 s2 freq -1234 path delay  512
into the same schema the simulator emits, so the discriminator/twin/healing loop
run unchanged. `phc2sys` lines are also recognised.

No linuxptp is required to PARSE a log (that is what makes this testable off-box);
`linuxptp_available()` only gates LIVE capture.
"""

import re
import shutil
from pathlib import Path

import pandas as pd

from ingest.schema import coerce_telemetry

# ptp4l:  "ptp4l[123.456]: master offset  -42 s2 freq  -1234 path delay   512"
_PTP4L_RE = re.compile(
    r"\[(?P<t>\d+\.\d+)\].*?master offset\s+(?P<offset>-?\d+)\s+s(?P<state>\d)"
    r"\s+freq\s+(?P<freq>[+-]?\d+)(?:.*?path delay\s+(?P<delay>-?\d+))?"
)
# phc2sys: "phc2sys[123.456]: CLOCK_REALTIME phc offset  -42 s2 freq  -1234 delay  512"
_PHC2SYS_RE = re.compile(
    r"\[(?P<t>\d+\.\d+)\].*?phc offset\s+(?P<offset>-?\d+)\s+s(?P<state>\d)"
    r"\s+freq\s+(?P<freq>[+-]?\d+)(?:.*?delay\s+(?P<delay>-?\d+))?"
)


def linuxptp_available() -> bool:
    return shutil.which("ptp4l") is not None


def parse_linuxptp_lines(lines, scenario: str = "live", label: str = "unlabeled") -> pd.DataFrame:
    rows = []
    t0 = None
    seq = 0
    for line in lines:
        m = _PTP4L_RE.search(line) or _PHC2SYS_RE.search(line)
        if not m:
            continue
        t = float(m.group("t"))
        if t0 is None:
            t0 = t
        delay = m.group("delay")
        path_delay_valid = delay is not None
        rows.append({
            "t_s": t - t0,
            "offset_ns": float(m.group("offset")),
            "path_delay_ns": float(delay) if path_delay_valid else float("nan"),
            "offset_valid": True,
            "path_delay_valid": path_delay_valid,
            "telemetry_valid": path_delay_valid,
            "freq_error_ppb": float(m.group("freq")),
            "ptp_seq_id": seq,
            "ptp_msg_type": "Sync",
            # servo state s0=unlocked/holdover-ish, s2=locked. Surface as holdover flag.
            "holdover": m.group("state") == "0",
        })
        seq += 1
    if not rows:
        raise ValueError("no ptp4l/phc2sys servo lines found (expected 'master offset ... freq ...')")
    df = pd.DataFrame(rows)
    df["scenario"] = scenario
    df["label"] = label
    return coerce_telemetry(df)


def ptp4l_log_to_telemetry(path: str | Path, scenario: str = "live", label: str = "unlabeled") -> pd.DataFrame:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return parse_linuxptp_lines(f, scenario=scenario, label=label)
