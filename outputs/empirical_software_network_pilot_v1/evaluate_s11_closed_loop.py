"""S11 closed-loop evaluation. Frozen detector artefacts only; no re-detection, no retuning."""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "s11_runs"
PROTOCOL = HERE / "S11_CLOSED_LOOP_PROTOCOL.json"
PLAN = {"action": [f"20260913_s11_act{i}" for i in range(1, 6)],
        "no_action": [f"20260913_s11_noact{i}" for i in range(1, 6)]}
# These are the evidence inputs this evaluator actually reads.  A manifest that
# omits one is not evidence-bound, even if every entry it does contain hashes.
REQUIRED_EVALUATION_INPUTS = frozenset({
    "capture_seg1.pcap", "capture_seg2.pcap", "decision_log.jsonl", "slave.log",
    "tc_seg1_p1.txt", "tc_seg1_p2.txt",
})


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wilson(k: int, n: int, z: float = 1.95996398454) -> dict:
    if n == 0:
        return {"k": 0, "n": 0, "proportion": None, "wilson95": [None, None]}
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"k": k, "n": n, "proportion": p, "wilson95": [max(0, c - r), min(1, c + r)]}


def verify_frozen() -> dict:
    fr = json.loads(PROTOCOL.read_text())["frozen_rule"]
    app = HERE.parents[1] / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
    actual = {"v1_engine_sha256": sha256(HERE / "streaming_discriminator_v1.py"),
              "v3_nonoverlap_engine_sha256": sha256(HERE / "streaming_discriminator_v3_nonoverlap.py"),
              "live_detector_sha256": sha256(HERE / "live_detect_and_act.py"),
              "s11_runner_sha256": sha256(app / "harness" / "run_s11_closed_loop.sh")}
    bad = {k: {"expected": fr[k], "actual": v} for k, v in actual.items() if fr[k].lower() != v.lower()}
    if bad:
        raise RuntimeError("frozen input hash mismatch: " + json.dumps(bad, sort_keys=True))
    return {"frozen_hashes_match": True, **actual}


def tc_sent(p: Path):
    if not p.is_file():
        return None, None
    t = p.read_text(); line = t.strip().splitlines()[0] if t.strip() else ""
    m = re.search(r"Sent \d+ bytes (\d+) pkt", t)
    return (int(m.group(1)) if m else None), ("noqueue" not in line)


def manifest_entries(path: Path) -> dict[str, str]:
    out = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise RuntimeError(f"malformed blank manifest line {number}: {path}")
        digest, sep, raw = line.partition("  ")
        name = Path(raw.strip()).name
        if not (sep and raw.strip() and re.fullmatch(r"[0-9a-f]{64}", digest) and name):
            raise RuntimeError(f"malformed manifest line {number}: {path}")
        if name in out:
            raise RuntimeError(f"duplicate manifest basename {name!r}: {path}")
        out[name] = digest
    if not out: raise RuntimeError(f"empty or malformed source manifest: {path}")
    return out


def sealed_log_prefix(path: Path, expected: str) -> tuple[bytes, int] | None:
    data = path.read_bytes(); lines = data.splitlines(keepends=True); prefix = b""
    for index, line in enumerate(lines, start=1):
        prefix += line
        if hashlib.sha256(prefix).hexdigest() == expected: return prefix, index
    return None


def verify_run_inputs(d: Path) -> dict:
    manifest = manifest_entries(d / "source_manifest.sha256")
    missing_required = sorted(REQUIRED_EVALUATION_INPUTS - manifest.keys())
    if missing_required:
        raise RuntimeError(f"manifest lacks evaluator input(s) for {d.name}: {missing_required}")
    mismatches = {}; appended = None; sealed_decision = None
    for name, expected in manifest.items():
        path = d / name
        if not path.is_file(): mismatches[name] = "missing"; continue
        actual = sha256(path)
        if actual == expected: continue
        if name == "decision_log.jsonl":
            prefix = sealed_log_prefix(path, expected)
            if prefix is not None:
                sealed_decision, sealed_lines = prefix
                current_lines = len(path.read_bytes().splitlines())
                appended = {"sealed_lines": sealed_lines, "current_lines": current_lines,
                            "reason": "post_seal_append_only; sealed decision prefix is used for S11 evidence"}
                continue
        mismatches[name] = "hash_mismatch"
    if mismatches: raise RuntimeError(f"manifest input mismatch for {d.name}: {json.dumps(mismatches, sort_keys=True)}")
    if sealed_decision is None: sealed_decision = (d / "decision_log.jsonl").read_bytes()
    return {"manifest_entries_rehashed": len(manifest), "all_manifest_inputs_match_or_accepted_prefix": True,
            "decision_log_post_seal_append": appended, "sealed_decision_log_bytes": sealed_decision}


def receiver_state_eligible(transitions: list[tuple[float, int, str]]) -> bool:
    """S11 protocol excludes any receiver port entering MASTER, preserving the run."""
    return not any("to MASTER" in text for _, _, text in transitions)


