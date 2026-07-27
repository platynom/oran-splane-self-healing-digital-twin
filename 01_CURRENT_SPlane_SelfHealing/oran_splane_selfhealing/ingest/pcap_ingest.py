from __future__ import annotations

"""Ingest a PTP-over-Ethernet packet capture into canonical S-plane telemetry.

Implements the IEEE-1588 end-to-end delay computation as a slave would:

    meanPathDelay = ((t2 - t1) + (t4 - t3)) / 2
    offsetFromMaster = (t2 - t1) - meanPathDelay

where t1 = Sync/Follow_Up origin timestamp (master clock, from payload),
t2 = Sync arrival (capture timestamp), t3 = Delay_Req send (capture timestamp),
t4 = Delay_Req receipt at master (Delay_Resp payload timestamp). This is exactly
how linuxptp derives 'master offset', so the same features apply to real traces
(e.g. the released genesys-neu/s-plane or TIMESAFE captures).
"""

from pathlib import Path

import pandas as pd

from ingest import ptp_wire as w
from ingest.schema import coerce_telemetry


def pcap_to_telemetry(path: str | Path, scenario: str = "live", label: str = "unlabeled",
                      tolerate_incomplete: bool = True, stale_path_delay_s: float = 2.0) -> pd.DataFrame:
    """Recover S-plane offset telemetry from a PTP-over-Ethernet capture.

    When ``tolerate_incomplete`` is True (default), captures where the Delay_Req/
    Delay_Resp exchange is missing or stale — e.g. a holdover / link-blackout with
    heavy loss — still yield rows, using the last-known path delay and marking
    ``holdover=True``. This represents a timing OUTAGE as degraded telemetry (which
    is exactly the fault condition the self-healing loop must react to) instead of
    raising. Set it False for strict offset-only recovery.
    """
    last_t1 = None            # master origin (ns) of most recent resolved Sync
    last_t2 = None            # slave arrival (ns) of most recent Sync
    last_sync_corr = 0.0
    pending_sync = {}         # seq -> (t2, corr) awaiting a Follow_Up (two-step)
    dreq_t3 = {}              # seq -> t3 (ns)
    mean_path_delay = None    # ns, current best estimate
    last_known_pd = None      # ns, last completed exchange
    last_exchange_ns = None   # capture time of last completed exchange
    t0 = None
    syncs_seen = 0
    rows = []
    announce_clock_class = None
    announce_time_source = None

    def emit(seq: int, t_ns: int, msg_type: str):
        nonlocal rows
        if last_t1 is None or last_t2 is None:
            return
        raw = last_t2 - last_t1 - last_sync_corr
        if mean_path_delay is not None:
            stale = last_exchange_ns is not None and (t_ns - last_exchange_ns) / 1e9 > stale_path_delay_s
            pd_use, hold = mean_path_delay, bool(stale)
        elif tolerate_incomplete:
            # no delay exchange yet: degraded/holdover telemetry
            pd_use, hold = (last_known_pd if last_known_pd is not None else 0.0), True
        else:
            return
        if announce_clock_class == 7:
            hold = True
        gnss_available = True
        if announce_clock_class is not None or announce_time_source is not None:
            gnss_available = announce_time_source == 0x20 or announce_clock_class == 6
        rows.append({
            "t_s": (t_ns - t0) / 1e9,
            "offset_ns": float(raw - pd_use),
            "path_delay_ns": float(pd_use),
            "ptp_seq_id": int(seq),
            "ptp_msg_type": msg_type,
            "gnss_available": gnss_available,
            "holdover": hold,
        })

    for cap_ns, frame in w.read_pcap(str(path)):
        payload = w.parse_eth_frame(frame)
        if payload is None:
            continue
        msg = w.decode_ptp_payload(payload)
        if msg is None:
            continue
        if t0 is None:
            t0 = cap_ns

        if msg.msg_type == w.MT_SYNC:
            syncs_seen += 1
            if msg.origin_ts_ns:  # one-step: origin carried in Sync
                last_t1, last_t2, last_sync_corr = int(msg.origin_ts_ns), cap_ns, msg.correction_ns
                emit(msg.seq_id, cap_ns, w.MSG_NAME[msg.msg_type])
            else:                 # two-step: wait for Follow_Up
                pending_sync[msg.seq_id] = (cap_ns, msg.correction_ns)
        elif msg.msg_type == w.MT_FOLLOW_UP:
            if msg.seq_id in pending_sync and msg.origin_ts_ns is not None:
                t2, corr = pending_sync.pop(msg.seq_id)
                last_t1, last_t2, last_sync_corr = int(msg.origin_ts_ns), t2, corr + msg.correction_ns
                emit(msg.seq_id, t2, "Sync")
                emit(msg.seq_id, cap_ns, w.MSG_NAME[msg.msg_type])
        elif msg.msg_type == w.MT_DELAY_REQ:
            dreq_t3[msg.seq_id] = cap_ns
            emit(msg.seq_id, cap_ns, w.MSG_NAME[msg.msg_type])
        elif msg.msg_type == w.MT_DELAY_RESP:
            if msg.seq_id in dreq_t3 and msg.origin_ts_ns is not None and last_t1 is not None:
                t3 = dreq_t3.pop(msg.seq_id)
                t4 = int(msg.origin_ts_ns)
                mean_path_delay = ((last_t2 - last_t1) + (t4 - t3)) / 2.0
                last_known_pd, last_exchange_ns = mean_path_delay, cap_ns
            emit(msg.seq_id, cap_ns, w.MSG_NAME[msg.msg_type])
        elif msg.msg_type == w.MT_ANNOUNCE:
            if msg.grandmaster_clock_class is not None:
                announce_clock_class = msg.grandmaster_clock_class
            if msg.time_source is not None:
                announce_time_source = msg.time_source
            emit(msg.seq_id, cap_ns, w.MSG_NAME[msg.msg_type])

    if not rows:
        raise ValueError(
            f"no PTP offset samples recovered from pcap (syncs_seen={syncs_seen}). "
            "Need at least paired Sync+Follow_Up (or one-step Sync); with "
            "tolerate_incomplete=True a total Sync outage still yields nothing."
        )
    df = pd.DataFrame(rows).sort_values("t_s").reset_index(drop=True)
    df["scenario"] = scenario
    df["label"] = label
    return coerce_telemetry(df)
