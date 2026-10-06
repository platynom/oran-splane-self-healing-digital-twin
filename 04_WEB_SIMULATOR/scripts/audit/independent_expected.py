"""Independent expected state from RAW run files (observer.jsonl, loop.jsonl, timeline.json). Imports nothing from the app.

  python3 scripts/audit/independent_expected.py [stratified]     -> $AUDIT_DIR/expected.json
Extracts the run archive into $AUDIT_DIR/raw on first use. Seed 20261006 (random) / 20261007 (stratified).
"""
import json, os, random, subprocess, sys
AUDIT = os.environ.get("AUDIT_DIR", "/tmp/sim-audit")
RAW = os.path.join(AUDIT, "raw")
TGZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "03_RECOVERY_LOOP_S-PLANE", "results", "recovery_eval_runs_r13-r17.tgz")
if not os.path.isdir(RAW):
    os.makedirs(RAW)
    subprocess.run(["tar", "xzf", TGZ, "-C", RAW, "--wildcards", "*/loop.jsonl", "*/observer.jsonl", "*/timeline.json"], check=True)
SEED = 20261006
rng = random.Random(SEED)
runs = sorted(d for d in os.listdir(RAW) if os.path.isdir(os.path.join(RAW, d)))
assert len(runs) == 140, len(runs)
picks = []
STRAT = len(sys.argv) > 1 and sys.argv[1] == "stratified"
if not STRAT:
    for _ in range(10):
        rid = rng.choice(runs)
        t = round(rng.uniform(-5, 40), 1)
        picks.append((rid, t))
else:
    # supplementary: runs whose loop.jsonl has an act / would_act / escalate, t drawn after the first such record
    rng = random.Random(SEED + 1)
    def first_action(rid):
        t0 = json.load(open(f"{RAW}/{rid}/timeline.json"))["t0_mono"]
        for l in open(f"{RAW}/{rid}/loop.jsonl"):
            d = json.loads(l)
            if d["kind"] in ("act", "would_act", "escalate"):
                return d["t_mono"] - t0
    cand = [r for r in runs if first_action(r) is not None]
    for rid in rng.sample(cand, 10):
        picks.append((rid, round(rng.uniform(first_action(rid) + 0.2, 40), 1)))
out = []
for rid, t in picks:
    sc, r, arm = rid.rsplit("__", 2)
    tl = json.load(open(f"{RAW}/{rid}/timeline.json"))
    t0 = tl["t0_mono"]
    rel = lambda m: round(m - t0, 3)
    nodes = {}
    for line in open(f"{RAW}/{rid}/observer.jsonl"):
        d = json.loads(line)
        if d.get("node") not in ("ru1", "ru2", "ru3"):
            continue
        if d["t"] - t0 <= t + 1e-9:
            nodes[d["node"]] = {"portState": d.get("portState"), "parentPort": d.get("parentPortIdentity")}
    ev = [json.loads(l) for l in open(f"{RAW}/{rid}/loop.jsonl")]
    evals = [e for e in ev if e["kind"] == "eval" and rel(e["t_mono"]) <= t + 1e-9]
    last = evals[-1] if evals else None
    shown = lambda k: sorted(f"{rel(e['t_mono']):.3f}" for e in ev if e["kind"] == k and rel(e["t_mono"]) <= t + 1e-9)
    first = lambda pred: next((rel(e["t_mono"]) for e in ev if pred(e)), None)
    stages = {
        "detect": first(lambda e: e["kind"] == "eval" and e.get("verdict") == "ATTACK" and rel(e["t_mono"]) >= 0),
        "localise": first(lambda e: e["kind"] == "eval" and e.get("violations") and rel(e["t_mono"]) >= 0),
        "decide": first(lambda e: e["kind"] in ("act", "would_act", "escalate")),
        "act": first(lambda e: e["kind"] == "act" and e.get("executed") is True),
        "verify": first(lambda e: e["kind"] == "verify"),
        "rollback": first(lambda e: e["kind"] == "rollback"),
    }
    out.append({"run": rid, "scenario": sc, "rep": int(r[1:]), "arm": arm, "t": t, "nodes": nodes,
                "verdict": last.get("verdict") if last else None, "hint": last.get("hint") if last else None,
                "act": shown("act"), "would_act": shown("would_act"), "verify": shown("verify"), "escalate": shown("escalate"),
                "stages": {k: (f"{v:.3f}" if v is not None and v <= t + 1e-9 else None) for k, v in stages.items()},
                "stages_in_run": {k: v is not None for k, v in stages.items()}})
json.dump({"seed": SEED + (1 if STRAT else 0), "mode": "stratified" if STRAT else "random", "states": out}, open(os.path.join(AUDIT, "expected.json"), "w"), indent=1)
print("\n".join(f"{o['run']} t={o['t']}" for o in out))
