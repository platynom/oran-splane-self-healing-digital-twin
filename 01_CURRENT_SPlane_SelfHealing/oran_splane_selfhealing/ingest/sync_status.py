from __future__ import annotations

"""Parse live Linux PTP/SyncE status text without requiring running daemons.

Production collection should use ptp4l ``SUBSCRIBE_EVENTS_NP`` notifications
rather than polling. On a real O-RAN deployment, the authoritative equivalent
is O-RU M-plane NETCONF/YANG synchronization telemetry.
"""

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PmcSyncStatus:
    clock_class: int | None
    gm_present: bool | None
    gnss_available: bool
    holdover: bool


_CLOCK_CLASS = re.compile(r"\bclockClass\s+(\d+)\b", re.IGNORECASE)
_GM_PRESENT = re.compile(r"\bgmPresent\s+(true|false|1|0)\b", re.IGNORECASE)
_QL_TOKEN = re.compile(
    r"\bQL[-_: ]?(PRC|PRS|SSU[-_ ]?A|SSU[-_ ]?B|SEC|ST2|ST3E|ST3|SMC|DNU|DUS)\b",
    re.IGNORECASE,
)

# Project convention: 1 is a high-quality frequency reference and 4 is unusable.
_QL_RANK = {
    "PRC": 1,
    "PRS": 1,
    "SSUA": 2,
    "SSUB": 2,
    "SEC": 3,
    "ST2": 2,
    "ST3E": 3,
    "ST3": 3,
    "SMC": 3,
    "DNU": 4,
    "DUS": 4,
}


def _text(lines: str | Iterable[str]) -> str:
    return lines if isinstance(lines, str) else "\n".join(lines)


def parse_pmc_output(lines: str | Iterable[str]) -> PmcSyncStatus:
    """Parse combined ``GET PARENT_DATA_SET`` / ``TIME_STATUS_NP`` output."""
    text = _text(lines)
    class_matches = _CLOCK_CLASS.findall(text)
    present_matches = _GM_PRESENT.findall(text)
    clock_class = int(class_matches[-1]) if class_matches else None
    gm_present = None
    if present_matches:
        gm_present = present_matches[-1].lower() in {"true", "1"}
    holdover = clock_class == 7 or gm_present is False
    gnss_available = gm_present is not False and clock_class == 6
    return PmcSyncStatus(clock_class, gm_present, gnss_available, holdover)


def parse_synce4l_ql(lines: str | Iterable[str]) -> int | None:
    """Return the most recent SyncE quality level as the project's 1..4 rank."""
    matches = _QL_TOKEN.findall(_text(lines))
    if not matches:
        return None
    token = re.sub(r"[-_ ]", "", matches[-1].upper())
    return _QL_RANK[token]
