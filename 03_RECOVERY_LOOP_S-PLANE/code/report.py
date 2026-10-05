#!/usr/bin/env python3
"""Evaluate the pre-registered hypotheses from analyse.py output and write the results tables.
Usage: report.py <analysis.json> <out.md>  (prints the same text)."""
import json, math, statistics, sys

A = json.load(open(sys.argv[1])); runs = A["runs"]
ATT = ["A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "C1_removal", "C2_malformed", "C3_wholesecond"]
BEN = ["baseline", "B2_gm_failover", "B3_pdv_congestion", "B7_topology_change", "B_bc_replacement"]
AMB = ["B_unplanned_failover"]
DISRUPT = ("ISOLATE_PTP_AT_PORT", "ACTIVATE_STANDBY_BC")

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(max(0, c - h), 3), round(min(1, c + h), 3)

# apparatus validity: pre-T0 service must be up (>= 0.8) in BOTH arms of a pair, else the pair is excluded
pairs = {}
for r in runs: pairs.setdefault((r["scenario"], r["rep"]), {})[r["arm"]] = r
excluded = sorted(k for k, v in pairs.items()
                  if len(v) < 2 or any(x["pre_t0_service_ok_fraction"] < 0.8 for x in v.values()))
valid = [r for r in runs if (r["scenario"], r["rep"]) not in excluded]
def sel(sc, arm): return [r for r in valid if r["scenario"] == sc and r["arm"] == arm]
def executed(r): return [a for a in r["actions"] if a["kind"] == "act" and a["action"] in DISRUPT]
def med(x):
    x = [v for v in x if v is not None]
    return round(statistics.median(x), 2) if x else None

L = []
P = L.append
P("| Scenario | Arm | n | Unhealthy s (median; each) | Restored at end | Following a rogue parent, s (each) | Detection s after T0 (each) | First action s (each) | Executed disruptive actions | Verified | RU3 unhealthy s (each) |")
P("|---|---|---:|---|---:|---|---|---|---|---:|---|")
for sc in ATT + BEN + AMB:
    for arm in ("control", "loop"):
        rr = sel(sc, arm)
        if not rr: continue
        ex = [a for r in rr for a in executed(r)]
        kinds = sorted({f"{a['action'].split('_')[0]}:{a['target']}" for a in ex})
        vok = sum(v["ok"] for r in rr for v in r["verifies"]); vt = sum(len(r["verifies"]) for r in rr)
        P(f"| {sc} | {arm} | {len(rr)} | {med([r['unhealthy_s'] for r in rr])}; {[r['unhealthy_s'] for r in rr]} | "
          f"{sum(r['restored_at_end'] for r in rr)}/{len(rr)} | {[r['rogue_parent_s'] for r in rr]} | "
          f"{[r['first_attack_verdict_s'] for r in rr]} | {[r['first_action_s'] for r in rr]} | "
          f"{len(ex)} {', '.join(kinds)} | {vok}/{vt} | {[r['ru3_unhealthy_s'] for r in rr]} |")
table = "\n".join(L)

H = []
# H1
h1_ok = True; h1_lines = []
for sc in ATT:
    c, l = sel(sc, "control"), sel(sc, "loop")
    if not c or not l: h1_ok = False; h1_lines.append(f"{sc}: missing arm"); continue
    mc, ml = med([r["unhealthy_s"] for r in c]), med([r["unhealthy_s"] for r in l])
    rest = sum(r["restored_at_end"] for r in l)
    cond = rest == len(l) and ml <= mc and (mc < 5 or ml <= 0.5 * mc)
    h1_ok &= cond
    h1_lines.append(f"{sc}: loop restored {rest}/{len(l)}; median unhealthy loop {ml} s vs control {mc} s -> {'PASS' if cond else 'FAIL'}")
H.append(("H1 restoration", h1_ok, h1_lines))
# H2
h2_ok = True; h2_lines = []
for sc in ATT:
    l = sel(sc, "loop")
    want = "ACTIVATE_STANDBY_BC" if sc == "C1_removal" else "ISOLATE_PTP_AT_PORT"
    k = 0
    for r in l:
        ex = [a for a in executed(r) if a["action"] == want]
        vok = [v for v in r["verifies"] if v["action"] == want and v["ok"]]
        k += bool(ex and vok)
    cond = k >= 4 if len(l) == 5 else k >= math.ceil(0.8 * len(l))
    h2_ok &= cond
    h2_lines.append(f"{sc}: {want} executed and verified in {k}/{len(l)} -> {'PASS' if cond else 'FAIL'}")
H.append(("H2 containment", h2_ok, h2_lines))
# H3
bl = [r for sc in BEN for r in sel(sc, "loop")]
nb = sum(len(executed(r)) for r in bl)
lo, hi = wilson(sum(1 for r in bl if executed(r)), len(bl))
H.append(("H3 no harm on benign", nb == 0, [f"{nb} executed disruptive actions in {len(bl)} benign loop runs; "
                                            f"runs with any disruptive action {sum(1 for r in bl if executed(r))}/{len(bl)} "
                                            f"(Wilson 95% [{lo}, {hi}])"]))
# H4
al = sel("B_unplanned_failover", "loop")
na = sum(len(executed(r)) for r in al); ne = sum(1 for r in al if r["escalations"])
H.append(("H4 honest abstention", na == 0 and ne >= (4 if len(al) == 5 else math.ceil(0.8 * len(al))),
          [f"{na} disruptive actions; escalation logged in {ne}/{len(al)} runs"]))
# control integrity
cr = [r for r in valid if r["arm"] == "control"]
nc = sum(1 for r in cr for a in r["actions"] if a["kind"] == "act")
H.append(("Control integrity", nc == 0, [f"{nc} executed actions across {len(cr)} control runs (would_act logged: "
                                        f"{sum(1 for r in cr for a in r['actions'] if a['kind']=='would_act')})"]))

out = ["## Hypotheses (pre-registered)", ""]
for name, ok, lines in H:
    out.append(f"**{name}: {'PASS' if ok else 'FAIL'}**")
    out += [f"- {x}" for x in lines]; out.append("")
out += [f"Excluded pairs (pre-T0 service < 0.8 in either arm): {excluded if excluded else 'none'}", "",
        f"Runs scored: {len(valid)} of {len(runs)}", "", "## Per-scenario outcomes", "", table, ""]
txt = "\n".join(out)
open(sys.argv[2], "w").write(txt); print(txt)
