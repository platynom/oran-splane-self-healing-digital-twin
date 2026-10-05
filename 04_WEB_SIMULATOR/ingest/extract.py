#!/usr/bin/env python3
"""Extract the project's real evidence archives into a derived, gzip-compressed JSON dataset
that scripts/ingest.ts loads into PostgreSQL.

Sources (read-only; nothing outside 04_WEB_SIMULATOR is modified):
  03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz      140 recovery-loop runs
  03_RECOVERY_LOOP_S-PLANE/results/EVALUATION_RL.json                   per-run scores (cross-check only)
  01_.../corrected_final/splane_campaign_CORRECTED_2026-09-20.tgz      168-run detection campaign
  01_.../corrected_final/EVALUATION_V4.json                            campaign evaluation (cross-check only)
  00_LATEST_PRESENTED_DECK_AND_DELIVERABLES/*_2026-10-05.xlsx          fault catalogue

Every archive is sha256-checked against the hash published next to it before it is opened.
Health is computed exactly as PREREGISTRATION.md section 4 / analyse.py define it. Any per-run
value that differs from EVALUATION_RL.json is written to DATA_DISCREPANCIES.md and makes the
script exit non-zero.

Usage: python3 ingest/extract.py [--repo ..] [--out data/derived]
"""
from __future__ import annotations
import argparse, collections, gzip, hashlib, io, json, os, re, statistics, struct, sys, tarfile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=os.path.abspath(os.path.join(HERE, "..", "..")))
ap.add_argument("--out", default=os.path.abspath(os.path.join(HERE, "..", "data", "derived")))
ap.add_argument("--discrepancies", default=os.path.abspath(os.path.join(HERE, "..", "DATA_DISCREPANCIES.md")))
A = ap.parse_args()
REPO, OUT = A.repo, A.out
os.makedirs(OUT, exist_ok=True)

RL_DIR = os.path.join(REPO, "03_RECOVERY_LOOP_S-PLANE")
RL_TGZ = os.path.join(RL_DIR, "results", "recovery_eval_runs_r13-r17.tgz")
RL_EVAL = os.path.join(RL_DIR, "results", "EVALUATION_RL.json")
RL_SUMS = os.path.join(RL_DIR, "results", "SHA256SUMS.txt")
CF_DIR = os.path.join(REPO, "01_CURRENT_SPlane_SelfHealing", "oran_splane_selfhealing", "gap_coverage_2026-09-20", "corrected_final")
CF_TGZ = os.path.join(CF_DIR, "splane_campaign_CORRECTED_2026-09-20.tgz")
CF_SUM = CF_TGZ + ".sha256"
CF_EVAL = os.path.join(CF_DIR, "EVALUATION_V4.json")
DECK = os.path.join(REPO, "00_LATEST_PRESENTED_DECK_AND_DELIVERABLES")
XLSX_DET = os.path.join(DECK, "ORAN_Fault_Detectability_v2026-10-05.xlsx")
XLSX_CLS = os.path.join(DECK, "ORAN_SPlane_Attack_vs_Benign_Classification_v2026-10-05.xlsx")
XLSX_PKT = os.path.join(DECK, "ORAN_SPlane_Packets_to_Classification_2026-10-05.xlsx")
XLSX_MTX = os.path.join(DECK, "ORAN_SPlane_Parameter_Fault_Matrix_v2026-10-05.xlsx")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def published_hash(sums_file, name):
    for line in open(sums_file):
        p = line.split()
        if len(p) >= 2 and os.path.basename(p[1]) == name:
            return p[0]
    raise SystemExit(f"no published hash for {name} in {sums_file}")

provenance = {"sources": [], "notes": []}
def check(path, sums, name=None):
    got, want = sha256(path), published_hash(sums, name or os.path.basename(path))
    if got != want:
        raise SystemExit(f"HASH MISMATCH {path}: {got} != published {want}")
    provenance["sources"].append(dict(path=os.path.relpath(path, REPO), sha256=got, verified_against=os.path.relpath(sums, REPO)))

check(RL_TGZ, RL_SUMS); check(RL_EVAL, RL_SUMS); check(CF_TGZ, CF_SUM)
for p in (CF_EVAL, XLSX_DET, XLSX_CLS, XLSX_PKT, XLSX_MTX):
    provenance["sources"].append(dict(path=os.path.relpath(p, REPO), sha256=sha256(p), verified_against=None))

