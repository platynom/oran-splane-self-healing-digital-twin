"""S11 mechanism probe analyser. Frozen detector, unchanged thresholds. Feasibility only."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(APP))
from streaming_discriminator_v1 import packet_from_frame                      # noqa: E402
from streaming_discriminator_v3_nonoverlap import NonoverlapV3State, observe_nonoverlap_v3  # noqa: E402
from ingest.ptp_wire import read_pcap                                          # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "spike_two_segment"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def phases() -> dict:
    out = {}
    for line in (OUT / "events.log").read_text().splitlines():
        m = re.search(r"event=(\S+).*monotonic_s=([\d.]+)", line)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def replay(cap: Path) -> dict:
    """One causal pass over the whole capture; record when each classification first appears."""
    cid = sha256(cap)
    st = NonoverlapV3State(); counts = Counter(); first = {}; start = None
    persist_times = []
    for ts_ns, frame in read_pcap(str(cap)):
        ts = ts_ns / 1e9
        if start is None:
            start = ts
        o = observe_nonoverlap_v3(st, packet_from_frame(cid, ts, frame))
        counts[o["classification"]] += 1
        if o["classification"] not in first:
            first[o["classification"]] = round(ts - start, 6)
        if o["classification"] == "NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED":
            persist_times.append(round(ts - start, 6))
    return {"capture_sha256": cid, "records": sum(counts.values()),
            "classification_counts": dict(counts),
            "first_classification_s": first,
            "persistence_event_times_s": persist_times,
            "any_persistence": counts["NONOVERLAPPING_BLOCK_PERSISTENCE_OBSERVED"] > 0}


def port_states(path: Path) -> dict:
    if not path.is_file():
        return {"present": False}
    txt = path.read_text()
    return {"present": True,
            "portIdentity_states": re.findall(r"portState\s+(\w+)", txt),
            "raw_excerpt": txt.strip().splitlines()[:20]}


def tc_counter(path: Path) -> dict:
    if not path.is_file():
        return {"present": False}
    t = path.read_text()
    qd = t.strip().splitlines()[0] if t.strip() else ""
    sent = re.search(r"Sent \d+ bytes (\d+) pkt", t)
    drop = re.search(r"dropped (\d+)", t)
    return {"present": True, "qdisc_line": qd,
            "sent_pkt": int(sent.group(1)) if sent else None,
            "dropped": int(drop.group(1)) if drop else None,
            "counter_informative": "noqueue" not in qd}


def main() -> None:
    ev = phases()
    res = {
        "schema_version": "s11-two-segment-mechanism-probe-v1",
        "scope": ("Feasibility probe of a commanded failover between two INDEPENDENT L2 segments. "
                  "No closed-loop experiment, no recovery claim, no performance estimate."),
        "phase_monotonic_s": ev,
        "segment1_capture": replay(OUT / "capture_seg1.pcap"),
        "segment2_capture": replay(OUT / "capture_seg2.pcap"),
        "port_states": {k: port_states(OUT / f"portstate_{k}.txt") for k in ("p1", "p2", "p3")},
        "tc_counters": {f"{s}_{p}": tc_counter(OUT / f"tc_{s}_{p}.txt")
                        for s in ("seg1", "seg2") for p in ("p1", "p2", "p3")},
    }
    ACTIVE = {"SLAVE", "UNCALIBRATED"}      # port carrying timing, or converging to it
    STANDBY = {"LISTENING", "PASSIVE"}       # port available but not carrying timing
    q = {}
    st1 = res["port_states"]["p1"].get("portIdentity_states", [])
    q["Q1_two_ports_one_active_one_standby_and_neither_MASTER"] = {
        "answer": ("YES" if (any(s in ACTIVE for s in st1) and any(s in STANDBY for s in st1)
                             and "MASTER" not in st1) else "NO"),
        "observed_phase1_port_states": st1,
        "note": ("ptp4l reports UNCALIBRATED for an active port still converging and LISTENING for a "
                 "standby port. A port in MASTER state would mean the two segments are not "
                 "independent and the topology could not fail over."),
    }
    q["Q2_both_segments_carry_ptp"] = {
        "answer": ("YES" if res["segment1_capture"]["records"] > 0 and res["segment2_capture"]["records"] > 0 else "NO"),
        "segment1_records": res["segment1_capture"]["records"],
        "segment2_records": res["segment2_capture"]["records"],
    }
    q["Q3_detector_observes_the_impaired_segment"] = {
        "answer": "YES" if res["segment1_capture"]["any_persistence"] else "NO",
        "persistence_event_times_s": res["segment1_capture"]["persistence_event_times_s"],
        "impairment_applied_at_monotonic_s": ev.get("phase2_jitter_impairment_applied_seg1"),
    }
    st3 = res["port_states"]["p3"].get("portIdentity_states", [])
    log = (OUT / "slave.log").read_text()
    trans = re.findall(r"ptp4l\[([\d.]+)\]: (port \d+: \w+ to \w+ on \w+)", log)
    down_t = ev.get("phase3_commanded_action_port_down")
    faulty = [(float(a), b) for a, b in trans if "to FAULTY" in b]
    took_over = [(float(a), b) for a, b in trans if "LISTENING to UNCALIBRATED" in b and down_t and float(a) >= down_t - 1]
    latency = round(took_over[0][0] - faulty[0][0], 6) if (faulty and took_over) else None
    seg1_egress = (res["tc_counters"]["seg1_p3"].get("sent_pkt"), res["tc_counters"]["seg1_p2"].get("sent_pkt"))
    delta = (seg1_egress[0] - seg1_egress[1]) if None not in seg1_egress else None
    q["Q4_commanded_action_moves_the_active_port_to_the_clean_segment"] = {
        "answer": ("YES" if (any(s in ACTIVE for s in st3) and st3 != st1
                             and faulty and took_over) else "NO"),
        "phase1_states": st1, "phase3_states": st3,
        "action_event_present": "phase3_commanded_action_port_down" in ev,
        "impaired_port_fault_transition": faulty[0][1] if faulty else None,
        "standby_port_takeover_transition": took_over[0][1] if took_over else None,
        "takeover_latency_s_from_fault_to_takeover": latency,
        "segment1_egress_packets_after_action": delta,
        "segment1_egress_packets_during_impairment": seg1_egress[1],
        "egress_note": ("Packets leaving the bridge toward the impaired slave port after the action, "
                        "compared with the same length of time before it. A near-zero value is "
                        "on-wire evidence the slave stopped using that segment."),
    }
    q["Q5_clean_segment_stays_unobserved_throughout"] = {
        "answer": "YES" if not res["segment2_capture"]["any_persistence"] else "NO",
        "segment2_persistence_times_s": res["segment2_capture"]["persistence_event_times_s"],
    }
    res["capability_questions"] = q
    res["interpretation_limits"] = [
        "The commanded action stops the slave USING the impaired segment. It does not repair the "
        "segment: segment 1 stays impaired on the wire and its capture continues to show it.",
        "The detector is replayed over each whole capture in one causal pass; state is never reset "
        "mid-capture and no future packet is used.",
        "A single probe run. No repetition, no control arm, no latency or effectiveness estimate.",
        "Shared host software clock, free_running 1. No physical timing or clock-recovery claim.",
        "A tc counter on a noqueue qdisc does not count packets; such a counter is uninformative "
        "and is flagged as counter_informative=false rather than read as zero traffic.",
    ]
    (OUT / "S11_MECHANISM_PROBE.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({"capability_questions": {k: v["answer"] for k, v in q.items()}}, indent=2))


if __name__ == "__main__":
    main()
