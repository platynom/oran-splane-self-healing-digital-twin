#!/usr/bin/env python3
"""Extract the additional datasets the 3D explorer needs into data/derived/extra.json.gz.

  * 168-run detector campaign: per-run evidence (decision.json 'evidence' block) plus message-type and sender counts
    computed from each run's deep CSV (one row per PTP frame). The CSV row count is checked against the evidence's
    n_packets; any difference is reported, never hidden.
  * 13 Sep pilot: S11 closed-loop trials (10) and S15 independent validation (30), with the summary blocks.
  * B6 two-laptop oscillator measurement: run 1 and run 2 analysis outputs (raw per-sample CSVs are NOT in the repo).

Nothing here approximates absent data. Row-count checks are written into extra.json.gz under "checks" and re-verified by
scripts/ingest.ts and the unit tests.
"""
from __future__ import annotations
import collections, csv, gzip, hashlib, io, json, os, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.abspath(os.path.join(HERE, "..", "data", "derived", "extra.json.gz"))
CF = os.path.join(REPO, "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/gap_coverage_2026-09-20/corrected_final")
PILOT = os.path.join(REPO, "outputs/empirical_software_network_pilot_v1")
B6 = os.path.join(REPO, "outputs/B6_two_machine_2026-10-02")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

checks = []
def check(name, got, want):
    ok = got == want
    checks.append(dict(name=name, got=got, want=want, ok=ok))
    if not ok:
        print(f"CHECK FAILED {name}: got {got}, want {want}", file=sys.stderr)

# ---------------------------------------------------------------- campaign
tgz = os.path.join(CF, "splane_campaign_CORRECTED_2026-09-20.tgz")
want_sha = open(tgz + ".sha256").read().split()[0]
check("campaign archive sha256 equals published", sha(tgz), want_sha)
runs = {}
with tarfile.open(tgz, "r:gz") as t:
    for m in t:
        if not m.isfile() or not m.name.startswith("./cap/"):
            continue
        parts = m.name.split("/")
        if len(parts) != 4:
            continue
        run, fn = parts[2], parts[3]
        rn = int(run.split("__r")[-1]) if run.split("__r")[-1].isdigit() else -1
        if not (1 <= rn <= 12):
            continue
        r = runs.setdefault(run, {})
        if fn == "decision.json":
            r["decision"] = json.load(t.extractfile(m))
        elif fn == "decision_v3.json":
            r["v3"] = json.load(t.extractfile(m))
        elif fn.endswith(".deep.csv"):
            mt, src, rows = collections.Counter(), collections.Counter(), 0
            rd = csv.DictReader(io.TextIOWrapper(t.extractfile(m), encoding="utf-8", newline=""))
            for row in rd:
                rows += 1
                mt[row.get("message_type") or "unparsed"] += 1
                src[(row.get("eth_src") or "").replace(":", "")] += 1
            r["csv"] = dict(file=fn, rows=rows, msg=dict(mt), src=dict(src))
        elif fn == "context.json":
            r["context"] = json.load(t.extractfile(m))
campaign = []
mism = []
for run in sorted(runs):
    r = runs[run]
    ev = r["decision"].get("evidence", {})
    c = r.get("csv")
    if c is None:
        mism.append(f"{run}: no deep csv")
        continue
    if ev.get("n_packets") != c["rows"]:
        mism.append(f"{run}: evidence n_packets {ev.get('n_packets')} != csv rows {c['rows']}")
    campaign.append(dict(runId=run, csvRows=c["rows"], nPacketsClaimed=ev.get("n_packets"), nAnnounce=ev.get("n_announce"),
                         captureSpanS=ev.get("capture_span_s"), msgTypeCounts=c["msg"], senderCounts=c["src"],
                         gmIdentities=ev.get("gm_identities", {}), evidence=ev, reasons=r["v3"].get("reasons", []),
                         description=(r.get("context") or {}).get("description")))
check("campaign runs with evidence", len(campaign), 168)
check("campaign runs whose deep-CSV rows equal evidence.n_packets", len(campaign) - len(mism), 168)
if mism:
    print("\n".join(mism[:10]), file=sys.stderr)

# ---------------------------------------------------------------- pilot S11 / S15
s11 = json.load(open(os.path.join(PILOT, "S11_CLOSED_LOOP_EVALUATION.json")))
s15 = json.load(open(os.path.join(PILOT, "S15_INDEPENDENT_VALIDATION_EVALUATION.json")))
pilot = []
for arm, d in s11["runs"].items():
    for rid, r in d.items():
        pilot.append(dict(id=rid, milestone="S11", group=arm, label="action" if arm == "action" else "no_action",
                          triggered=r.get("detector_triggered"), actionExecuted=r.get("action_executed"),
                          outcome=r.get("active_port_moved_to_clean_segment"), data=r))
for r in s15["runs"]:
    pilot.append(dict(id=r["run"], milestone="S15", group=r["condition"], label=r.get("receiver_label"),
                      triggered=None, actionExecuted=None, outcome=None, data=r))