# ---------------------------------------------------------------- definitions (PREREGISTRATION.md s4)
ALLOW_GM = {"020000fffe00000a", "020000fffe00000b"}
LEGIT_PARENT = {"020000fffe000001", "020000fffe0000c5"}
PRIMARY = ("ru1", "ru2")
OWN = {"ru1": "020000fffe00000c", "ru2": "020000fffe00000d", "ru3": "020000fffe00000e"}
WINDOW_S, TAIL_S = 40.0, 5.0

def ident(s):
    return s.split("-")[0].replace(".", "") if s else ""

def healthy(r, legit):
    return (r.get("portState") in ("SLAVE", "UNCALIBRATED")
            and ident(r.get("parentPortIdentity")) in legit
            and ident(r.get("grandmasterIdentity")) in ALLOW_GM)

SCEN_META = {
    "baseline": dict(code="BASE", cls="healthy", title="Baseline (healthy control)"),
    "A1_rogue_master": dict(code="A1", cls="attack", title="Rogue grandmaster"),
    "A2_sync_spoof": dict(code="A2", cls="attack", title="Sync / Follow_Up spoofing"),
    "A3_replay": dict(code="A3", cls="attack", title="Replay"),
    "A5_dos_flood": dict(code="A5", cls="attack", title="DoS / PTP flooding"),
    "A8_rogue_bc": dict(code="A8", cls="attack", title="Rogue boundary clock"),
    "C1_removal": dict(code="C1", cls="attack", title="Interception and removal (BC port blackholed)"),
    "C2_malformed": dict(code="C2", cls="attack", title="Malformed frames"),
    "C3_wholesecond": dict(code="C3", cls="attack", title="Whole-second field abuse"),
    "B2_gm_failover": dict(code="B2", cls="benign", title="Planned grandmaster changeover"),
    "B3_pdv_congestion": dict(code="B3", cls="benign", title="PDV / congestion"),
    "B7_topology_change": dict(code="B7", cls="benign", title="Topology change (RU3 link bounced)"),
    "B_bc_replacement": dict(code="B_bc", cls="benign", title="Planned boundary-clock replacement"),
    "B_unplanned_failover": dict(code="B_unpl", cls="ambiguous", title="Unplanned grandmaster failover (ambiguous)"),
}

# ---------------------------------------------------------------- pcap
MSG = {0: "Sync", 1: "Delay_Req", 2: "Pdelay_Req", 3: "Pdelay_Resp", 8: "Follow_Up", 9: "Delay_Resp",
       10: "Pdelay_Resp_Follow_Up", 11: "Announce", 12: "Signaling", 13: "Management"}
MASTER_TYPES = {0, 8, 9, 11}

def pcap_frames(raw):
    f = io.BytesIO(raw)
    gh = f.read(24)
    if len(gh) < 24: return
    magic = struct.unpack("<I", gh[:4])[0]
    endian, nano = ("<", False) if magic in (0xa1b2c3d4, 0xa1b23c4d) else (">", False)
    if magic == 0xa1b23c4d: nano = True
    while True:
        h = f.read(16)
        if len(h) < 16: break
        s, us, il, _ = struct.unpack(endian + "IIII", h)
        d = f.read(il)
        if len(d) < 15: continue
        et = struct.unpack(">H", d[12:14])[0]; off = 14
        if et == 0x8100 and len(d) >= 19:
            et = struct.unpack(">H", d[16:18])[0]; off = 18
        if et != 0x88F7: continue
        yield s + (us / 1e9 if nano else us / 1e6), d[6:12].hex(), d[off] & 0x0F

def mac(s):  # "02:00:00:00:00:62" -> "020000000062"
    return s.replace(":", "").lower()

LOG_RE = re.compile(r"ptp4l\[(\d+\.\d+)\]: (.*)")
STATE_RE = re.compile(r"port (\d+) \(([^)]+)\): (\w+) to (\w+) on (\w+)")

