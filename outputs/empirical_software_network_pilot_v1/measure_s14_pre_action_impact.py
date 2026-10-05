"""Task 2: independent, receiver-measured, pre-action software impact.

Source: ptp4l's own periodic servo summary in slave.log, field `delay <mean> +/- <dispersion>`,
nanoseconds. This is computed by the RECEIVER from its own Sync/Delay_Req exchange. It is not
produced by, and does not depend on, the packet detector.

Timing basis: the servo lines and any port-state transition appear in the SAME ptp4l log, so
"before the action" is decided entirely inside one timebase. No mapping between ptp4l, capture
and detector clocks is assumed or required.

The action arm is EXCLUDED from pre-action impact: its later sample straddles a commanded
link-down, so it cannot evidence the condition before the action.
"""
from __future__ import annotations
import json, re, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "s14_runs"
COND = {"base": "baseline_clean", "bng": "benign_delay_jitter",
        "jnoact": "jitter_fault_no_action", "asf": "authorized_source_failover",
        "jact": "jitter_fault_action"}
NETEM = {"baseline_clean": "none",
         "benign_delay_jitter": "delay 100us 20us distribution normal",
         "jitter_fault_no_action": "delay 100us 200us distribution normal",
         "jitter_fault_action": "delay 100us 200us distribution normal",
         "authorized_source_failover": "none (clean master A termination)"}
SERVO = re.compile(r"ptp4l\[([\d.]+)\]:.*?\bdelay (\d+) \+/- (\d+)")
FAULT = re.compile(r"ptp4l\[([\d.]+)\]: port (\d+): \w+ to FAULTY")


def parse(d: Path) -> dict:
    log = (d / "slave.log").read_text(encoding="utf-8", errors="replace")
    servo = [{"ptp4l_log_time": float(a), "path_delay_ns": int(b), "path_delay_dispersion_ns": int(c)}
             for a, b, c in SERVO.findall(log)]
    fm = FAULT.search(log)
    fault_t = float(fm.group(1)) if fm else None
    for s in servo:
        s["strictly_before_any_fault"] = (fault_t is None) or (s["ptp4l_log_time"] < fault_t)
    key = re.sub(r"\d+$", "", d.name.replace("20260913_s14_", ""))
    return {"run": d.name, "condition": COND.get(key, key), "netem": NETEM.get(COND.get(key, key)),
            "fault_transition_ptp4l_time": fault_t, "servo_samples": servo}


def stats(v):
    v = sorted(v)
    return {"n": len(v), "min": v[0], "median": st.median(v), "max": v[-1]} if v else {"n": 0}


def main() -> None:
    runs = [parse(d) for d in sorted(RUNS.iterdir()) if d.is_dir()]
    # The impaired-window sample is the LAST servo line of the run.
    by_cond: dict[str, list] = {}
    for r in runs:
        if not r["servo_samples"]:
            continue
        last = r["servo_samples"][-1]
        r["impaired_window_sample"] = last
        r["usable_as_pre_action_impact"] = bool(last["strictly_before_any_fault"])
        by_cond.setdefault(r["condition"], []).append(r)

    summary = {}
    for cond, rs in sorted(by_cond.items()):
        usable = [r for r in rs if r["usable_as_pre_action_impact"]]
        summary[cond] = {
            "netem": NETEM.get(cond),
            "runs": len(rs),
            "runs_usable_for_pre_action_impact": len(usable),
            "excluded_reason": (None if len(usable) == len(rs)
                                else "later servo sample straddles the commanded link-down; "
                                     "cannot evidence the condition before the action"),
            "path_delay_ns": stats([r["impaired_window_sample"]["path_delay_ns"] for r in usable]),
            "path_delay_dispersion_ns": stats(
                [r["impaired_window_sample"]["path_delay_dispersion_ns"] for r in usable]),
        }

    def rng(c, f):
        s = summary[c][f]
        return (s["min"], s["max"]) if s["n"] else None

    sep = {}
    pairs = [("baseline_clean", "benign_delay_jitter"),
             ("baseline_clean", "jitter_fault_no_action"),
             ("benign_delay_jitter", "jitter_fault_no_action"),
             ("baseline_clean", "authorized_source_failover")]
    for a, b in pairs:
        for f in ("path_delay_ns", "path_delay_dispersion_ns"):
            ra, rb = rng(a, f), rng(b, f)
            if not ra or not rb:
                continue
            lo, hi = (ra, rb) if ra[1] < rb[0] else ((rb, ra) if rb[1] < ra[0] else (None, None))
            sep[f"{a}__vs__{b}::{f}"] = {
                "range_a": ra, "range_b": rb,
                "separable_without_overlap": lo is not None,
                "margin_ns": (hi[0] - lo[1]) if lo else None,
            }

    out = {
        "schema_version": "s14-pre-action-impact-v1",
        "measurement": ("ptp4l receiver-reported mean path delay and its dispersion, nanoseconds, "
                        "from the receiver's own servo summary line."),
        "independence": ("Computed by ptp4l from its own Sync/Delay_Req exchange. Not produced by "
                         "and not dependent on the packet detector."),
        "timing_basis": ("Servo lines and port-state transitions share the ptp4l log timebase, so "
                         "pre-action ordering needs no cross-clock mapping. No numeric comparison "
                         "is made against capture or detector clocks."),
        "per_condition": summary,
        "pairwise_separation": sep,
        "runs": runs,
        "interpretation_rules": [
            "These are receiver-measured protocol observations. They are NOT harm labels.",
            "Harmfulness remains UNKNOWN: no service requirement has been specified against which "
            "a path-delay dispersion could be judged harmful.",
            "The action arm contributes no pre-action impact evidence and is excluded from it.",
            "Under free_running with a shared host clock this is a protocol-level estimate over "
            "software timestamps, not a calibrated physical timing measurement.",
            "One impaired-window sample per run; ptp4l emits this summary only periodically.",
        ],
    }
    (HERE / "S14_PRE_ACTION_IMPACT.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"per_condition": summary, "pairwise_separation": sep}, indent=2))


if __name__ == "__main__":
    main()