# S15 trigger flags live in the per-condition block only as counts; keep the per-run record verbatim.
check("S11 pilot runs", sum(1 for p in pilot if p["milestone"] == "S11"), 10)
check("S15 pilot runs", sum(1 for p in pilot if p["milestone"] == "S15"), 30)
tb = s15["two_by_two"]
check("S15 2x2 cells sum to 30", tb["above_boundary_and_trigger"] + tb["above_boundary_and_no_trigger"] + tb["below_boundary_and_trigger"] + tb["below_boundary_and_no_trigger"], 30)
check("S15 above-boundary n = 15", tb["above_boundary_and_trigger"] + tb["above_boundary_and_no_trigger"], 15)
check("S15 below-boundary n = 15", tb["below_boundary_and_trigger"] + tb["below_boundary_and_no_trigger"], 15)
check("S15 labels: 15 above, 15 below", (sum(1 for r in s15["runs"] if r["receiver_label"].endswith("ABOVE_BOUNDARY")), sum(1 for r in s15["runs"] if r["receiver_label"].endswith("BELOW_BOUNDARY"))), (15, 15))
check("S11 action 5/5, no-action 0/5 eligible outcome", (s11["primary_outcome_summary"]["action"]["k"], s11["primary_outcome_summary"]["no_action"]["k"]), (5, 0))
pilot_summary = [
    dict(id="S11", status="PRESPECIFIED_BRANCH_MET", statement=s11["prespecified_statement"], limits=s11["limits"],
         data={k: s11[k] for k in ("primary_outcome_summary", "detector_trigger_rate", "prespecified_branch_selected", "action_command_failures")},
         sourcePath="outputs/empirical_software_network_pilot_v1/S11_CLOSED_LOOP_EVALUATION.json"),
    dict(id="S15", status="NOT_ESTABLISHED", statement=("Independent validation S15 not established: trigger rate above boundary 14/15 (0.9333), "
         "no-trigger rate below boundary 8/15 (0.5333), below the frozen 0.8 criterion."), limits=[s15["not_claimed"]],
         data={k: s15[k] for k in ("two_by_two", "sensitivity_trigger_rate_among_above_boundary", "specificity_no_trigger_rate_among_below_boundary",
                                    "overall_agreement", "boundary_ns", "per_condition", "prespecified_branch_reached")},
         sourcePath="outputs/empirical_software_network_pilot_v1/START_HERE_FINAL.md; S15_INDEPENDENT_VALIDATION_EVALUATION.json"),
]
check("S15 sensitivity 14/15 and specificity 8/15 as in START_HERE_FINAL.md",
      (s15["sensitivity_trigger_rate_among_above_boundary"]["k"], s15["sensitivity_trigger_rate_among_above_boundary"]["n"],
       s15["specificity_no_trigger_rate_among_below_boundary"]["k"], s15["specificity_no_trigger_rate_among_below_boundary"]["n"]), (14, 15, 8, 15))

# ---------------------------------------------------------------- B6
b6 = []
for rid, rel in (("run1", "drift_pair.json"), ("run2", "run2/drift_pair_run2.json")):
    p = os.path.join(B6, rel)
    d = json.load(open(p))
    rf = d["relative_frequency_offset_ppm"]
    b6.append(dict(id=rid, verdict=d["verdict"]["overall"].replace(" ", "_"), relativePpm=rf["ppm"], ci95=rf["ci95"], halfwidthPpm=rf["halfwidth_ppm"],
                   armA={k: d["arm_a"][k] for k in ("label", "platform", "rows_total", "rows_retained", "duration_min", "crystal_ppm_vs_utc", "csv", "csv_sha256")},
                   armB={k: d["arm_b"][k] for k in ("label", "platform", "rows_total", "rows_retained", "duration_min", "crystal_ppm_vs_utc", "csv", "csv_sha256")},
                   stability=d["stability"], criteria=d["verdict"]["criteria"], pairing=d["pairing"], scopeLimits=d.get("scope_limits", []),
                   rawCsvPresent=False, sourcePath=f"outputs/B6_two_machine_2026-10-02/{rel}", sourceSha256=sha(p)))
check("B6 measurements", len(b6), 2)
check("B6 run1 NOT_ESTABLISHED, run2 ESTABLISHED", (b6[0]["verdict"], b6[1]["verdict"]), ("NOT_ESTABLISHED", "ESTABLISHED"))
check("B6 raw CSVs absent from the repo (not approximated)", [os.path.isfile(os.path.join(B6, x["armA"]["csv"])) or os.path.isfile(os.path.join(B6, x["armB"]["csv"])) for x in b6], [False, False])

doc = dict(campaign=campaign, pilot=pilot, pilotSummary=pilot_summary, b6=b6, checks=checks,
           counts=dict(campaign=len(campaign), campaignCsvRows=sum(c["csvRows"] for c in campaign), pilot=len(pilot), pilotSummary=len(pilot_summary), b6=len(b6)))
with gzip.open(OUT, "wt", compresslevel=9) as f:
    json.dump(doc, f, separators=(",", ":"))
bad = [c for c in checks if not c["ok"]]
print(json.dumps(doc["counts"]), f"checks: {len(checks) - len(bad)}/{len(checks)} ok")
sys.exit(1 if bad else 0)