def parse_ptp4l(text, node, t0):
    out = []
    for line in text.splitlines():
        m = LOG_RE.match(line)
        if not m: continue
        t, msg = float(m.group(1)), m.group(2)
        sm = STATE_RE.match(msg)
        if sm:
            if sm.group(2).startswith("/var/run"): continue
            out.append(dict(t=round(t - t0, 3), node=node, kind="port_state", iface=sm.group(2),
                            from_=sm.group(3), to=sm.group(4), cause=sm.group(5)))
        elif msg.startswith("selected best master clock"):
            out.append(dict(t=round(t - t0, 3), node=node, kind="best_master", clock=msg.split()[-1]))
        elif "assuming the grand master role" in msg:
            out.append(dict(t=round(t - t0, 3), node=node, kind="gm_role", iface=msg.split("(")[1].split(")")[0]))
        elif "timed out while polling for tx timestamp" in msg:
            out.append(dict(t=round(t - t0, 3), node=node, kind="tx_timeout"))
    return out

# ---------------------------------------------------------------- recovery runs
TMP = tempfile.mkdtemp(prefix="rl_extract_")
def read_member(tf, name):
    p = os.path.join(TMP, name)
    return open(p, "rb").read() if os.path.isfile(p) else None

print("reading", RL_TGZ)
tf = tarfile.open(RL_TGZ, "r:gz")
names = tf.getnames()
tf.extractall(TMP, filter="data")
run_dirs = sorted({n.split("/")[1] if n.startswith("./") else n.split("/")[0] for n in names if "__r" in n})
prefix = "./" if names and names[0].startswith(".") else ""
eval_rl = {r["run"]: r for r in json.load(open(RL_EVAL))["runs"]}
runs, discrepancies, anchor_resid = [], [], []

