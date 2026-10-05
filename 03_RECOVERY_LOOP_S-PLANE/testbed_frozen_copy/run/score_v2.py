#!/usr/bin/env python3
"""Score one run dir with frozen v2; write decision_v2.json. Hash-gates both rules."""
import sys, os, json, csv, hashlib, importlib.util
SP="/opt/sptb"
def load(n):
    s=importlib.util.spec_from_file_location(n,f"{SP}/run/{n}.py")
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
frz=json.load(open(f"{SP}/FROZEN.json")); frz2=json.load(open(f"{SP}/FROZEN_V2.json"))
h1=hashlib.sha256(open(f"{SP}/run/decision_rule.py","rb").read()).hexdigest()
h2=hashlib.sha256(open(f"{SP}/run/decision_rule_v2.py","rb").read()).hexdigest()
assert h1==frz["artifacts"]["run/decision_rule.py"]["sha256"], "frozen base hash mismatch"
assert h2==frz2["sha256"], "frozen v2 hash mismatch"
v2=load("decision_rule_v2")
run_dir=sys.argv[1]
ctx=json.load(open(os.path.join(run_dir,"context.json")))
cands=[f for f in os.listdir(run_dir) if f.endswith("dn.deep.csv")]
if not cands:
    print("no deep csv"); sys.exit(2)
deep=os.path.join(run_dir,cands[0])
v,hint,why,ev=v2.decide_v2(deep,ctx)
out=dict(scenario=ctx.get("scenario"), truth_class=ctx.get("class"), truth_fault=ctx.get("fault_id"),
         verdict=v, fault_hint=hint, reasons=why, rule="decision_rule_v2 (frozen e32eb65b)")
json.dump(out, open(os.path.join(run_dir,"decision_v2.json"),"w"), indent=2)
print(f"{os.path.basename(run_dir)}: v2={v} {hint}")
