"""S15 independent validation evaluator. FROZEN by S15_INDEPENDENT_VALIDATION_PROTOCOL_V2.json.

Read-only on raw evidence. Executes the frozen analysis plan and nothing else. It contains no
tunable parameter: every constant below is quoted from the frozen protocol and any change to one
invalidates the validation.

It reports what it finds, including a poor result. It never re-labels, re-thresholds, drops an
UNKNOWN run silently, or substitutes another label source.
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "s15_runs"
PROTOCOL = HERE / "S15_INDEPENDENT_VALIDATION_PROTOCOL_V2.json"

# --- frozen constants, quoted from the protocol -----------------------------------------------
BOUNDARY_NS = 29000                 # receiver_measurement.boundary_ns
MIN_VALID_WINDOWS = 2               # receiver_measurement.minimum_valid_windows_per_run
TRIGGER_AMBIGUITY_S = 1.0           # detector_decision.ambiguity_rule, events.log utc resolution
MANDATORY = {"capture_seg1.pcap", "capture_seg2.pcap", "events.log", "slave.log",
             "master_a.log", "master_b.log", "slave.conf", "master_a.conf", "master_b.conf",
             "run_environment.txt", "decision_log.jsonl", "source_manifest.sha256"}

SERVO = re.compile(r"ptp4l\[([\d.]+)\]:.*?\bdelay (\d+) \+/- (\d+)")
FAULT = re.compile(r"ptp4l\[([\d.]+)\]: port (\d+): \w+ to FAULTY")
MASTER = re.compile(r"port \d+: \w+ to MASTER")
APPLY_MONO = re.compile(r"event=phase2_graded_jitter_applied_seg1\s+utc=(\S+)\s+monotonic_s=([\d.]+)")
COND = re.compile(r"_s15_(j\d+)_r\d+$")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def utc_to_epoch(s: str) -> float:
    import datetime as dt
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()


def seal_check(d: Path) -> list:
    """Returns a list of integrity problems. Empty means the run is sealed and consistent."""
    problems = []
    missing = sorted(MANDATORY - {p.name for p in d.iterdir() if p.is_file()})
    if missing:
        problems.append("missing mandatory files: " + ", ".join(missing))
    mp = d / "source_manifest.sha256"
    if not mp.is_file():
        problems.append("unsealed: no source_manifest.sha256")
        return problems
    man = {}
    for line in mp.read_text(errors="replace").splitlines():
        m = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line.strip())
        if m:
            man[Path(m.group(2)).name] = m.group(1)
    for name, want in man.items():
        if name == "source_manifest.sha256":
            continue
        fp = d / name
        if not fp.is_file():
            problems.append(f"manifest entry missing on disk: {name}")
        elif sha256(fp) != want:
            problems.append(f"manifest hash mismatch: {name}")
    return problems


def receiver_measurement(d: Path) -> dict:
    """Frozen statistic: dispersion of the FIRST summary window lying wholly inside the
    impaired phase. Window = (previous summary, this summary], per linuxptp clock.c."""
    log = (d / "slave.log").read_text(errors="replace")
    ev = (d / "events.log").read_text(errors="replace")
    am = APPLY_MONO.search(ev)
    apply_mono = float(am.group(2)) if am else None
    apply_utc = am.group(1) if am else None
    fm = FAULT.search(log)
    fault_t = float(fm.group(1)) if fm else None
    receiver_master = bool(MASTER.search(log))
    s = [(float(a), int(b), int(c)) for a, b, c in SERVO.findall(log)]
    windows = []
    for i, (t, dly, disp) in enumerate(s):
        prev = s[i - 1][0] if i > 0 else None
        why = []
        if prev is None:
            why.append("first summary after process start; window start unrecorded")
        if apply_mono is None:
            why.append("no phase apply event found")
        elif prev is not None and prev < apply_mono:
            why.append("window begins before the phase apply time (mixed phase)")
        elif prev is not None and abs(prev - apply_mono) < 0.001:
            why.append("window start within the 1 ms alignment precision of the apply instant")
        if fault_t is not None and t >= fault_t:
            why.append("window ends at or after a fault transition")
        windows.append({"summary_time": t, "window_start": prev,
                        "window_duration_s": (round(t - prev, 6) if prev else None),
                        "path_delay_ns": dly, "path_delay_dispersion_ns": disp,
                        "wholly_in_phase": not why, "invalid_reasons": why})
    valid = [w for w in windows if w["wholly_in_phase"]]
    unknown = None
    if receiver_master:
        unknown = "receiver entered MASTER on a port"
    elif not valid:
        unknown = "no wholly-in-phase measurement window"
    elif len(valid) < MIN_VALID_WINDOWS:
        unknown = f"insufficient_valid_windows ({len(valid)} < {MIN_VALID_WINDOWS})"
    first = valid[0] if valid else None
    label = "UNKNOWN" if unknown else (
        "RECEIVER_DISPERSION_ABOVE_BOUNDARY"
        if first["path_delay_dispersion_ns"] >= BOUNDARY_NS
        else "RECEIVER_DISPERSION_BELOW_BOUNDARY")
    return {"apply_monotonic_s": apply_mono, "apply_utc": apply_utc,
            "fault_transition_time": fault_t, "receiver_entered_master": receiver_master,
            "summary_windows": windows, "valid_window_count": len(valid),
            "first_valid_window": first,
            "first_valid_window_dispersion_ns": (first["path_delay_dispersion_ns"] if first else None),
            "receiver_unknown_reason": unknown, "receiver_label": label}


def detector_decision(d: Path, apply_utc: str | None) -> dict:
    """Frozen rule: a detection_trigger counts only if its packet timestamp (pcap epoch) is later
    than the apply instant. The apply instant in epoch terms comes from events.log utc, resolution
    1 s; within +/- 1 s the run is UNKNOWN. No duration is computed across timebases."""
    trigs = []
    dl = d / "decision_log.jsonl"
    if dl.is_file():
        for line in dl.read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event") == "detection_trigger":
                trigs.append(r)
    if apply_utc is None:
        return {"triggers": len(trigs), "detector_outcome": "UNKNOWN",
                "detector_unknown_reason": "no apply event; trigger causality unresolvable",
                "trigger_packet_ts": [t.get("packet_ts") for t in trigs]}
    a = utc_to_epoch(apply_utc)
    after = [t for t in trigs if t.get("packet_ts") is not None and t["packet_ts"] > a + TRIGGER_AMBIGUITY_S]
    ambiguous = [t for t in trigs if t.get("packet_ts") is not None
                 and abs(t["packet_ts"] - a) <= TRIGGER_AMBIGUITY_S]
    if after:
        outcome, reason = "TRIGGER", None
    elif ambiguous:
        outcome, reason = "UNKNOWN", "trigger_timing_unresolvable"
    else:
        outcome, reason = "NO_TRIGGER", None
    return {"triggers": len(trigs), "triggers_after_apply": len(after),
            "triggers_ambiguous": len(ambiguous), "detector_outcome": outcome,
            "detector_unknown_reason": reason,
            "trigger_packet_ts": [t.get("packet_ts") for t in trigs],
            "apply_epoch_from_utc": a}


def wilson(k: int, n: int, z: float = 1.959963985) -> dict:
    if n == 0:
        return {"point": None, "low": None, "high": None, "n": 0}
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"point": round(p, 4), "low": round(max(0.0, c - h), 4),
            "high": round(min(1.0, c + h), 4), "n": n, "k": k}


def main() -> None:
    if not RUNS.is_dir():
        print(json.dumps({"error": "s15_runs does not exist; no S15 data to evaluate"}, indent=2))
        return
    rows = []
    for d in sorted(x for x in RUNS.iterdir() if x.is_dir()):
        m = COND.search(d.name)
        row = {"run": d.name, "condition": m.group(1) if m else "UNPARSED"}
        problems = seal_check(d)
        row["integrity_problems"] = problems
        rm = receiver_measurement(d)
        row.update({k: rm[k] for k in ("apply_monotonic_s", "apply_utc", "valid_window_count",
                                       "first_valid_window_dispersion_ns", "receiver_entered_master",
                                       "receiver_unknown_reason", "receiver_label")})
        row["summary_windows"] = rm["summary_windows"]
        row.update(detector_decision(d, rm["apply_utc"]))
        if problems:
            row["receiver_label"] = "UNKNOWN"
            row["receiver_unknown_reason"] = "; ".join(problems)
        row["counted_in_2x2"] = (row["receiver_label"] != "UNKNOWN"
                                 and row["detector_outcome"] in ("TRIGGER", "NO_TRIGGER"))
        rows.append(row)

    counted = [r for r in rows if r["counted_in_2x2"]]
    above = [r for r in counted if r["receiver_label"] == "RECEIVER_DISPERSION_ABOVE_BOUNDARY"]
    below = [r for r in counted if r["receiver_label"] == "RECEIVER_DISPERSION_BELOW_BOUNDARY"]
    tp = sum(1 for r in above if r["detector_outcome"] == "TRIGGER")
    fn = len(above) - tp
    fp = sum(1 for r in below if r["detector_outcome"] == "TRIGGER")
    tn = len(below) - fp

    per_cond = {}
    for r in rows:
        c = per_cond.setdefault(r["condition"], {
            "runs": 0, "counted": 0, "above_boundary": 0, "below_boundary": 0,
            "unknown": 0, "triggered_among_counted": 0, "dispersions_ns": []})
        c["runs"] += 1
        if r["first_valid_window_dispersion_ns"] is not None:
            c["dispersions_ns"].append(r["first_valid_window_dispersion_ns"])
        if r["counted_in_2x2"]:
            c["counted"] += 1
            c["above_boundary" if r["receiver_label"].endswith("ABOVE_BOUNDARY") else "below_boundary"] += 1
            if r["detector_outcome"] == "TRIGGER":
                c["triggered_among_counted"] += 1
        else:
            c["unknown"] += 1
    for c in per_cond.values():
        c["dispersions_ns"].sort()
        c["trigger_rate_among_counted"] = wilson(c["triggered_among_counted"], c["counted"])
        c["above_boundary_rate_among_counted"] = wilson(c["above_boundary"], c["counted"])

    unknowns = [{"run": r["run"], "condition": r["condition"],
                 "receiver_unknown_reason": r["receiver_unknown_reason"],
                 "detector_unknown_reason": r["detector_unknown_reason"],
                 "valid_window_count": r["valid_window_count"],
                 "first_valid_window_dispersion_ns": r["first_valid_window_dispersion_ns"]}
                for r in rows if not r["counted_in_2x2"]]

    sens = wilson(tp, len(above))
    spec = wilson(tn, len(below))
    maj = max(len(above), len(below)) / len(counted) if counted else None
    agree = (tp + tn) / len(counted) if counted else None

    branch = None
    if counted:
        if not above or not below:
            branch = ("only one receiver label class was produced; sensitivity or specificity is "
                      "undefined and agreement cannot be assessed")
        elif (sens["point"] >= 0.8 and spec["point"] >= 0.8
              and sens["low"] > 0.5 and spec["low"] > 0.5):
            branch = ("the detector's run-level decision agrees with the receiver-side dispersion "
                      "boundary across the sweep in this testbed")
        elif sens["point"] >= 0.8 and spec["point"] < 0.8:
            branch = ("the detector triggers at jitter levels the receiver measurement places below "
                      "the boundary; see per-condition divergence")
        elif sens["point"] < 0.8 and spec["point"] >= 0.8:
            branch = ("the detector fails to trigger on above-boundary runs; see per-condition "
                      "failures")
        elif maj is not None and agree is not None and agree <= maj:
            branch = "the detector decision is not shown to track the receiver-side measurement"
        else:
            branch = ("agreement is partial: neither sensitivity nor specificity reaches the "
                      "pre-specified 0.8 with a lower bound above 0.5")
    if len(unknowns) > len(rows) / 2:
        branch = ("most runs are UNKNOWN: the measurement plan failed. Reported as a failed "
                  "validation attempt. No other label source is substituted.")

    out = {
        "schema_version": "s15-independent-validation-evaluation-v1",
        "protocol": PROTOCOL.name,
        "protocol_sha256": sha256(PROTOCOL) if PROTOCOL.is_file() else None,
        "evaluator_sha256": sha256(Path(__file__)),
        "runs_found": len(rows),
        "runs_counted": len(counted),
        "runs_unknown": len(unknowns),
        "two_by_two": {
            "above_boundary_and_trigger": tp, "above_boundary_and_no_trigger": fn,
            "below_boundary_and_trigger": fp, "below_boundary_and_no_trigger": tn,
            "note": ("Rows are the receiver-side dispersion label, columns the detector outcome. "
                     "Below-boundary-and-trigger is a trigger-without-above-boundary, and "
                     "above-boundary-and-no-trigger a missed-above-boundary. Neither is a false "
                     "positive or a miss with respect to harm; harm is not measured here.")},
        "sensitivity_trigger_rate_among_above_boundary": sens,
        "specificity_no_trigger_rate_among_below_boundary": spec,
        "overall_agreement": (round(agree, 4) if agree is not None else None),
        "majority_label_rate": (round(maj, 4) if maj is not None else None),
        "prespecified_branch_reached": branch,
        "per_condition": per_cond,
        "unknown_runs": unknowns,
        "every_run_dispersion_ns": {r["run"]: r["first_valid_window_dispersion_ns"] for r in rows},
        "every_run_valid_window_count": {r["run"]: r["valid_window_count"] for r in rows},
        "boundary_ns": BOUNDARY_NS,
        "not_claimed": ("Agreement between a packet-level decision and a receiver-side path-delay "
                        "dispersion measurement in a software testbed. NOT harm, service impact, "
                        "physical timing accuracy, attack detection, recovery benefit, or O-RAN "
                        "conformance. Harmfulness remains UNKNOWN."),
        "runs": rows,
    }
    (HERE / "S15_INDEPENDENT_VALIDATION_EVALUATION.json").write_text(json.dumps(out, indent=2) + "\n")
    brief = {k: out[k] for k in ("runs_found", "runs_counted", "runs_unknown", "two_by_two",
                                 "sensitivity_trigger_rate_among_above_boundary",
                                 "specificity_no_trigger_rate_among_below_boundary",
                                 "overall_agreement", "majority_label_rate",
                                 "prespecified_branch_reached")}
    brief["per_condition"] = {k: {kk: vv for kk, vv in v.items() if kk != "dispersions_ns"}
                              for k, v in out["per_condition"].items()}
    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