for rd in run_dirs:
    P = lambda f: f"{prefix}{rd}/{f}"
    ctx = json.loads(read_member(tf, P("context.json")))
    tl = json.loads(read_member(tf, P("timeline.json")))
    state = json.loads(read_member(tf, P("state.json")))
    t0 = tl["t0_mono"]
    legit = set(LEGIT_PARENT)
    if ctx.get("expected_bc_identity_secondary"): legit.add(ctx["expected_bc_identity_secondary"])
    obs = [json.loads(l) for l in read_member(tf, P("observer.jsonl")).decode().splitlines() if l.strip()]
    # rounds: group the three per-node samples of one poll cycle (identical to analyse.py)
    rounds, cur = [], {}
    for r in obs:
        if r["node"] in cur:
            rounds.append(cur); cur = {}
        cur[r["node"]] = r
    if cur: rounds.append(cur)
    samples = []
    for i, rdn in enumerate(rounds):
        tr = min(x["t"] for x in rdn.values()) - t0
        for n, x in rdn.items():
            samples.append(dict(round=i, tMono=x["t"], t=round(x["t"] - t0, 3), tRound=round(tr, 3), node=n,
                                portState=x.get("portState"), parent=ident(x.get("parentPortIdentity")) or None,
                                parentPort=x.get("parentPortIdentity"), gm=ident(x.get("grandmasterIdentity")) or None,
                                gmClockClass=int(x["gm.ClockClass"]) if x.get("gm.ClockClass", "").isdigit() else None,
                                stepsRemoved=int(x["stepsRemoved"]) if x.get("stepsRemoved", "").isdigit() else None,
                                healthy=healthy(x, legit)))
    # --- independent recomputation of analyse.py's metrics (cross-check) ---
    def t_of(rdn): return min(x["t"] for x in rdn.values()) - t0
    post = [rdn for rdn in rounds if 0 <= t_of(rdn) <= WINDOW_S]
    pre = [rdn for rdn in rounds if -10.0 <= t_of(rdn) < 0]
    ok = lambda rdn, nodes=PRIMARY: all(n in rdn and healthy(rdn[n], legit) for n in nodes)
    unhealthy = sum(t_of(b) - t_of(a) for a, b in zip(post, post[1:]) if not ok(a))
    ru3 = sum(t_of(b) - t_of(a) for a, b in zip(post, post[1:]) if not ok(a, ("ru3",)))
    tail = [rdn for rdn in post if t_of(rdn) >= WINDOW_S - TAIL_S]
    restored = bool(tail) and all(ok(rdn) for rdn in tail)
    pre_ok = sum(ok(rdn) for rdn in pre) / max(1, len(pre))
    mine = dict(unhealthy_s=round(unhealthy, 2), ru3_unhealthy_s=round(ru3, 2), restored_at_end=restored,
                pre_t0_service_ok_fraction=round(pre_ok, 3))
    ref = eval_rl.get(rd)
    if ref is None:
        discrepancies.append(f"| {rd} | present in archive | missing from EVALUATION_RL.json |")
    else:
        for k, v in mine.items():
            if ref[k] != v:
                discrepancies.append(f"| {rd} | {k} recomputed = {v} | EVALUATION_RL.json = {ref[k]} |")
    # --- loop events ---
    events = []
    for l in read_member(tf, P("loop.jsonl")).decode().splitlines():
        if not l.strip(): continue
        e = json.loads(l)
        k = e.pop("kind"); tm = e.pop("t_mono"); t = round(tm - t0, 3); e.pop("t_rel", None); e.pop("mode", None)
        if k == "start":
            events.append(dict(t=t, tMono=tm, kind="loop_start", detail=dict(params=e.get("params"), state=e.get("state"))))
        elif k == "eval":
            events.append(dict(t=t, tMono=tm, kind="eval", verdict=e.get("verdict"), hint=e.get("hint"),
                               detail=dict(reason=e.get("reason"), n=e.get("n"), violations=e.get("violations"))))
        elif k in ("act", "would_act"):
            events.append(dict(t=t, tMono=tm, kind=k, action=e["action"], target=e["target"],
                               detail=dict(reason=e.get("reason"), executed=e.get("executed"), stderr=e.get("stderr"))))
        elif k == "verify":
            events.append(dict(t=t, tMono=tm, kind="verify", action=e["action"], target=e["target"], ok=e["ok"], detail=dict(nodes=e.get("detail"))))
        elif k == "rollback":
            events.append(dict(t=t, tMono=tm, kind="rollback", action=e["action"], target=e["target"]))
        elif k == "escalate":
            events.append(dict(t=t, tMono=tm, kind="escalate", detail=dict(reason=e["reason"])))
        elif k == "end":
            events.append(dict(t=t, tMono=tm, kind="loop_end", detail=dict(isolated=e.get("isolated"), standby_active=e.get("standby_active"),
                                                               escalations=e.get("escalations"))))
    # --- ptp4l logs (CLOCK_MONOTONIC, same clock as the loop and observer) ---
    ptp = []
    logs = {}
    for node in ("gma", "gmb", "bc", "ru1", "ru2", "ru3", "rogue", "rbc", "bcs", "bc2"):
        raw = read_member(tf, P(f"{node}.log"))
        if raw is not None:
            logs[node] = raw.decode(errors="replace")
            ptp += parse_ptp4l(logs[node], node, t0)
    ptp.sort(key=lambda x: x["t"])
    # --- packets: per-0.5 s counts per (segment, sender, message type), aligned to CLOCK_MONOTONIC ---
    P_ = ctx["randomised_params"]
    macmap = {"020000000002": "bc", "02000000000c": "ru1", "02000000000d": "ru2", "02000000000e": "ru3",
              "0200000000c6": "bcs", "0200000000b2": "bc2", "02000000000a": "gma", "02000000000b": "gmb",
              "020000000001": "bc", "0200000000c5": "bcs", "0200000000b1": "bc2"}
    if ctx["scenario"] == "A1_rogue_master": macmap[mac(P_["rogue_mac"])] = "rogue"
    if ctx["scenario"] == "A8_rogue_bc":
        macmap[mac(P_["rbc_dn_mac"])] = "rbc"; macmap[mac(P_["rbc_up_mac"])] = "rbc"
    if ctx["scenario"] == "A5_dos_flood": macmap.setdefault(mac(P_["flood_src"]), "flooder")
    dn = list(pcap_frames(gzip.decompress(read_member(tf, P("dn.pcap.gz")))))
    up_raw = read_member(tf, P("up.pcap.gz"))
    up = list(pcap_frames(gzip.decompress(up_raw))) if up_raw else []
    # anchor: BC downstream port's first Announce on brDN <-> bc.log "v-bc-dn ... to MASTER"
    bc_master = next((e["t"] for e in ptp if e["node"] == "bc" and e["kind"] == "port_state"
                      and e.get("iface") == "v-bc-dn" and e["to"] == "MASTER"), None)
    first_bc_ann = next((t for t, m_, ty in dn if m_ == "020000000002" and ty == 11), None)
    anchor = None
    if bc_master is not None and first_bc_ann is not None:
        anchor = first_bc_ann - bc_master          # realtime - (mono - t0)
        dn_mac = {"rogue": mac(P_["rogue_mac"]), "rbc": mac(P_["rbc_dn_mac"]), "bcs": "0200000000c6", "bc2": "0200000000b2"}
        for dev, iface in (("rogue", "v-rogue"), ("rbc", "v-rbc-dn"), ("bcs", "v-bcs-dn"), ("bc2", "v-bc2-dn")):
            if dev not in logs: continue
            tm = next((e["t"] for e in ptp if e["node"] == dev and e["kind"] == "port_state" and e.get("iface") == iface
                       and e["to"] == "MASTER"), None)
            fa = next((t for t, m_, ty in dn if m_ == dn_mac[dev] and ty == 11), None)
            if tm is not None and fa is not None:
                anchor_resid.append(round((fa - anchor) - tm, 4))
    bins = collections.Counter()
    ann_times = []
    if anchor is not None:
        for seg, frames in (("dn", dn), ("up", up)):
            for t, m_, ty in frames:
                tr = t - anchor
                dev = macmap.get(m_, "unknown")
                if ctx["scenario"] in ("A2_sync_spoof", "A3_replay", "C2_malformed", "C3_wholesecond", "A5_dos_flood") and (
                        dev in ("unknown", "flooder") or (dev == "ru3" and ty in MASTER_TYPES)
                        or (seg == "dn" and dev in ("gma", "gmb"))):
                    # (C2/C3 injectors send with GM-A's MAC, inject_malformed.py / inject_wholesecond.py; GM-A itself
                    # is only on brUP, so GM MACs on brDN in these scenarios are the injector)
                    # run_one.py starts every injector inside RU3's namespace: master-role frames from RU3's MAC and
                    # frames from MACs that are not provisioned on the segment are attributed to it
                    dev = "injector"
                b = round((tr // 0.5) * 0.5, 1)
                if -20.0 <= b <= 42.0:
                    bins[(seg, b, dev, MSG.get(ty, f"type{ty}"))] += 1
                if seg == "dn" and ty == 11 and dev in ("bc", "bcs", "bc2"):
                    ann_times.append(tr)
    ann_times.sort()
    post_ann = [t for t in ann_times if 0 <= t <= WINDOW_S]
    gaps = [b - a for a, b in zip([0.0] + post_ann, post_ann + [WINDOW_S])]
    max_gap = round(max(gaps), 3) if gaps else None
    # Service-continuity input for the sandbox model: Announce on brDN from the provisioned master ports the
    # loop's channel 2 watches (primary BC, and the planned replacement BC in B_bc_replacement; the standby BC
    # is excluded exactly as recovery_loop.py excludes p-bcs-dn). Gaps >= 0.4 s are kept; a trailing gap
    # that never closes is stored with end = null.
    ch2_dev = ("bc", "bc2") if ctx["scenario"] == "B_bc_replacement" else ("bc",)
    ch2 = sorted(t - anchor for seg_, frames_ in (("dn", dn),) for t, m_, ty in frames_
                 if ty == 11 and macmap.get(m_) in ch2_dev) if anchor is not None else []
    ch2 = [t for t in ch2 if -12.0 <= t <= 42.0]
    ann_gaps = [[round(a, 3), round(b, 3)] for a, b in zip(ch2, ch2[1:]) if b - a >= 0.4]
    if ch2 and ch2[-1] < 41.0:
        ann_gaps.append([round(ch2[-1], 3), None])
    # --- artefacts ---
    nft = (read_member(tf, P("nft_final.txt")) or b"").decode(errors="replace")
    has_bcs_log = read_member(tf, P("bcs.log")) is not None
    runs.append(dict(
        id=rd, scenario=ctx["scenario"], cls=ctx["class"], rep=ctx["rep"], arm=ctx["arm"],
        t0Mono=t0, tStartRel=round(tl["t_start_mono"] - t0, 3), tEndRel=round(tl["t_end_mono"] - t0, 3),
        params=ctx["randomised_params"], state=state, maintenanceWindowOpen=ctx.get("maintenance_window_open", False),
        legitParents=sorted(legit), nftFinal=nft, standbyLogPresent=has_bcs_log,
        pcapAnchor=dict(method="BC downstream first Announce on brDN aligned to bc.log 'v-bc-dn ... to MASTER'",
                        offset_s=round(anchor, 6) if anchor is not None else None),
        maxProvisionedAnnounceGapS=max_gap, announceGaps=ann_gaps,
        samples=samples, events=events, ptp4l=ptp,
        packets=[[seg, b, dev, ty, n] for (seg, b, dev, ty), n in sorted(bins.items())],
        crossCheck=mine))
    print(f"  {rd}: samples={len(samples)} events={len(events)} ptp4l={len(ptp)} bins={len(bins)} maxGap={max_gap}")
tf.close()
import shutil; shutil.rmtree(TMP, ignore_errors=True)

if anchor_resid:
    provenance["notes"].append(dict(topic="pcap alignment", detail=(
        "tcpdump stamps frames with CLOCK_REALTIME; the loop, observer and ptp4l use CLOCK_MONOTONIC. Each run's packet "
        "series is aligned with one anchor (BC downstream port's first Announce vs its ptp4l 'to MASTER' line). Validated on "
        f"{len(anchor_resid)} independent anchors (rogue / rogue-BC / standby-BC / replacement-BC first Announce vs their own "
        f"'to MASTER' log line): median residual {statistics.median(anchor_resid)*1000:.1f} ms, max |residual| "
        f"{max(abs(x) for x in anchor_resid)*1000:.1f} ms.")))
    provenance["anchorResiduals_s"] = anchor_resid

# ---------------------------------------------------------------- campaign (168 runs)
print("reading", CF_TGZ)
camp = []
tf = tarfile.open(CF_TGZ, "r:gz")
members = {m.name: m for m in tf.getmembers()}
CTMP = tempfile.mkdtemp(prefix="cf_extract_")
tf.extractall(CTMP, members=[m for m in members.values() if m.name.endswith(".json")], filter="data")
cdirs = sorted({n.split("/")[2] for n in members if n.startswith("./cap/") and n.count("/") >= 3})
# Identical admissibility and scoring to evaluate_v4.py (rep from the directory name, EXPECT map,
# abstention credited only on the substantive path hint "B2?", attribution with its alias map).
EXPECT = {"A1_rogue_master": "ATTACK", "A2_sync_spoof": "ATTACK", "A3_replay": "ATTACK", "A5_dos_flood": "ATTACK",
          "A8_rogue_bc": "ATTACK", "C1_removal": "ATTACK", "C2_malformed": "ATTACK", "C3_wholesecond": "ATTACK",
          "baseline": "BENIGN", "B2_gm_failover": "BENIGN", "B_bc_replacement": "BENIGN", "B3_pdv_congestion": "BENIGN",
          "B7_topology_change": "BENIGN", "B_unplanned_failover": "UNKNOWN"}
ALIAS = {"A_intercept": "C1", "A_malformed": "C2", "A_wholesecond": "C3"}
ctx_rep_mismatch = []
for cd in cdirs:
    g = lambda f: json.load(open(os.path.join(CTMP, "cap", cd, f))) if os.path.isfile(os.path.join(CTMP, "cap", cd, f)) else None
    ctx, base, v2, v3 = g("context.json"), g("decision.json"), g("decision_v2.json"), g("decision_v3.json")
    rep = int(cd.split("__r")[-1]); sc = cd.split("__r")[0]
    if not (1 <= rep <= 12) or sc not in EXPECT: continue
    if ctx.get("rep") != rep: ctx_rep_mismatch.append(cd)
    camp.append(dict(id=cd, scenario=sc, rep=rep, expected=EXPECT[sc], truthClass=ctx["class"], truthFault=ctx.get("fault_id"),
                     description=ctx.get("description"), nPackets=(base.get("evidence") or {}).get("n_packets"),
                     baseVerdict=base["verdict"], baseHint=base.get("fault_hint"),
                     v2Verdict=v2["verdict"] if v2 else None, v2Hint=v2.get("fault_hint") if v2 else None,
                     v3Verdict=v3["verdict"], v3Hint=v3.get("fault_hint"),
                     v3Reason=(v3.get("reasons") or [""])[0][:400]))
tf.close()
import shutil; shutil.rmtree(CTMP, ignore_errors=True)
if ctx_rep_mismatch:
    provenance["notes"].append(dict(topic="campaign context.json rep field", detail=(
        f"{len(ctx_rep_mismatch)} campaign runs ({', '.join(sorted({c.split('__r')[0] for c in ctx_rep_mismatch}))}) carry "
        "rep=901 in context.json while the directory name gives 1..12. evaluate_v4.py takes the replicate from the directory "
        "name, so this app does the same. Informational; no number changes.")))
ev4 = json.load(open(CF_EVAL))
def camp_metrics(key, hint):
    A_ = [c for c in camp if c["expected"] == "ATTACK"]; B_ = [c for c in camp if c["expected"] == "BENIGN"]
    U_ = [c for c in camp if c["expected"] == "UNKNOWN"]
    return dict(tp=sum(c[key] == "ATTACK" for c in A_), n_attack=len(A_), tn=sum(c[key] == "BENIGN" for c in B_),
                n_benign=len(B_), abstain=sum(c[key] == "UNKNOWN" and c[hint] == "B2?" for c in U_), n_unknown=len(U_),
                attributed=sum(ALIAS.get(c[hint], c[hint]) == c["truthFault"] for c in A_))
for key, hint, label in (("baseVerdict", "baseHint", "frozen"), ("v2Verdict", "v2Hint", "v2"), ("v3Verdict", "v3Hint", "v3")):
    m = camp_metrics(key, hint)
    e = ev4[label]
    att_k = round(e["attribution"][0] * e["n_attack"])
    for a, b, ev in (("tp", "tp", e["tp"]), ("tn", "tn", e["tn"]), ("n_attack", "n_attack", e["n_attack"]),
                     ("n_benign", "n_benign", e["n_benign"]), ("abstain", "abstain_substantive", e["abstain_substantive"]),
                     ("attributed", "attribution x n_attack", att_k)):
        if m[a] != ev:
            discrepancies.append(f"| campaign {label} | {a} recomputed = {m[a]} | EVALUATION_V4.json {b} = {ev} |")
print("campaign runs:", len(camp), "v3:", camp_metrics("v3Verdict", "v3Hint"), "base:", camp_metrics("baseVerdict", "baseHint"))

# ---------------------------------------------------------------- fault catalogue (xlsx)
import openpyxl
def sheet_rows(path, sheet, header_first="ID"):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb[sheet].iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == header_first)
    hdr = [str(h).strip() if h else None for h in rows[hi]]
    out = []
    for r in rows[hi + 1:]:
        if not r or r[0] is None or str(r[0]).strip() in ("", "TALLY"): break
        out.append({hdr[i]: (str(v).strip() if v is not None else None) for i, v in enumerate(r) if i < len(hdr) and hdr[i]})
    return out
det = {r["ID"]: r for r in sheet_rows(XLSX_DET, "DETECTABILITY")}
att = {r["ID"]: r for r in sheet_rows(XLSX_CLS, "ATTACK catalog")}
ben = {r["ID"]: r for r in sheet_rows(XLSX_CLS, "BENIGN catalog")}
key = {r["ID"]: r for r in sheet_rows(XLSX_MTX, "FAULT KEY")}
looks = sheet_rows(XLSX_CLS, "LOOK-ALIKES", header_first="Shared symptom")
S = lambda r, prefix: next((v for k, v in r.items() if k and k.startswith(prefix)), None)
faults = []
for fid, r in det.items():
    c = att.get(fid) or ben.get(fid) or {}
    k = key.get(fid, {})
    faults.append(dict(id=fid, name=r["Fault"], cls=r["Class"], kind="catalogue",
                       source=S(r, "Source"), destination=S(r, "Destination"), attackDevices=S(r, "Attack devices"),
                       consequence=S(r, "Consequence"), detectableNow=S(r, "Detectable NOW"),
                       evidence=S(r, "Evidence"), thresholdBasis=S(r, "Threshold basis"), missing=S(r, "What is still missing"),
                       mechanism=S(c, "Mechanism") or S(c, "Cause"), signature=S(c, "Anomalous signature") or S(c, "Benign tell"),
                       reasoning=S(c, "Why it is an ATTACK"), lookAlike=S(c, "Look-alike"), citations=S(c, "Standard / source"),
                       testbedRequired=S(k, "Testbed required"), threatId=S(k, "O-RAN WG11"),
                       sourceFile="ORAN_Fault_Detectability_v2026-10-05.xlsx (DETECTABILITY) + Attack_vs_Benign_Classification (catalogues) + Parameter_Fault_Matrix (FAULT KEY)"))
per_sc = sheet_rows(XLSX_PKT, "PER-SCENARIO", header_first="Scenario")
for r in per_sc:
    sc = r["Scenario"]
    if sc in ("A1_rogue_master", "A2_sync_spoof", "A3_replay", "A5_dos_flood", "A8_rogue_bc", "B2_gm_failover", "B3_pdv_congestion", "B7_topology_change"):
        continue   # already present as catalogue rows A1..B8
    faults.append(dict(id=SCEN_META[sc]["code"] if sc in SCEN_META else sc, scenario=sc, name=SCEN_META.get(sc, {}).get("title", sc),
                       cls=r["Expected verdict"], kind="campaign scenario",
                       source=S(r, "Source"), destination=S(r, "Destination"), attackDevices=S(r, "Attack devices"),
                       consequence=S(r, "Consequence"), detectableNow=r.get("Status"),
                       evidence=f"Base rule {r.get('Base rule correct')} · v3 rule {r.get('v3 rule correct')} correct (168-run campaign)",
                       citations=None, sourceFile="ORAN_SPlane_Packets_to_Classification_2026-10-05.xlsx (PER-SCENARIO)"))
scen_extra = {r["Scenario"]: r for r in per_sc}

scenarios = []
for sc, m in SCEN_META.items():
    x = scen_extra.get(sc, {})
    scenarios.append(dict(id=sc, code=m["code"], cls=m["cls"], title=m["title"], expectedVerdict=x.get("Expected verdict"),
                          source=S(x, "Source") if x else None, destination=S(x, "Destination") if x else None,
                          attackDevices=S(x, "Attack devices") if x else None, consequence=S(x, "Consequence") if x else None))

# ---------------------------------------------------------------- write
def wgz(name, obj):
    with gzip.open(os.path.join(OUT, name), "wt", compresslevel=9) as f:
        json.dump(obj, f, separators=(",", ":"))
wgz("recovery_runs.json.gz", runs)
wgz("campaign_runs.json.gz", camp)
wgz("faults.json.gz", dict(faults=faults, lookAlikes=looks))
wgz("scenarios.json.gz", scenarios)
provenance["counts"] = dict(recovery_runs=len(runs), campaign_runs=len(camp), faults=len(faults), look_alikes=len(looks))
provenance["campaign_eval_v4"] = {k: ev4[k] for k in ("generated", "n_runs")} | {
    "v3": {k: ev4["v3"][k] for k in ("tp", "fn", "tn", "fp", "n_attack", "n_benign", "n_unknown", "abstain_substantive", "pooled_sensitivity", "pooled_specificity", "attribution")},
    "frozen": {k: ev4["frozen"][k] for k in ("tp", "fn", "tn", "fp", "pooled_sensitivity", "pooled_specificity", "attribution")}}
json.dump(provenance, open(os.path.join(OUT, "provenance.json"), "w"), indent=2)

if discrepancies:
    with open(A.discrepancies, "w") as f:
        f.write("# Data discrepancies found by ingest/extract.py\n\n| Item | Recomputed | Published |\n|---|---|---|\n")
        f.write("\n".join(discrepancies) + "\n")
    print(f"{len(discrepancies)} DISCREPANCIES -> {A.discrepancies}")
    sys.exit(2)
print("OK: every recomputed per-run value matches EVALUATION_RL.json; campaign counts match EVALUATION_V4.json")
