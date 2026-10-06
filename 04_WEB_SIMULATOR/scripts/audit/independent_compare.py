"""Compare rendered DOM values with values derived from raw run files; exit 1 on any mismatch."""
import json, os, sys
AUDIT = os.environ.get("AUDIT_DIR", "/tmp/sim-audit")
E = json.load(open(os.path.join(AUDIT, "expected.json")))["states"]
R = {(r["run"], r["t"]): r for r in json.load(open(os.path.join(AUDIT, "rendered.json")))["states"]}
checks, bad = 0, []
def cmp(what, got, want):
    global checks
    checks += 1
    if got != want: bad.append(f"{what}: rendered {got!r} expected {want!r}")
for e in E:
    r = R[(e["run"], e["t"])]; k = f"{e['run']} t={e['t']}"
    cmp(f"{k} time", r["time"], f"T0 {'+' if e['t'] >= 0 else '−'} {abs(e['t']):.1f} s")
    for n in ("ru1", "ru2", "ru3"):
        want = e["nodes"].get(n, {})
        cmp(f"{k} {n} portState", r["rows"][n]["portState"], want.get("portState") or "–")
        cmp(f"{k} {n} parentPort", r["rows"][n]["parentTitle"] or None, want.get("parentPort"))
    v = e["verdict"]
    cmp(f"{k} rule verdict", ("Rule: " + v) in r["badge"] if v else "Rule:" not in r["badge"], True)
    if v and e["hint"]: cmp(f"{k} rule hint", e["hint"] in r["badge"], True)
    truncated = r["logCount"] >= 60
    for kind in ("act", "would_act", "verify", "escalate"):
        got = sorted(t for kd, t in r["items"] if kd == kind)
        if truncated and len(got) < len(e[kind]): bad.append(f"{k} {kind}: log truncated at 60 items (not compared)"); continue
        cmp(f"{k} log {kind} times", got, e[kind])
    for st, want in e["stages"].items():
        s = r["stages"][st]
        cmp(f"{k} stage {st} lit", s["lit"], "true" if want else "false")
        if want: cmp(f"{k} stage {st} time", f"T0 + {want} s" in s["text"], True)
        cmp(f"{k} stage {st} never", s["never"], "false" if e["stages_in_run"][st] else "true")
print(f"independent check: {len(E)} states, {checks} values compared, {len(bad)} mismatches")
for b in bad: print("MISMATCH", b)
json.dump({"seed": json.load(open(os.path.join(AUDIT, "expected.json")))['seed'], "states": [f"{e['run']} t={e['t']}" for e in E], "values": checks, "mismatches": bad}, open(os.path.join(AUDIT, "independent_result.json"), "w"), indent=1)
sys.exit(1 if bad else 0)
