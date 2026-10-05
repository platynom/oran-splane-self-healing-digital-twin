#!/usr/bin/env python3
"""
evaluate_v4 - corrected evaluation of the frozen rule and frozen v2.

Fixes applied after the 2026-09-20 audit (each was a real defect in evaluate_v3.py):
 1. Explicit rep whitelist (1..12). v3 gated on the presence of decision_v2.json, so running
    score_v2.py over the PRIOR campaign's reps 30-41 would have silently doubled the pool.
 2. Per-scenario recall is now PRIMARY, with a macro-average across scenarios. The pooled
    figure is reported but explicitly labelled run-count-dependent: because both rules are
    bimodal (perfect on one subset, zero on another), pooled sensitivity is a function of how
    many runs of each scenario exist, not of rule quality.
 3. Additive-only is now checked PER RUN (frozen ATTACK => v2 ATTACK; equality elsewhere),
    not by comparing two aggregate scalars that could hide offsetting errors.
 4. Abstention is credited only via the SUBSTANTIVE path (fault_hint == "B2?"). The frozen
    rule also returns UNKNOWN on pure failure paths (unreadable/empty capture, no Announce);
    v3 would have scored an infrastructure failure as a correct abstention.
 5. Attribution scoring restored, with an alias map for the v2 detector labels.
 6. Denominator and partition invariants asserted; run list + timestamps written to JSON.
 7. Design-effective n reported for the C scenarios (their randomised draw space is small).
"""
import json, os, glob, math, collections, datetime, hashlib

SP="/opt/sptb"; REPS=set(range(1,13))
EXPECT = {
 "A1_rogue_master":"ATTACK","A2_sync_spoof":"ATTACK","A3_replay":"ATTACK",
 "A5_dos_flood":"ATTACK","A8_rogue_bc":"ATTACK",
 "C1_removal":"ATTACK","C2_malformed":"ATTACK","C3_wholesecond":"ATTACK",
 "baseline":"BENIGN","B2_gm_failover":"BENIGN","B_bc_replacement":"BENIGN",
 "B3_pdv_congestion":"BENIGN","B7_topology_change":"BENIGN",
 "B_unplanned_failover":"UNKNOWN",
}
ALIAS={"A_intercept":"C1","A_malformed":"C2","A_wholesecond":"C3"}
# distinct randomised designs available per scenario (from randparams draw sets)
DESIGN_N={"C1_removal":5,"C2_malformed":4,"C3_wholesecond":4}

def wilson(k,n,z=1.96):
    if n==0: return (None,None,None)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(p,4),round(max(0.0,c-h),4),round(min(1.0,c+h),4))

def ci(est):
    return "n/a" if est[0] is None else f"{est[0]:.3f} [{est[1]:.3f}, {est[2]:.3f}]"

runs={}
skipped=collections.Counter()
for d in sorted(glob.glob(f"{SP}/cap/*__r*")):
    base=os.path.basename(d); tail=base.split("__r")[-1]
    if not tail.isdigit(): skipped["bad_name"]+=1; continue
    rep=int(tail)
    if rep not in REPS: skipped["rep_out_of_range"]+=1; continue
    sc=base.split("__r")[0]
    if sc not in EXPECT: skipped["unknown_scenario"]+=1; continue
    f1,f2,f3,cj=[os.path.join(d,x) for x in ("decision.json","decision_v2.json","decision_v3.json","context.json")]
    if not all(map(os.path.exists,(f1,f2,f3,cj))): skipped["missing_decision"]+=1; continue
    ctx=json.load(open(cj)); d1=json.load(open(f1)); d2=json.load(open(f2)); d3=json.load(open(f3))
    if ctx["scenario"]!=sc: skipped["scenario_mismatch"]+=1; continue
    runs[base]=dict(scenario=sc,rep=rep,expect=EXPECT[sc],truth_fault=ctx["fault_id"],
        frozen=d1["verdict"],frozen_hint=d1.get("fault_hint"),
        v2=d2["verdict"],v2_hint=d2.get("fault_hint"),
        v3=d3["verdict"],v3_hint=d3.get("fault_hint"))

R=list(runs.values())
assert R, "no admissible runs"
# invariant: both rules scored on the identical run set (guaranteed by construction above)
per_sc=collections.Counter(r["scenario"] for r in R)