def evaluate_run(name: str) -> dict:
    d = RUNS / name
    integrity = verify_run_inputs(d)
    rows = [json.loads(l) for l in integrity.pop("sealed_decision_log_bytes").decode("utf-8").splitlines() if l.strip()]
    by = {r["event"]: r for r in rows}
    trig = by.get("detection_trigger")
    exec_res = by.get("action_execution_result")
    withheld = "action_withheld" in by

    if trig is None or by.get("stream_started", {}).get("arm") not in ("action", "no_action"):
        raise RuntimeError(f"missing eligible sealed detector records: {name}")
    expected_arm = "action" if name in PLAN["action"] else "no_action"
    if by["stream_started"]["arm"] != expected_arm:
        raise RuntimeError(f"sealed decision arm mismatch: {name}")
    log = (d / "slave.log").read_text()
    trans = [(float(a), int(b), c) for a, b, c in
             re.findall(r"ptp4l\[([\d.]+)\]: port (\d+): (\w+ to \w+ on [\w_() ]+)", log)]
    faulty = [x for x in trans if "to FAULTY" in x[2]]
    # A takeover is a standby port becoming active AFTER the impaired port faulted, on a
    # DIFFERENT port.  The printed ptp4l timebase is not mapped to the detector's host
    # monotonic time in the sealed evidence, so this uses ordering only within slave.log.
    takeover = []
    if faulty:
        ft, fport, _ = faulty[0]
        takeover = [x for x in trans
                    if "LISTENING to UNCALIBRATED" in x[2] and x[1] != fport and x[0] >= ft]
    moved = bool(faulty and takeover)
    master_transition = [x for x in trans if "to MASTER" in x[2]]

    s1_p1, inf1 = tc_sent(d / "tc_seg1_p1.txt")
    s1_p2, inf2 = tc_sent(d / "tc_seg1_p2.txt")
    return {
        "run": name,
        "detector_triggered": trig is not None,
        "detection_trigger_monotonic_s": trig.get("monotonic_s") if trig else None,
        "action_withheld": withheld,
        "action_executed": exec_res is not None,
        "action_returncode": exec_res.get("returncode") if exec_res else None,
        "detection_to_action_result_s": (round(exec_res["monotonic_s"] - trig["monotonic_s"], 6)
                                         if (trig and exec_res) else None),
        "impaired_port_fault": (f"port {faulty[0][1]}: {faulty[0][2]}" if faulty else None),
        "standby_takeover": (f"port {takeover[0][1]}: {takeover[0][2]}" if takeover else None),
        "fault_to_takeover_s": (round(takeover[0][0] - faulty[0][0], 6) if (faulty and takeover) else None),
        "active_port_moved_to_clean_segment": moved,
        "receiver_port_state_eligible": receiver_state_eligible(trans),
        "master_transitions": [f"port {x[1]}: {x[2]}" for x in master_transition],
        "ordering_timebase_limit": "Detector/action uses host monotonic time. The ptp4l printed timestamp basis was not established from the sealed local package/source, and no cross-clock mapping was recorded. Port-event ordering is used only within slave.log; a numeric command-to-fault interval is not established.",
        "seg1_egress_pkt_phase1": s1_p1, "seg1_egress_pkt_phase2": s1_p2,
        "seg1_egress_counter_informative": [inf1, inf2],
        "seg1_egress_note": ("phase1 is read before netem is applied, on a noqueue qdisc that does not count packets; only the phase2 value is informative"),
        "capture_seg1_sha256": sha256(d / "capture_seg1.pcap"),
        "capture_seg2_sha256": sha256(d / "capture_seg2.pcap"),
        "manifest_sha256": sha256(d / "source_manifest.sha256"),
        "input_integrity": integrity,
    }


def main() -> None:
    frozen = verify_frozen()
    runs = {arm: {n: evaluate_run(n) for n in names} for arm, names in PLAN.items()}
    eligible = {arm: {n: r for n, r in rs.items() if r["receiver_port_state_eligible"]}
                for arm, rs in runs.items()}
    summary = {arm: wilson(sum(r["active_port_moved_to_clean_segment"] for r in rs.values()), len(rs))
               for arm, rs in eligible.items()}
    trig = {arm: wilson(sum(r["detector_triggered"] for r in rs.values()), len(rs))
            for arm, rs in runs.items()}
    a, na = summary["action"], summary["no_action"]
    pre = json.loads(PROTOCOL.read_text())["prespecified_interpretation"]
    if na["k"] > 0:
        branch = "no_action_>0of5"
    elif a["k"] >= 4:
        branch = "action_>=4of5_and_no_action_0of5"
    else:
        branch = "action_<4of5_with_triggers_present"
    bad_rc = [r["run"] for rs in runs.values() for r in rs.values()
              if r["action_returncode"] not in (None, 0)]
    excluded = [r["run"] for rs in runs.values() for r in rs.values()
                if not r["receiver_port_state_eligible"]]
    out = {
        "schema_version": "s11-closed-loop-evaluation-v1",
        "protocol": "S11_CLOSED_LOOP_PROTOCOL.json",
        "frozen_input_verification": frozen,
        "runs": runs,
        "primary_outcome_summary": summary,
        "primary_outcome_eligible_runs": {arm: sorted(rs) for arm, rs in eligible.items()},
        "excluded_receiver_master_runs": excluded,
        "detector_trigger_rate": trig,
        "prespecified_branch_selected": branch,
        "prespecified_statement": pre[branch],
        "action_command_failures": bad_rc,
        "limits": [
            "Eligible n is reported per arm. Any receiver-MASTER run is retained but excluded by the frozen protocol; this pilot happened to have none.",
            "The commanded action stops the receiver using the impaired segment. The segment stays "
            "impaired; nothing was repaired and no laboratory impairment was removed.",
            "Shared host software clock, free_running 1. No physical clock recovery is demonstrated.",
            "Detector sensitivity is roughly 13 of 15 from V3-V5; a non-trigger is a known miss, "
            "not an excluded run.",
            "A tc counter on a noqueue qdisc does not count packets and is flagged as uninformative.",
        ],
    }
    (HERE / "S11_CLOSED_LOOP_EVALUATION.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"primary_outcome_summary": summary, "detector_trigger_rate": trig,
                      "branch": branch, "action_command_failures": bad_rc}, indent=2))


if __name__ == "__main__":
    main()
