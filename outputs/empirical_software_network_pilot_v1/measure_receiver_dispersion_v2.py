"""v2 receiver-dispersion measurement with verified semantics and verified phase alignment.

SUPERSEDES measure_s14_pre_action_impact.py (v1), which selected "the last servo sample" without
establishing its measurement interval. v1 is retained as superseded exploratory work.

MEASUREMENT SEMANTICS (established from linuxptp source, clock.c):
  clock_stats_update() prints when the accumulated offset sample count reaches max_count, then
  clock_stats_display() calls stats_reset() on offset, freq and delay. Delay values accumulate from
  every path-delay update between printed summaries. Therefore a printed summary aggregates exactly
  the interval (previous_summary_time, this_summary_time]. The print trigger is SAMPLE-COUNT driven,
  not time driven. Units are nanoseconds (ptp4l(8)).

PHASE ALIGNMENT (established empirically, evidence recorded in the output):
  ptp4l's printed log time and the runner/detector monotonic clock are the same basis. Verified on
  five independent anchor pairs: the commanded link-down recorded by the detector process and the
  resulting ptp4l FAULTY transition agree to <= 1 ms across runs spanning ~1000 s.

VALIDITY RULE: a window counts only if it lies WHOLLY inside the intended phase, i.e.
  previous_summary_time >= phase_apply_time  AND  this_summary_time < any fault-transition time.
The first summary after process start is always invalid: its window begins at an unrecorded time.

STATISTIC: the FIRST valid wholly-in-phase window. Not a maximum over windows, so the value does not
depend on how many windows a run happens to contain.

This is a receiver-computed measurement CHANNEL. It is not statistically independent of the packet
observations: both derive from the same traffic. It is a separate computation by a different program.
"""
from __future__ import annotations
import json, re, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVO = re.compile(r"ptp4l\[([\d.]+)\]:.*?\bdelay (\d+) \+/- (\d+)")
FAULT = re.compile(r"ptp4l\[([\d.]+)\]: port (\d+): \w+ to FAULTY")
MASTER = re.compile(r"port \d+: \w+ to MASTER")
APPLY = re.compile(r"event=phase2_\S*.*?monotonic_s=([\d.]+)")
BOUNDARY_NS = 29000


def anchors(run_dirs) -> dict:
    """Evidence that ptp4l log time and the detector process clock share a basis."""
    pairs = []
    for d in run_dirs:
        log = (d / "slave.log").read_text(errors="replace")
        fm = FAULT.search(log)
        dl = d / "decision_log.jsonl"
        if not fm or not dl.is_file():
            continue
        for line in dl.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["event"] == "action_execution_result":
                pairs.append({"run": d.name, "ptp4l_fault_time": float(fm.group(1)),
                              "detector_monotonic": r["monotonic_s"],
                              "difference_s": round(float(fm.group(1)) - r["monotonic_s"], 6)})
                break
    diffs = [abs(p["difference_s"]) for p in pairs]
    return {"anchor_pairs": pairs, "n": len(pairs),
            "max_abs_difference_s": max(diffs) if diffs else None,
            "conclusion": ("ptp4l log time and the detector monotonic clock share a basis to within "
                           "the stated maximum difference" if diffs else "NOT ESTABLISHED"),
            "caveat": ("The anchor is a command and its direct effect, so the difference also "
                       "contains the true command-to-fault latency. It bounds the clock offset from "
                       "above; it does not prove a zero offset.")}