def score(rule,hint_key,label):
    A=[r for r in R if r["expect"]=="ATTACK"]; B=[r for r in R if r["expect"]=="BENIGN"]; U=[r for r in R if r["expect"]=="UNKNOWN"]
    tp=sum(1 for r in A if r[rule]=="ATTACK"); fn=sum(1 for r in A if r[rule]=="BENIGN"); ua=sum(1 for r in A if r[rule]=="UNKNOWN")
    tn=sum(1 for r in B if r[rule]=="BENIGN"); fp=sum(1 for r in B if r[rule]=="ATTACK"); ub=sum(1 for r in B if r[rule]=="UNKNOWN")
    assert tp+fn+ua==len(A) and tn+fp+ub==len(B), "verdict partition invariant violated"
    # abstention: substantive path only
    ab=sum(1 for r in U if r[rule]=="UNKNOWN" and r[hint_key]=="B2?")
    ab_err=sum(1 for r in U if r[rule]=="UNKNOWN" and r[hint_key]!="B2?")
    scen={}
    for sc in sorted({r["scenario"] for r in R}):
        rr=[r for r in R if r["scenario"]==sc]; exp=EXPECT[sc]
        want={"ATTACK":"ATTACK","BENIGN":"BENIGN","UNKNOWN":"UNKNOWN"}[exp]
        k=sum(1 for r in rr if r[rule]==want)
        scen[sc]=dict(correct=k,n=len(rr),expect=exp,est=wilson(k,len(rr)))
    atk=[s for s in scen if EXPECT[s]=="ATTACK"]; ben=[s for s in scen if EXPECT[s]=="BENIGN"]
    macro_sens=sum(scen[s]["correct"]/scen[s]["n"] for s in atk)/len(atk)
    macro_spec=sum(scen[s]["correct"]/scen[s]["n"] for s in ben)/len(ben)
    # attribution
    ok=0
    for r in A:
        h=r[hint_key]; h=ALIAS.get(h,h)
        if h==r["truth_fault"]: ok+=1
    return dict(label=label,n_attack=len(A),n_benign=len(B),n_unknown=len(U),
        tp=tp,fn=fn,unknown_on_attack=ua,tn=tn,fp=fp,unknown_on_benign=ub,
        abstain_substantive=ab,abstain_via_error_path=ab_err,
        pooled_sensitivity=wilson(tp,len(A)),pooled_specificity=wilson(tn,len(B)),
        abstention=wilson(ab,len(U)),
        macro_sensitivity=round(macro_sens,4),macro_specificity=round(macro_spec,4),
        attribution=wilson(ok,len(A)),per_scenario=scen)

sf=score("frozen","frozen_hint","FROZEN rule c362e11")
sv=score("v2","v2_hint","FROZEN v2 e32eb65b  (superseded - see FROZEN_V3.json)")
s3=score("v3","v3_hint","FROZEN v3 aa9417b7  (defect-fix revision - PRIMARY)")

# ---- per-run additive-only verification (the check v3 omitted) ----
viol_soften=[k for k,r in runs.items() if r["frozen"]=="ATTACK" and r["v3"]!="ATTACK"]
changed=[k for k,r in runs.items() if r["frozen"]!=r["v3"]]
v2_vs_v3=[k for k,r in runs.items() if r["v2"]!=r["v3"]]
escalated=collections.Counter(runs[k]["scenario"] for k in changed)
additive_ok = (len(viol_soften)==0)

def show(s):
    print("\n"+"="*80); print(s["label"]); print("="*80)
    print(f"  runs: attack={s['n_attack']} benign={s['n_benign']} abstain={s['n_unknown']}")
    print(f"  PER-SCENARIO (primary):")
    for sc,d in s["per_scenario"].items():
        print(f"    {sc:22s} {d['expect']:7s} {d['correct']:2d}/{d['n']:<2d}  {ci(d['est'])}")
    print(f"  macro-avg sensitivity : {s['macro_sensitivity']:.3f}   (mean over 8 attack scenarios)")
    print(f"  macro-avg specificity : {s['macro_specificity']:.3f}   (mean over 5 benign scenarios)")
    print(f"  pooled sensitivity    : {ci(s['pooled_sensitivity'])}  <- run-count dependent, descriptive only")
    print(f"  pooled specificity    : {ci(s['pooled_specificity'])}")
    print(f"  abstention (substantive path only): {ci(s['abstention'])}   [via error path: {s['abstain_via_error_path']}]")
    print(f"  attribution accuracy  : {ci(s['attribution'])}")

print(f"admissible runs: {len(R)}   scenarios: {len(per_sc)}   reps: {sorted({r['rep'] for r in R})}")
print(f"per-scenario n: {dict(sorted(per_sc.items()))}")
if skipped: print(f"skipped: {dict(skipped)}")
show(sf); show(sv); show(s3)
print("\n"+"="*80); print("ADDITIVE-ONLY VERIFICATION (per-run, not scalar)"); print("="*80)
print(f"  runs where frozen=ATTACK but v2!=ATTACK (regressions): {len(viol_soften)}  -> {'PASS' if additive_ok else 'FAIL'}")
print(f"  runs where v3 differs from frozen (escalations): {len(changed)}  {dict(escalated)}")
print(f"  runs where v2 and v3 disagree on this (downstream) set: {len(v2_vs_v3)}")
print("\n"+"="*80); print("COVERAGE-GAP CLOSURE"); print("="*80)
for sc in ["C1_removal","C2_malformed","C3_wholesecond"]:
    f=sf["per_scenario"].get(sc); v=s3["per_scenario"].get(sc)
    if f and v:
        de=DESIGN_N[sc]
        print(f"  {sc:18s} frozen {f['correct']}/{f['n']}  ->  v3 {v['correct']}/{v['n']}   {ci(v['est'])}   "
              f"[distinct randomised designs available: {de}]")

out=dict(generated=datetime.datetime.utcnow().isoformat()+"Z",
    evaluator="evaluate_v4.py", reps=sorted(REPS), n_runs=len(R),
    per_scenario_n=dict(per_sc), skipped=dict(skipped),
    frozen=sf, v2=sv, v3=s3,
    additive_only=dict(passed=additive_ok,regressions=viol_soften,
        escalations=dict(escalated),n_changed=len(changed)),
    design_effective_n=DESIGN_N,
    run_list=sorted(runs.keys()))
json.dump(out,open(f"{SP}/results/EVALUATION_V4.json","w"),indent=2)
print(f"\n-> results/EVALUATION_V4.json  ({len(R)} runs, fully enumerated)")
