"""Smoke-run acceptance check required by S15_INDEPENDENT_VALIDATION_PROTOCOL_V2.json.

Verifies the six protocol checks on one isolated run. Exits non-zero if any check fails, so the
batch cannot be started from a failed smoke run. Reports findings; it does not fix anything.
"""
from __future__ import annotations
import importlib.util, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ev", HERE / "evaluate_s15.py")
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)


def main() -> int:
    d = Path(sys.argv[1]).resolve()
    # Guard: never write into a sealed evidence directory. The smoke check writes a result file,
    # and adding a file to a sealed run is a post-seal modification of raw evidence.
    if (d / "source_manifest.sha256").is_file() and d.parent.name != "s15_smoke":
        print(json.dumps({"error": "refusing to run: target is a sealed run directory outside "
                                   "s15_smoke/. The smoke check writes SMOKE_CHECK.json and must "
                                   "never add a file to sealed evidence.",
                          "target": str(d)}, indent=2))
        return 2
    checks = []

    def chk(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    confs = sorted(d.glob("*.conf"))
    missing_fr = [c.name for c in confs if "free_running 1" not in c.read_text(errors="replace")]
    chk("every written ptp4l config sets free_running 1",
        confs and not missing_fr,
        {"configs": [c.name for c in confs], "without_free_running": missing_fr})

    envt = (d / "run_environment.txt").read_text(errors="replace") if (d / "run_environment.txt").is_file() else ""
    chk("run environment records that host clock adjustment is disabled",
        "host_clock_adjustment=disabled_by_free_running_1" in envt,
        {"run_environment_present": bool(envt)})

    log = (d / "slave.log").read_text(errors="replace") if (d / "slave.log").is_file() else ""
    servo = ev.SERVO.findall(log)
    chk("receiver produced servo summary lines", len(servo) >= 2,
        {"servo_summary_lines": len(servo)})

    rm = ev.receiver_measurement(d)
    chk(f"at least {ev.MIN_VALID_WINDOWS} wholly-in-phase summary windows",
        rm["valid_window_count"] >= ev.MIN_VALID_WINDOWS,
        {"valid_window_count": rm["valid_window_count"],
         "first_valid_window_dispersion_ns": rm["first_valid_window_dispersion_ns"],
         "apply_monotonic_s": rm["apply_monotonic_s"],
         "window_durations_s": [w["window_duration_s"] for w in rm["summary_windows"]]})

    wx = d / "writer_exit_status.tsv"
    bad = []
    if wx.is_file():
        for line in wx.read_text(errors="replace").splitlines():
            f = line.split("\t")
            if len(f) >= 2 and f[1].strip() not in ("0", "status", "exit_status"):
                bad.append(line.strip())
    chk("all writers closed gracefully", wx.is_file() and not bad,
        {"writer_exit_status_present": wx.is_file(), "nonzero_lines": bad})

    problems = ev.seal_check(d)
    chk("run is sealed and every manifest hash verifies", not problems, {"problems": problems})

    det = ev.detector_decision(d, rm["apply_utc"])
    out = {"smoke_run": str(d), "checks": checks,
           "all_passed": all(c["pass"] for c in checks),
           "observed_receiver_label": rm["receiver_label"],
           "observed_detector_outcome": det["detector_outcome"],
           "note": ("This run is a configuration and integrity check only. Its label and detector "
                    "outcome are NOT evidence for or against the hypothesis and are excluded from "
                    "S15 estimation. It is stored under s15_smoke/, which evaluate_s15.py never reads.")}
    (d / "SMOKE_CHECK.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0 if out["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
