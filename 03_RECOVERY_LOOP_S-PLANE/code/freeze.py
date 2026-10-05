#!/usr/bin/env python3
"""freeze.py --write : record sha256 of every file the evaluation depends on -> FROZEN_RL.json
   freeze.py --verify: exit 1 if any differs."""
import hashlib, json, sys, datetime, os
B = "/opt/sptb"
FILES = ["recovery/recovery_loop.py", "recovery/run_one.py", "recovery/observer.py", "recovery/analyse.py",
         "recovery/provisioning.json", "recovery/PREREGISTRATION.md", "recovery/campaign.sh", "recovery/devrun.sh",
         "run/decision_rule.py", "run/decision_rule_v3.py", "ptp_deep_extract.py", "run/topology.sh", "run/start.sh",
         "run/stop.sh", "run/clean_all.sh", "run/randparams.py", "run/inject.py", "run/flood.py",
         "run/inject_malformed.py", "run/inject_wholesecond.py", "run/bg_traffic.py", "cfg/g87251.base",
         "cfg/gma.cfg", "cfg/gmb.cfg", "cfg/bc.cfg", "cfg/ru1.cfg", "cfg/ru2.cfg", "cfg/ru3.cfg"]
h = {f: hashlib.sha256(open(os.path.join(B, f), "rb").read()).hexdigest() for f in FILES}
P = os.path.join(B, "recovery/FROZEN_RL.json")
if sys.argv[1] == "--write":
    json.dump(dict(frozen_at=datetime.datetime.utcnow().isoformat() + "Z", sha256=h,
                   note="Evaluation replicates 13-17. Development replicate 101 ran before this freeze."), open(P, "w"), indent=2)
    print("frozen", len(h))
else:
    f = json.load(open(P))["sha256"]
    bad = [k for k in f if f[k] != h.get(k)]
    if bad: print("MISMATCH", bad); sys.exit(1)
