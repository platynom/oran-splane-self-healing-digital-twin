"""S12: packet-path comparison after the detector trigger, against matched no-action.

Question: after the detection trigger, does the frozen detector still observe dispersion
persistence on the segment the receiver is ACTUALLY USING?
  action arm    -> the receiver moved to segment 2, so segment 2 is the active path
  no_action arm -> the receiver stayed on segment 1, so segment 1 is the active path
The trigger instant is the detector-recorded capture-packet timestamp.  It partitions each
selected capture in capture time.  Receiver transition timestamps have no recorded mapping to
that timebase, so this is not asserted to be an interval after the takeover/action.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(APP))
from streaming_discriminator_v1 import packet_from_frame                       # noqa: E402
from streaming_discriminator_v3_nonoverlap import NonoverlapV3State, observe_nonoverlap_v3  # noqa: E402
from ingest.ptp_wire import read_pcap                                           # noqa: E402

RUNS = HERE / "s11_runs"
PLAN = {"action": [f"20260913_s11_act{i}" for i in range(1, 6)],
        "no_action": [f"20260913_s11_noact{i}" for i in range(1, 6)]}
TRIG = "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wilson(k, n, z=1.95996398454):
    if n == 0:
        return {"k": 0, "n": 0, "proportion": None, "wilson95": [None, None]}
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"k": k, "n": n, "proportion": p, "wilson95": [max(0, c - r), min(1, c + r)]}


def trigger_packet_ts(d: Path):
    for line in (d / "decision_log.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["event"] == "detection_trigger":
            return r.get("packet_ts")
    return None


def verified_active_capture(d: Path, arm: str, s11: dict) -> tuple[str | None, str]:
    """Use sealed S11 receiver transition evidence, never an arm-name shortcut."""
    if not s11.get("receiver_port_state_eligible"):
        return None, "receiver port entered MASTER; excluded"
    if arm == "action":
        takeover = s11.get("standby_takeover") or ""
        if s11.get("active_port_moved_to_clean_segment") and takeover.startswith("port 2:"):
            return "capture_seg2.pcap", "S11 sealed port-2 takeover after port-1 fault"
        return None, "no verified port-2 takeover"
    if s11.get("action_withheld") and not s11.get("active_port_moved_to_clean_segment") and not s11.get("impaired_port_fault"):
        return "capture_seg1.pcap", "S11 sealed no-action record with no port-1 fault/takeover"
    return None, "no verified retained segment-1 path"


def replay_after(cap: Path, split_ts: float) -> dict:
    cid = sha256(cap)
    st = NonoverlapV3State(); post = Counter(); pre = Counter()
    post_persist = []; last = None; valid_gaps = 0
    for ts_ns, frame in read_pcap(str(cap)):
        ts = ts_ns / 1e9; last = ts
        o = observe_nonoverlap_v3(st, packet_from_frame(cid, ts, frame))
        (post if ts > split_ts else pre)[o["classification"]] += 1
        if ts > split_ts and o["classification"] == TRIG:
            post_persist.append(round(ts - split_ts, 6))
        if ts > split_ts and "gap_s" in o: valid_gaps += 1
    eligible = valid_gaps >= 16
    return {"capture": cap.name, "capture_sha256": cid,
            "split_packet_ts": split_ts,
            "observation_window_after_trigger_s": (round(last - split_ts, 3) if last else None),
            "records_before": sum(pre.values()), "records_after": sum(post.values()),
            "persistence_after_trigger": post[TRIG],
            "persistence_offsets_after_trigger_s": post_persist,
            "valid_gap_observations_after_trigger": valid_gaps,
            "outcome_eligible": eligible,
            "clean_after_trigger": (post[TRIG] == 0 if eligible else None)}


def main() -> None:
    s11 = json.loads((HERE / "S11_CLOSED_LOOP_EVALUATION.json").read_text())["runs"]
    runs = {}
    for arm, names in PLAN.items():
        runs[arm] = {}
        for n in names:
            d = RUNS / n
            ts = trigger_packet_ts(d)
            cap_name, path_evidence = verified_active_capture(d, arm, s11[arm][n])
            runs[arm][n] = ({"error": "no detection_trigger recorded"} if ts is None
                            else {"error": path_evidence} if cap_name is None
                            else {**replay_after(d / cap_name, ts), "active_path_evidence": path_evidence,
                                  "capture_timestamp_timebase": "absolute pcap timestamp; trigger packet timestamp from the detector stream"})
    summary = {arm: wilson(sum(1 for r in rs.values() if r.get("clean_after_trigger") is True), len(rs))
               for arm, rs in runs.items()}
    a, na = summary["action"], summary["no_action"]
    if a["k"] == a["n"] and na["k"] == 0:
        verdict = ("In the selected-capture suffix after the detector trigger, the observation is absent "
                   "in every action run and present in every no-action run. This is not timed as post-takeover.")
    elif a["k"] > na["k"]:
        verdict = "Partial separation between arms; report per-run."
    else:
        verdict = "No benefit separation between arms."
    out = {
        "schema_version": "s12-measured-outcome-v1",
        "question": ("In the capture-time suffix after the detector trigger, does the frozen detector "
                     "observe dispersion persistence in the capture selected by sealed receiver-path evidence?"),
        "capture_selection_by_arm": {"action": "segment 2, selected because sealed logs show port-2 takeover",
                                      "no_action": "segment 1, selected because sealed logs show no retained path change"},
        "runs": runs,
        "clean_active_path_after_trigger": summary,
        "verdict": verdict,
        "limits": [
            "n=5 per arm; matched control on identical topology and identical impairment.",
            "The impaired segment was never repaired and the netem qdisc was never removed. "
            "The action changes which segment the receiver uses.",
            "This is a packet-observation outcome. It is NOT a clock-error, timing-quality, "
            "service-restoration or physical-recovery measurement.",
            "Shared host software clock under free_running 1.",
            "The post-trigger observation window differs per run; it is reported per run.",
            "The capture-time trigger split is not a measured post-takeover or post-command interval: no cross-clock mapping to the ptp4l transition log was recorded.",
        ],
    }
    (HERE / "S12_MEASURED_OUTCOME.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"clean_active_path_after_trigger": summary, "verdict": verdict}, indent=2))
    for arm, rs in runs.items():
        for n, r in rs.items():
            print(f"  {n[-8:]:9s} {r.get('capture','-'):17s} window={r.get('observation_window_after_trigger_s')}s "
                  f"post_records={r.get('records_after')} persistence_after={r.get('persistence_after_trigger')}")


if __name__ == "__main__":
    main()
