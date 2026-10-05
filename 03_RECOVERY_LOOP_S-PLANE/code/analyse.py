#!/usr/bin/env python3
"""Score the recovery-loop campaign. Usage: analyse.py <cap_dir> <out_json> [rep list]
Outcome measurement uses ONLY the passive observer (pmc -d 24 PARENT_DATA_SET + PORT_DATA_SET
on every RU, every 0.5 s), which runs identically in both arms. Loop logs are used only for
detection latency, actions and verification records."""
import glob, json, os, statistics, sys

CAP, OUT = sys.argv[1], sys.argv[2]
REPS = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else None
ALLOW_GM = {"020000fffe00000a", "020000fffe00000b"}
LEGIT_PARENT = {"020000fffe000001", "020000fffe0000c5"}    # primary BC, standby BC
PRIMARY_NODES = ("ru1", "ru2")       # RU3 shares the attacker's port in A2/A3/A5/C2/C3 and is the bounced RU in B7
WINDOW_S = 40.0                      # T0 .. T0+40 s
TAIL_S = 5.0                         # "restored at end" = healthy throughout the final 5 s

def ident(s): return s.split("-")[0].replace(".", "") if s else ""

def healthy(r, legit):
    return (r.get("portState") in ("SLAVE", "UNCALIBRATED")
            and ident(r.get("parentPortIdentity")) in legit
            and ident(r.get("grandmasterIdentity")) in ALLOW_GM)

def score_run(d):
    ctx = json.load(open(f"{d}/context.json")); tl = json.load(open(f"{d}/timeline.json"))
    t0 = tl["t0_mono"]
    legit = set(LEGIT_PARENT)
    if ctx.get("expected_bc_identity_secondary"): legit.add(ctx["expected_bc_identity_secondary"])
    obs = [json.loads(l) for l in open(f"{d}/observer.jsonl")]
    # rounds: group the three per-node samples of one poll cycle
    rounds, cur = [], {}
    for r in obs:
        if r["node"] in cur:
            rounds.append(cur); cur = {}
        cur[r["node"]] = r
    if cur: rounds.append(cur)
    def t_of(rd): return min(x["t"] for x in rd.values()) - t0
    pre = [rd for rd in rounds if -10.0 <= t_of(rd) < 0]
    post = [rd for rd in rounds if 0 <= t_of(rd) <= WINDOW_S]
    def ok(rd, nodes=PRIMARY_NODES): return all(n in rd and healthy(rd[n], legit) for n in nodes)
    pre_ok = sum(ok(rd) for rd in pre) / max(1, len(pre))
    unhealthy_s = 0.0
    for a, b in zip(post, post[1:]):
        if not ok(a): unhealthy_s += t_of(b) - t_of(a)
    tail = [rd for rd in post if t_of(rd) >= WINDOW_S - TAIL_S]
    restored_end = bool(tail) and all(ok(rd) for rd in tail)
    first_bad = next((t_of(rd) for rd in post if not ok(rd)), None)
    outage = None
    if first_bad is not None and restored_end:
        last_bad = max(t_of(rd) for rd in post if not ok(rd))
        nxt = [t_of(rd) for rd in post if t_of(rd) > last_bad]
        outage = round((nxt[0] if nxt else last_bad) - first_bad, 2)
    own = {"ru1": "020000fffe00000c", "ru2": "020000fffe00000d", "ru3": "020000fffe00000e"}
    def foreign_parent(rd):    # an RU following a parent that is neither provisioned nor itself
        return any(n in rd and ident(rd[n].get("parentPortIdentity")) not in legit | {"", own[n]}
                   for n in PRIMARY_NODES)
    rogue_parent_s = 0.0
    for a, b in zip(post, post[1:]):
        if foreign_parent(a): rogue_parent_s += t_of(b) - t_of(a)
    ru3_unhealthy_s = 0.0
    for a, b in zip(post, post[1:]):
        if not ok(a, ("ru3",)): ru3_unhealthy_s += t_of(b) - t_of(a)
    # loop records
    acts, verifies, esc, first_attack, first_action = [], [], [], None, None
    for l in open(f"{d}/loop.jsonl"):
        e = json.loads(l); te = round(e["t_mono"] - t0, 2)
        if e["kind"] == "eval" and e.get("verdict") == "ATTACK" and te >= 0 and first_attack is None:
            first_attack = te
        if e["kind"] in ("act", "would_act"):
            acts.append(dict(t=te, action=e["action"], target=e["target"], kind=e["kind"]))
            if first_action is None and te >= 0: first_action = te
        if e["kind"] == "verify": verifies.append(dict(t=te, ok=e["ok"], action=e["action"]))
        if e["kind"] == "escalate": esc.append(dict(t=te, reason=e["reason"][:140]))
        if e["kind"] == "rollback": acts.append(dict(t=te, action="ROLLBACK", target=e["target"], kind="rollback"))
    pre_t0_actions = [a for a in acts if a["t"] < 0]
    return dict(run=os.path.basename(d), scenario=ctx["scenario"], cls=ctx["class"], rep=ctx["rep"], arm=ctx["arm"],
                pre_t0_service_ok_fraction=round(pre_ok, 3), unhealthy_s=round(unhealthy_s, 2),
                rogue_parent_s=round(rogue_parent_s, 2), ru3_unhealthy_s=round(ru3_unhealthy_s, 2),
                first_unhealthy_s=first_bad, outage_s=outage, restored_at_end=restored_end,
                first_attack_verdict_s=first_attack, first_action_s=first_action,
                actions=acts, verifies=verifies, escalations=esc, pre_t0_actions=pre_t0_actions)