def measure(d: Path) -> dict:
    log = (d / "slave.log").read_text(errors="replace")
    ev = (d / "events.log").read_text(errors="replace")
    am = APPLY.search(ev)
    apply_t = float(am.group(1)) if am else None
    fm = FAULT.search(log)
    fault_t = float(fm.group(1)) if fm else None
    receiver_master = bool(MASTER.search(log))
    s = [(float(a), int(b), int(c)) for a, b, c in SERVO.findall(log)]
    windows = []
    for i, (t, dly, disp) in enumerate(s):
        prev = s[i - 1][0] if i > 0 else None
        reasons = []
        if prev is None:
            reasons.append("first summary after process start; window start unrecorded")
        if apply_t is None:
            reasons.append("no phase apply event found")
        elif prev is not None and prev < apply_t:
            reasons.append("window begins before the phase apply time (mixed phase)")
        if fault_t is not None and t >= fault_t:
            reasons.append("window ends at or after a fault transition (action effect)")
        windows.append({"summary_time": t, "window_start": prev,
                        "window_duration_s": (round(t - prev, 6) if prev else None),
                        "path_delay_ns": dly, "path_delay_dispersion_ns": disp,
                        "wholly_in_phase": not reasons, "invalid_reasons": reasons})
    valid = [w for w in windows if w["wholly_in_phase"]]
    unknown = None
    if receiver_master:
        unknown = "receiver entered MASTER on a port"
    elif not valid:
        unknown = "no wholly-in-phase measurement window"
    first = valid[0] if valid else None
    label = "UNKNOWN" if unknown else (
        "RECEIVER_DISPERSION_ABOVE_BOUNDARY" if first["path_delay_dispersion_ns"] >= BOUNDARY_NS
        else "RECEIVER_DISPERSION_BELOW_BOUNDARY")
    key = re.sub(r"\d+$", "", d.name.split("_s14_")[-1].split("_s15_")[-1])
    return {"run": d.name, "condition_key": key, "phase_apply_time": apply_t,
            "fault_transition_time": fault_t, "receiver_entered_master": receiver_master,
            "summary_windows": windows, "valid_window_count": len(valid),
            "statistic_first_valid_window": first, "unknown_reason": unknown,
            "receiver_label": label}


def main() -> None:
    runs_root = HERE / "s14_runs"
    dirs = sorted(x for x in runs_root.iterdir() if x.is_dir())
    rows = [measure(d) for d in dirs]
    by = {}
    for r in rows:
        by.setdefault(r["condition_key"], []).append(r)
    summary = {}
    for k, rs in sorted(by.items()):
        ok = [r for r in rs if r["unknown_reason"] is None]
        disp = sorted(r["statistic_first_valid_window"]["path_delay_dispersion_ns"] for r in ok)
        dly = sorted(r["statistic_first_valid_window"]["path_delay_ns"] for r in ok)
        summary[k] = {
            "runs": len(rs), "usable": len(ok),
            "unknown_reasons": [r["unknown_reason"] for r in rs if r["unknown_reason"]],
            "dispersion_ns": ({"min": disp[0], "median": st.median(disp), "max": disp[-1]} if disp else None),
            "path_delay_ns": ({"min": dly[0], "median": st.median(dly), "max": dly[-1]} if dly else None),
            "labels": {l: sum(1 for r in ok if r["receiver_label"] == l)
                       for l in ("RECEIVER_DISPERSION_ABOVE_BOUNDARY", "RECEIVER_DISPERSION_BELOW_BOUNDARY")},
        }
    out = {
        "schema_version": "receiver-dispersion-measurement-v2",
        "supersedes": "measure_s14_pre_action_impact.py / S14_PRE_ACTION_IMPACT.json (v1, exploratory)",
        "measurement_semantics_source": ("linuxptp clock.c: clock_stats_update prints on sample count "
            "reaching max_count; clock_stats_display then calls stats_reset on offset, freq and delay. "
            "Window = (previous summary, this summary]. Units nanoseconds per ptp4l(8)."),
        "documentation_source": "ptp4l(8) summary_interval: power of two in seconds, default 0 (1 second), units nanoseconds and ppb",
        "clock_alignment_evidence": anchors(dirs),
        "validity_rule": ("window start >= phase apply time AND window end < any fault transition; "
                          "the first summary after process start is always invalid"),
        "statistic": "dispersion of the FIRST valid wholly-in-phase window",
        "boundary_ns": BOUNDARY_NS,
        "label_semantics": ("RECEIVER_DISPERSION_ABOVE_BOUNDARY / BELOW_BOUNDARY are names for a "
                            "measurement category only. They are NOT harm labels, NOT fault labels "
                            "and NOT service-impact labels. Harmfulness remains UNKNOWN."),
        "independence_caveat": ("A separate receiver-computed channel, produced by ptp4l rather than "
                                "the detector. NOT statistically independent of the packet "
                                "observations: both arise from the same traffic."),
        "per_condition": summary,
        "runs": rows,
    }
    (HERE / "RECEIVER_DISPERSION_S14_V2.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"clock_alignment": {k: v for k, v in out["clock_alignment_evidence"].items() if k != "anchor_pairs"},
                      "per_condition": summary}, indent=2))


if __name__ == "__main__":
    main()
