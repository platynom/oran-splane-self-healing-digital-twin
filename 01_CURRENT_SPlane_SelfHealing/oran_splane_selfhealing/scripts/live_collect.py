from __future__ import annotations

"""Collect canonical S-plane telemetry by polling a live linuxptp instance."""

import argparse
import csv
import logging
import re
import shutil
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Callable, Sequence

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from ingest.schema import TELEMETRY_COLUMNS, coerce_telemetry
from ingest.sync_status import parse_pmc_output, parse_synce4l_ql


LOG = logging.getLogger("live_collect")
PMC_DATASETS = (
    "TIME_STATUS_NP",
    "CURRENT_DATA_SET",
    "PARENT_DATA_SET",
    "PORT_DATA_SET",
    "PORT_SERVICE_STATS_NP",
    "PORT_STATS_NP",
)
Runner = Callable[[Sequence[str], float], subprocess.CompletedProcess[str]]


def _run(command: Sequence[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def _number(text: str, field: str, default: float | None = None) -> float | None:
    match = re.search(rf"(?mi)^\s*{re.escape(field)}\s+([-+]?\d+(?:\.\d+)?)\s*$", text)
    return float(match.group(1)) if match else default


def _integer(text: str, pattern: str, default: int) -> int:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return int(match.group(1), 0) if match else default


def _token(text: str, pattern: str, default: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1) if match else default


def _split_pmc_sections(text: str) -> dict[str, str]:
    headers = list(
        re.finditer(r"(?mi)^[^\r\n]*RESPONSE MANAGEMENT\s+(\S+)\s*$", text)
    )
    sections: dict[str, str] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        sections[header.group(1).upper()] = text[header.end():end]
    return sections


def parse_live_pmc(outputs: dict[str, str], previous_counts: dict[str, int] | None, elapsed_s: float) -> tuple[dict, dict[str, int]]:
    """Convert measured linuxptp 3.x/4.x management output to one telemetry row."""
    combined = "\n".join(outputs.values())
    current = outputs.get("CURRENT_DATA_SET", "")
    time_status = outputs.get("TIME_STATUS_NP", "")
    parent = outputs.get("PARENT_DATA_SET", "")
    port = outputs.get("PORT_DATA_SET", "")
    stats = outputs.get("PORT_STATS_NP", "")
    sync = parse_pmc_output(combined)

    # Absence is not a perfect zero: carry it through as invalid telemetry.
    offset = _number(current, "offsetFromMaster", _number(time_status, "master_offset"))
    delay = _number(current, "meanPathDelay")
    rate_fraction = _number(time_status, "cumulativeScaledRateOffset", 0.0) or 0.0
    counts = {
        name: _integer(stats, rf"^\s*(?:rx|tx)_{re.escape(name)}\s+(\d+)\s*$", 0)
        for name in ("Sync", "Follow_Up", "Delay_Req", "Delay_Resp", "Announce", "Signaling", "Management")
    }
    rate = 0.0
    dominant_type = "Sync"
    if previous_counts and elapsed_s > 0:
        deltas = {name: max(0, value - previous_counts.get(name, value)) for name, value in counts.items()}
        rate = sum(deltas.values()) / elapsed_s
        if any(deltas.values()):
            dominant_type = max(deltas, key=deltas.get)

    gm_identity = _token(parent, r"^\s*grandmasterIdentity\s+([0-9a-f.:-]+)\s*$", "unknown")
    clock_class = _integer(parent, r"^\s*(?:gm\.)?ClockClass\s+(\d+)\s*$", sync.clock_class or 248)
    port_state = _token(port, r"^\s*portState\s+(\S+)\s*$", "UNKNOWN").upper()
    # UNCALIBRATED is a servo convergence state with a present GM, not holdover.
    holdover = bool(sync.holdover or port_state in {"FAULTY", "DISABLED"})
    gm_missing = "gmpresent false" in combined.lower()
    # In live netem holdover, ptp4l elects its own clock (ClockClass 255) and
    # reports zero offset/path values. Those are not measurements of an upstream
    # reference, so they must not be considered valid timing telemetry.
    local_or_holdover_source = holdover or port_state in {"MASTER", "LISTENING", "FAULTY", "DISABLED"}
    timing_source_unavailable = gm_missing or local_or_holdover_source
    offset_valid = offset is not None and not timing_source_unavailable
    path_delay_valid = delay is not None and not timing_source_unavailable
    telemetry_valid = offset_valid and path_delay_valid
    row = {
        "offset_ns": offset if offset_valid else np.nan,
        "measured_offset_ns": offset if offset_valid else np.nan,
        "path_delay_ns": delay if path_delay_valid else np.nan,
        "offset_valid": offset_valid,
        "path_delay_valid": path_delay_valid,
        "telemetry_valid": telemetry_valid,
        "stale_s": 0.0,
        "pdv_ns": 0.0 if path_delay_valid else np.nan,
        "freq_error_ppb": rate_fraction * 1e9,
        "synce_ql": 4,
        "ptp_seq_id": 0,
        "ptp_msg_type": dominant_type,
        "msg_rate_hz": rate,
        "grandmaster_identity": gm_identity,
        "grandmaster_priority1": _integer(parent, r"^\s*grandmasterPriority1\s+(\d+)\s*$", 128),
        "grandmaster_clock_class": clock_class,
        "grandmaster_clock_accuracy": _integer(parent, r"^\s*(?:gm\.)?ClockAccuracy\s+(0x[0-9a-f]+|\d+)\s*$", 0xFE),
        "offset_scaled_log_variance": _integer(parent, r"^\s*(?:gm\.)?OffsetScaledLogVariance\s+(0x[0-9a-f]+|\d+)\s*$", 0xFFFF),
        "grandmaster_priority2": _integer(parent, r"^\s*grandmasterPriority2\s+(\d+)\s*$", 128),
        "steps_removed": _integer(current, r"^\s*stepsRemoved\s+(\d+)\s*$", 0),
        "gnss_sync_status": sync.gnss_sync_status,
        "satellites_tracked": sync.satellites_tracked if sync.satellites_tracked is not None else -1,
        "gnss_available": sync.gnss_available,
        "holdover": holdover,
        "port_state": port_state,
    }
    return row, counts


class LiveCollector:
    """Poll pmc datasets and expose one canonical row per successful cycle."""

    def __init__(
        self,
        namespace: str | None = None,
        scenario: str = "live",
        poll_interval_s: float = 0.1,
        synce_log: Path | None = None,
        pmc_socket: str = "/var/run/ptp4l-splane-slave",
        runner: Runner = _run,
    ) -> None:
        self.namespace = namespace
        self.scenario = scenario
        self.poll_interval_s = float(poll_interval_s)
        self.synce_log = synce_log
        self.pmc_socket = pmc_socket
        self.runner = runner
        self.started = time.monotonic()
        self.previous_poll: float | None = None
        self.previous_counts: dict[str, int] | None = None
        self.sequence = 0
        self.delay_history: deque[float] = deque(maxlen=max(10, int(10.0 / self.poll_interval_s)))
        self.previous_offset: float | None = None
        self.last_valid_elapsed: float | None = None
        self.unsupported: set[str] = set()
        self.pmc_down = False
        self.synce_available = bool(shutil.which("synce4l") or (synce_log and synce_log.exists()))
        if not self.synce_available:
            LOG.warning("synce4l unavailable; synce_ql will be recorded as unavailable/DNU (4)")

    def _pmc(self, dataset: str) -> str:
        command = ["pmc", "-u", "-b", "0", "-s", self.pmc_socket, f"GET {dataset}"]
        if self.namespace:
            command = ["ip", "netns", "exec", self.namespace, *command]
        result = self.runner(command, max(1.0, self.poll_interval_s * 4.0))
        text = (result.stdout or "") + "\n" + (result.stderr or "")
        if result.returncode != 0 or "bad command" in text.lower():
            if dataset not in self.unsupported:
                LOG.warning("pmc dataset %s unavailable: %s", dataset, text.strip() or f"exit {result.returncode}")
                self.unsupported.add(dataset)
            return ""
        return text

    def _poll_pmc(self) -> dict[str, str]:
        """Poll all supported datasets in one pmc process to preserve subsecond cadence."""
        requested = [dataset for dataset in PMC_DATASETS if dataset not in self.unsupported]
        command = [
            "pmc",
            "-u",
            "-b",
            "0",
            "-s",
            self.pmc_socket,
            *(f"GET {dataset}" for dataset in requested),
        ]
        if self.namespace:
            command = ["ip", "netns", "exec", self.namespace, *command]
        result = self.runner(command, max(1.0, self.poll_interval_s * 4.0))
        text = (result.stdout or "") + "\n" + (result.stderr or "")
        sections = _split_pmc_sections(text)
        outputs: dict[str, str] = {}
        for dataset in requested:
            outputs[dataset] = sections.get(dataset, "")
            if re.search(rf"bad command:\s*GET {re.escape(dataset)}", text, re.IGNORECASE):
                if dataset not in self.unsupported:
                    LOG.warning("pmc dataset %s unsupported by this linuxptp build", dataset)
                    self.unsupported.add(dataset)
        if result.returncode != 0 and not any(outputs.values()):
            if not self.pmc_down:
                LOG.warning("pmc poll unavailable: %s", text.strip() or f"exit {result.returncode}")
            self.pmc_down = True
        elif any(outputs.values()) and self.pmc_down:
            LOG.info("pmc polling recovered")
            self.pmc_down = False
        return outputs

    def _synce_ql(self) -> int:
        if self.synce_log and self.synce_log.exists():
            return parse_synce4l_ql(self.synce_log.read_text(encoding="utf-8", errors="replace")) or 4
        return 4

    def _invalid_sample(self, elapsed: float) -> dict:
        """Record a failed poll as invalid instead of silently dropping the cycle."""
        stale_s = elapsed - self.last_valid_elapsed if self.last_valid_elapsed is not None else elapsed
        self.sequence += 1
        frame = coerce_telemetry(pd.DataFrame([{
            "t_s": elapsed, "scenario": self.scenario, "offset_ns": np.nan,
            "measured_offset_ns": np.nan, "path_delay_ns": np.nan, "pdv_ns": np.nan,
            "offset_valid": False, "path_delay_valid": False, "telemetry_valid": False,
            "stale_s": max(0.0, stale_s), "ptp_seq_id": self.sequence,
            "attack_flag": False, "fault_flag": False, "run_id": 0, "label": "healthy",
        }]))
        return frame.iloc[0].to_dict()

    def sample(self) -> dict:
        now = time.monotonic()
        outputs = self._poll_pmc()
        elapsed = now - self.started
        if not any(outputs.values()):
            self.previous_poll = now
            return self._invalid_sample(elapsed)
        poll_elapsed = now - self.previous_poll if self.previous_poll is not None else self.poll_interval_s
        parsed, counts = parse_live_pmc(outputs, self.previous_counts, poll_elapsed)
        delay = parsed["path_delay_ns"]
        if bool(parsed["path_delay_valid"]) and delay is not None and float(delay) > 0:
            delay = float(delay)
            self.delay_history.append(delay)
            parsed["pdv_ns"] = delay - float(np.median(self.delay_history))
        offset = parsed["offset_ns"]
        if (
            bool(parsed["offset_valid"])
            and offset is not None
            and abs(float(parsed["freq_error_ppb"])) < 1e-12
            and self.previous_offset is not None
            and poll_elapsed > 0
        ):
            offset = float(offset)
            parsed["freq_error_ppb"] = (offset - self.previous_offset) / poll_elapsed
        if bool(parsed["offset_valid"]) and offset is not None:
            self.previous_offset = float(offset)
        if bool(parsed["telemetry_valid"]):
            self.last_valid_elapsed = elapsed
        else:
            parsed["stale_s"] = elapsed - self.last_valid_elapsed if self.last_valid_elapsed is not None else elapsed
        self.previous_counts = counts
        self.previous_poll = now
        self.sequence += 1
        parsed.update(
            {
                "t_s": elapsed,
                "scenario": self.scenario,
                "ptp_seq_id": self.sequence,
                "synce_ql": self._synce_ql(),
                "attack_flag": False,
                "fault_flag": False,
                "run_id": 0,
                "label": "healthy",
            }
        )
        frame = coerce_telemetry(pd.DataFrame([parsed]))
        return frame.iloc[0].to_dict()


def collect(
    duration_s: float,
    out: Path,
    poll_interval_s: float,
    namespace: str | None,
    scenario: str,
    synce_log: Path | None,
    pmc_socket: str,
) -> int:
    collector = LiveCollector(namespace, scenario, poll_interval_s, synce_log, pmc_socket)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    started = time.monotonic()
    try:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=TELEMETRY_COLUMNS)
            writer.writeheader()
            while duration_s <= 0 or time.monotonic() - started < duration_s:
                cycle = time.monotonic()
                row = collector.sample()
                if row is not None:
                    writer.writerow(row)
                    handle.flush()
                    count += 1
                time.sleep(max(0.0, poll_interval_s - (time.monotonic() - cycle)))
    except KeyboardInterrupt:
        LOG.info("collection interrupted; flushed %d rows", count)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=60.0, help="seconds; <=0 runs until Ctrl-C")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--namespace", default=None, help="network namespace containing the target ptp4l socket")
    parser.add_argument("--scenario", default="live")
    parser.add_argument("--synce-log", type=Path, default=None)
    parser.add_argument("--pmc-socket", default="/var/run/ptp4l-splane-slave")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    rows = collect(
        args.duration,
        args.out,
        args.poll_interval,
        args.namespace,
        args.scenario,
        args.synce_log,
        args.pmc_socket,
    )
    LOG.info("wrote %d canonical telemetry rows to %s", rows, args.out)


if __name__ == "__main__":
    main()