runs = []
for d in sorted(glob.glob(f"{CAP}/*__r*__*")):
    if not os.path.exists(f"{d}/timeline.json"): continue
    r = score_run(d)
    if REPS and r["rep"] not in REPS: continue
    runs.append(r)

summary = {}
for sc in sorted({r["scenario"] for r in runs}):
    s = {}
    for arm in ("control", "loop"):
        rr = [r for r in runs if r["scenario"] == sc and r["arm"] == arm]
        if not rr: continue
        disruptive = [a for r in rr for a in r["actions"] if a["action"] in ("ISOLATE_PTP_AT_PORT", "ACTIVATE_STANDBY_BC")]
        s[arm] = dict(n=len(rr),
                      unhealthy_s_median=statistics.median(r["unhealthy_s"] for r in rr),
                      unhealthy_s_each=[r["unhealthy_s"] for r in rr],
                      restored_at_end=sum(r["restored_at_end"] for r in rr),
                      outage_s_each=[r["outage_s"] for r in rr],
                      rogue_parent_s_each=[r["rogue_parent_s"] for r in rr],
                      ru3_unhealthy_s_each=[r["ru3_unhealthy_s"] for r in rr],
                      first_attack_verdict_s_each=[r["first_attack_verdict_s"] for r in rr],
                      first_action_s_each=[r["first_action_s"] for r in rr],
                      disruptive_actions=len(disruptive),
                      action_kinds=sorted({f'{a["action"]}:{a["target"]}' for a in disruptive}),
                      verify_ok=sum(v["ok"] for r in rr for v in r["verifies"]),
                      verify_total=sum(len(r["verifies"]) for r in rr),
                      rollbacks=sum(1 for r in rr for a in r["actions"] if a["action"] == "ROLLBACK"),
                      runs_with_escalation=sum(1 for r in rr if r["escalations"]),
                      pre_t0_actions=sum(len(r["pre_t0_actions"]) for r in rr),
                      pre_t0_service_ok_min=min(r["pre_t0_service_ok_fraction"] for r in rr))
    summary[sc] = s
json.dump(dict(runs=runs, summary=summary), open(OUT, "w"), indent=1)
for sc, s in summary.items():
    line = f"{sc:24s}"
    for arm in ("control", "loop"):
        if arm in s:
            a = s[arm]
            line += (f" | {arm}: n={a['n']} unhealthy_med={a['unhealthy_s_median']:5.1f}s restored={a['restored_at_end']}/{a['n']}"
                     f" acts={a['disruptive_actions']} vfy={a['verify_ok']}/{a['verify_total']}")
    print(line)
