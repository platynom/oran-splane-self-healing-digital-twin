#!/usr/bin/env python3
"""Re-run the FROZEN decision rule (decision_rule_v3.decide_v2 over the unchanged base rule) on the recorded
brDN capture of every control run, at the run's recorded evaluation ticks, for several window lengths.

Why: the sandbox lets a learner change the loop's evidence window. Instead of guessing how the rule would
react, this computes the frozen rule's actual verdicts on the recorded packets for W = 2, 4, 6, 8, 10 s.

Validation: for W = 6 s (the pre-registered value) the recomputed verdicts are compared with the verdicts the
loop logged live in loop.jsonl; the agreement is written to provenance and shown in the app.

Differences from the live loop, stated in the output:
  * the live loop captured each frame at its ingress bridge port; this uses tcpdump on the brDN bridge
    interface (frames delivered to the bridge). The rule itself does not use the ingress port.
  * frame times come from the capture (CLOCK_REALTIME), aligned to CLOCK_MONOTONIC with the per-run anchor
    computed by extract.py (validated to <= 1 ms).

Only control runs are used: they contain no intervention, so the verdict sequence is the fault as observed.
The frozen rule files are sha256-checked before use.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, importlib.util, io, json, os, struct, sys, tarfile, tempfile, time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=os.path.abspath(os.path.join(HERE, "..", "..")))
ap.add_argument("--out", default=os.path.abspath(os.path.join(HERE, "..", "data", "derived")))
ap.add_argument("--windows", default="2,4,6,8,10")
ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
A = ap.parse_args()
WINDOWS = [float(x) for x in A.windows.split(",")]
TB = os.path.join(A.repo, "03_RECOVERY_LOOP_S-PLANE", "testbed_frozen_copy")
FROZEN = {"run/decision_rule.py": "c362e11072344161437aaae33b2902caf9bca57dfc33f653a9c2184edae8a985",
          "run/decision_rule_v3.py": "aa9417b701cc09dcf242a814cc136ce2acd561269389b7553618205997b7f330"}
for rel, h in FROZEN.items():
    got = hashlib.sha256(open(os.path.join(TB, rel), "rb").read()).hexdigest()
    if got != h:
        sys.exit(f"REFUSING: {rel} sha256 {got} != frozen {h}")
PROV = json.load(open(os.path.join(A.repo, "03_RECOVERY_LOOP_S-PLANE", "code", "provisioning.json")))

def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

RULE = EXT = None
def init():
    global RULE, EXT
    RULE = load("decision_rule_v3", os.path.join(TB, "run", "decision_rule_v3.py"))
    EXT = load("ptp_deep_extract", os.path.join(TB, "ptp_deep_extract.py"))

def frames(raw):
    f = io.BytesIO(raw); f.read(24)
    while True:
        h = f.read(16)
        if len(h) < 16: break
        s, us, il, _ = struct.unpack("<IIII", h)
        d = f.read(il)
        if len(d) < 14: continue
        et = struct.unpack(">H", d[12:14])[0]
        if et == 0x8100 and len(d) >= 18: et = struct.unpack(">H", d[16:18])[0]
        if et != 0x88F7: continue
        yield s + us / 1e6, d

def rule_ctx(sc, maint):
    ctx = {k: PROV[k] for k in ("gm_allowlist", "provisioned_backup_gm", "expected_bc_identity",
                                 "expected_client_identities", "expected_steps_removed_at_ru")}
    ctx["maintenance_window_open"] = maint
    ctx["leap_window_open"] = False
    if sc == "B_bc_replacement":
        ctx["expected_bc_identity_secondary"] = "020000fffe0000b1"
    return ctx

def work(job):
    run_id, pcap_bytes, anchor, ticks, sc, maint = job
    recs = []
    for ts, d in frames(gzip.decompress(pcap_bytes)):
        try:
            r = EXT.parse_frame(int(ts * 1e9), d)
        except Exception:
            r = None
        if r is not None:
            recs.append((ts - anchor, r))
    ctx = rule_ctx(sc, maint)
    out = {}
    fd, path = tempfile.mkstemp(suffix=".deep.csv"); os.close(fd)
    try:
        for W in WINDOWS:
            seq = []
            lo = 0
            for t in ticks:
                win = [r for (tr, r) in recs if t - W <= tr <= t]
                if not win:
                    seq.append([t, "NO_EVIDENCE", None]); continue
                with open(path, "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=EXT.COLUMNS, extrasaction="ignore")
                    w.writeheader()
                    for r in win: w.writerow(r)
                v, hint, why, _ = RULE.decide_v2(path, ctx)
                seq.append([t, v, hint])
            out[str(int(W))] = seq
    finally:
        os.unlink(path)
    return run_id, out

def main():
    t_start = time.time()
    runs = json.load(gzip.open(os.path.join(A.out, "recovery_runs.json.gz"), "rt"))
    ctrl = {r["id"]: r for r in runs if r["arm"] == "control"}
    tf = tarfile.open(os.path.join(A.repo, "03_RECOVERY_LOOP_S-PLANE", "results", "recovery_eval_runs_r13-r17.tgz"), "r:gz")
    pcaps = {}
    for m in tf:
        parts = m.name.lstrip("./").split("/")
        if len(parts) == 2 and parts[1] == "dn.pcap.gz" and parts[0] in ctrl:
            pcaps[parts[0]] = tf.extractfile(m).read()
    jobs = []
    for rid, r in ctrl.items():
        ticks = [e["t"] for e in r["events"] if e["kind"] == "eval"]
        anchor = r["pcapAnchor"]["offset_s"]
        jobs.append((rid, pcaps[rid], anchor, ticks, r["scenario"], r["maintenanceWindowOpen"]))
    results = {}
    with Pool(A.jobs, initializer=init) as pool:
        for i, (rid, out) in enumerate(pool.imap_unordered(work, jobs), 1):
            results[rid] = out
            print(f"[{i}/{len(jobs)}] {rid} ({time.time() - t_start:.0f}s)", flush=True)
    # validation against the verdicts logged live (W = 6 s)
    agree = total = 0
    mism = []
    for rid, r in ctrl.items():
        live = [(e["t"], e.get("verdict") or "NO_EVIDENCE") for e in r["events"] if e["kind"] == "eval"]
        rec = results[rid]["6"]
        for (t, v), (t2, v2, _) in zip(live, rec):
            total += 1
            if v == v2: agree += 1
            else: mism.append(f"{rid} t={t:+.2f}: live {v} vs recomputed {v2}")
    summary = dict(windows=WINDOWS, runs=len(results), ticks_compared_w6=total, agree_w6=agree,
                   agreement_w6=round(agree / max(1, total), 4), mismatches_sample=mism[:40],
                   method="frozen decision_rule_v3.decide_v2 on brDN capture frames in [t-W, t] at the live evaluation ticks")
    with gzip.open(os.path.join(A.out, "rule_windows.json.gz"), "wt") as f:
        json.dump(dict(summary=summary, runs=results), f, separators=(",", ":"))
    print(json.dumps({k: v for k, v in summary.items() if k != "mismatches_sample"}, indent=1))
    print("\n".join(mism[:15]))

if __name__ == "__main__":
    main()
