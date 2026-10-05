#!/usr/bin/env python3
"""
S-plane recovery loop: DETECT -> LOCALISE -> DECIDE -> ACT -> VERIFY (-> ROLLBACK).

Runs beside the frozen G.8275.1 software testbed (6 linuxptp 4.0 daemons in network
namespaces). It does NOT modify any frozen artefact:
  * detection channel 1 calls decision_rule_v3.decide_v2 (sha256 aa9417b7...), which in turn
    imports the frozen base rule decision_rule.py (sha256 c362e110...). Both hashes are checked
    at start-up and the loop refuses to run if either differs.
  * per-frame parsing uses parse_frame() from the frozen extractor ptp_deep_extract.py, so the
    rule sees exactly the 56-column records it saw in the 168-run campaign.

Standards basis for each element is given in RECOVERY_LOOP_DESIGN.md. In brief:
  ISOLATE   - RFC 7384 s5.1.1 (only authorised masters), s5.10.1 (discard packets from
              unsecured clocks); master_only ports / acceptable master table (Arnold & Frost,
              WSTS 2016); G.8275.1 per-port notSlave attribute.
  FAILOVER  - RFC 7384 s5.9 (redundant masters / redundant paths); IEEE 1588-2019 security
              Prong C (architecture guidance: redundant grandmasters and paths).
  TOLERATE  - benign, standards-consistent state change: no intervention.
  ESCALATE  - "raise alarm" (Arnold & Frost); the project's UNKNOWN verdict semantics.
  MONITOR   - IEEE 1588-2019 security Prong D (monitoring and management).

Modes: --mode act  (closed loop)   --mode observe (matched control: identical detection and
decision logging, no action executed).
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, importlib.util, json, os, select, socket, struct
import subprocess, sys, tempfile, threading, time

SPTB = os.environ.get("SPTB", "/opt/sptb")
HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_HASHES = {
    "run/decision_rule.py":    "c362e11072344161437aaae33b2902caf9bca57dfc33f653a9c2184edae8a985",
    "run/decision_rule_v3.py": "aa9417b701cc09dcf242a814cc136ce2acd561269389b7553618205997b7f330",
}
ETH_P_ALL = 0x0003
ETH_PTP = 0x88F7
PACKET_OUTGOING = 4
MASTER_ROLE_TYPES = {"Sync", "Follow_Up", "Delay_Resp", "Announce"}

# ---- pre-registered loop parameters (see PREREGISTRATION.md; frozen with this file) ----
WINDOW_S          = 6.0    # sliding evidence window handed to the frozen rule
EVAL_PERIOD_S     = 1.0    # one rule evaluation per second
PERSIST_K, PERSIST_N = 2, 3   # act only if >=2 of the last 3 evaluations agree on ATTACK
WARMUP_S          = 12.0   # no decisions until the testbed has settled (BMCA start-up)
SERVICE_LOSS_S    = 2.0    # no Announce from any provisioned master port for this long -> loss
SERVICE_LOSS_MAINT_S = 10.0  # grace when an operator maintenance window is open
VERIFY_DEADLINE_S = 20.0   # action must restore provisioned parent + allow-listed GM within this
VERIFY_POLL_S     = 0.5
MAX_ACTIONS       = 4

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def load_frozen():
    for rel, h in FROZEN_HASHES.items():
        got = sha(os.path.join(SPTB, rel))
        if got != h:
            sys.exit(f"REFUSING TO RUN: {rel} hash {got} != frozen {h}")
    def load(name, path):
        s = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
    rule = load("decision_rule_v3", os.path.join(SPTB, "run/decision_rule_v3.py"))
    ext = load("ptp_deep_extract", os.path.join(SPTB, "ptp_deep_extract.py"))
    return rule, ext

def mono():
    return time.monotonic()      # same clock (CLOCK_MONOTONIC) that ptp4l stamps its log lines with

# --------------------------------------------------------------------------- capture
class SegmentCapture(threading.Thread):
    """Capture every PTP frame entering the segment bridge, tagged with its ingress port.
    One AF_PACKET socket per bridge port (the root-namespace end of each veth); frames the
    bridge transmits out of a port are PACKET_OUTGOING and skipped, so each frame on the
    segment is recorded exactly once, at the port it came in on."""
    def __init__(self, bridge, ext, log):
        super().__init__(daemon=True)
        self.bridge, self.ext, self.log = bridge, ext, log
        self.socks = {}                      # port -> socket
        self.lock = threading.Lock()
        self.frames = collections.deque()    # (mono_t, port, rec|None, raw_len)
        self.last_announce_from = {}         # port -> mono_t
        self.stop_flag = False

    def _rescan(self):
        try:
            ports = set(os.listdir(f"/sys/class/net/{self.bridge}/brif"))
        except FileNotFoundError:
            ports = set()
        for p in ports - set(self.socks):
            try:
                s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
                s.bind((p, 0)); s.setblocking(False); self.socks[p] = s
            except OSError:
                pass
        for p in set(self.socks) - ports:
            try: self.socks[p].close()
            except OSError: pass
            del self.socks[p]

    def run(self):
        last_scan = 0
        while not self.stop_flag:
            if mono() - last_scan > 0.5:
                self._rescan(); last_scan = mono()
            rl = list(self.socks.values())
            if not rl:
                time.sleep(0.05); continue
            try:
                ready, _, _ = select.select(rl, [], [], 0.1)
            except (OSError, ValueError):
                self._rescan(); continue
            for s in ready:
                port = next((k for k, v in self.socks.items() if v is s), None)
                for _ in range(256):
                    try:
                        data, addr = s.recvfrom(65535)
                    except (BlockingIOError, OSError):
                        break
                    if addr[2] == PACKET_OUTGOING or len(data) < 14:
                        continue
                    et = struct.unpack(">H", data[12:14])[0]
                    if et == 0x8100 and len(data) >= 18:
                        et = struct.unpack(">H", data[16:18])[0]
                    if et != ETH_PTP:
                        continue
                    t = mono()
                    try:
                        rec = self.ext.parse_frame(time.time_ns(), data)
                    except Exception:
                        rec = None
                    with self.lock:
                        self.frames.append((t, port, rec, len(data)))
                        if rec and rec.get("message_type") == "Announce":
                            self.last_announce_from[port] = t

    def window(self, now, span):
        with self.lock:
            while self.frames and self.frames[0][0] < now - 30.0:
                self.frames.popleft()
            return [f for f in self.frames if f[0] >= now - span]

# --------------------------------------------------------------------------- outcome probe
def pmc_get(node, *ds):
    cmd = ["ip", "netns", "exec", node, "pmc", "-u", "-b", "0", "-d", "24",
           "-s", f"/var/run/p.{node}"] + [f"GET {d}" for d in ds]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return {}
    r = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in ("parentPortIdentity", "grandmasterIdentity", "portState"):
            r[parts[0]] = parts[1]
    return r

def ident(s):
    """'020000.fffe.000001-2' -> '020000fffe000001'"""
    return s.split("-")[0].replace(".", "") if s else ""

# --------------------------------------------------------------------------- the loop
class Loop:
    def __init__(self, args):
        self.args = args
        self.rule, self.ext = load_frozen()
        self.prov = json.load(open(args.provisioning))
        self.state = json.load(open(args.state))
        self.log_f = open(args.log, "a")
        self.cap = SegmentCapture(self.prov["segment"], self.ext, self.log)
        self.hist = collections.deque(maxlen=PERSIST_N)
        self.actions = []           # executed (or, in observe mode, would-be) actions
        self.isolated = set()
        self.isolated_at = {}
        self.standby_active = False
        self.escalated = set()
        self.t0 = mono()
        self.inventory = dict(self.prov["port_inventory"])
        pr = self.state.get("planned_replacement")
        if pr:
            self.inventory[pr["port"]] = {"device": "BC-R (planned replacement, maintenance ticket)",
                                          "role": "master", "identities": [pr["identity"]]}

    def log(self, kind, **kw):
        kw.update(kind=kind, t_mono=round(mono(), 3), t_rel=round(mono() - self.t0, 3),
                  mode=self.args.mode)
        self.log_f.write(json.dumps(kw) + "\n"); self.log_f.flush()

    def rule_ctx(self):
        ctx = {k: self.prov[k] for k in ("gm_allowlist", "provisioned_backup_gm", "expected_bc_identity",
                                          "expected_client_identities", "expected_steps_removed_at_ru")}
        ctx["maintenance_window_open"] = bool(self.state.get("maintenance_window_open", False))
        ctx["leap_window_open"] = False
        pr = self.state.get("planned_replacement")
        if pr:
            ctx["expected_bc_identity_secondary"] = pr["identity"]
        elif self.standby_active:
            ctx["expected_bc_identity_secondary"] = self.prov["standby_bc_identity"]
        return ctx

    def master_ports(self):
        return {p for p, v in self.inventory.items() if v["role"] == "master"}

    # ---- channel 1: frozen packet-legality rule on a sliding window ----
    def evaluate(self, now):
        win = self.cap.window(now, WINDOW_S)
        # frames that ingress on an isolated port after its isolation never reach the segment
        win = [f for f in win if not (f[1] in self.isolated_at and f[0] >= self.isolated_at[f[1]])]
        recs = [f[2] for f in win if f[2] is not None]
        if not recs:
            return None
        fd, path = tempfile.mkstemp(suffix=".deep.csv"); os.close(fd)
        try:
            with open(path, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=self.ext.COLUMNS, extrasaction="ignore")
                w.writeheader()
                for r in recs: w.writerow(r)
            v, hint, why, ev = self.rule.decide_v2(path, self.rule_ctx())
        finally:
            os.unlink(path)
        return dict(verdict=v, hint=hint, reason=(why[0][:240] if why else ""), n=len(recs),
                    violations=self.localise(win))

    # ---- localisation: which ingress port breaks the provisioned port roles ----
    def localise(self, win):
        per = collections.defaultdict(lambda: dict(n=0, master_msgs=0, foreign_ids=collections.Counter(),
                                                   malformed=0))
        for t, port, rec, ln in win:
            d = per[port]; d["n"] += 1
            if rec is None:
                d["malformed"] += 1; continue
            if rec.get("message_type") in MASTER_ROLE_TYPES:
                d["master_msgs"] += 1
            sid = rec.get("source_clock_identity") or ""
            if port in self.inventory and sid not in self.inventory[port]["identities"]:
                d["foreign_ids"][sid] += 1
            if str(rec.get("version_ptp", "2")) not in ("2", ""):
                d["malformed"] += 1
        out = {}
        for port, d in per.items():
            why = []
            inv = self.inventory.get(port)
            if inv is None:
                why.append("unprovisioned port originating PTP")
            else:
                if inv["role"] == "client" and d["master_msgs"] > 0:
                    why.append(f"client-role port originated {d['master_msgs']} master-role messages")
                if sum(d["foreign_ids"].values()) > 0:
                    why.append(f"source identities not provisioned for this port: {dict(d['foreign_ids'].most_common(3))}")
                if d["malformed"] > 0:
                    why.append(f"{d['malformed']} malformed frames")
            if why:
                out[port] = why
        return out

    # ---- actions ----
    def nft(self, *cmd):
        return subprocess.run(["nft"] + list(cmd), capture_output=True, text=True)

    def act_isolate(self, port, reason):
        rec = dict(action="ISOLATE_PTP_AT_PORT", target=port, reason=reason)
        if self.args.mode == "act":
            self.nft("add", "table", "bridge", "rl")
            self.nft("add", "chain", "bridge", "rl", "guard", "{ type filter hook prerouting priority -200 ; policy accept ; }")
            r = self.nft("add", "rule", "bridge", "rl", "guard", "iifname", port, "ether", "type", "0x88f7",
                         "counter", "drop", "comment", f"\"rl-isolate-{port}\"")
            rec["executed"] = (r.returncode == 0); rec["stderr"] = r.stderr.strip()[:200]
        self.isolated.add(port)
        if self.args.mode == "act":
            self.isolated_at[port] = mono()
        return rec

    def undo_isolate(self, port):
        if self.args.mode != "act": return
        self.isolated_at.pop(port, None); self.isolated.discard(port)
        out = self.nft("-a", "list", "chain", "bridge", "rl", "guard").stdout
        for line in out.splitlines():
            if f"rl-isolate-{port}" in line and "# handle" in line:
                h = line.rsplit("# handle", 1)[1].strip()
                self.nft("delete", "rule", "bridge", "rl", "guard", "handle", h)

    def act_failover(self, reason):
        rec = dict(action="ACTIVATE_STANDBY_BC", target="bcs", reason=reason)
        if self.args.mode == "act":
            cmd = (f"ip netns exec bcs ptp4l -f {SPTB}/cfg/bcs.cfg -i v-bcs-up -i v-bcs-dn -m "
                   f"--uds_address=/var/run/p.bcs --uds_ro_address=/var/run/pr.bcs "
                   f">{self.args.outdir}/bcs.log 2>&1 & echo $! >{self.args.outdir}/bcs.pid")
            r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
            rec["executed"] = (r.returncode == 0)
        self.standby_active = True
        return rec

    def undo_failover(self):
        if self.args.mode != "act": return
        pid = os.path.join(self.args.outdir, "bcs.pid")
        if os.path.exists(pid):
            subprocess.run(["kill", open(pid).read().strip()], capture_output=True)

    def verify(self, exclude_nodes):
        """Pass when every non-excluded RU reports a provisioned master-role parent, an
        allow-listed grandmaster and a tracking port state, measured through pmc (-d 24)."""
        ok_ids = set()
        for v in self.inventory.values():
            if v["role"] == "master": ok_ids |= set(v["identities"])
        deadline = min(mono() + VERIFY_DEADLINE_S, self.t0 + self.args.duration)
        while mono() < deadline:
            res = {}
            for n in ("ru1", "ru2", "ru3"):
                if n in exclude_nodes: continue
                d = pmc_get(n, "PARENT_DATA_SET", "PORT_DATA_SET")
                res[n] = (ident(d.get("parentPortIdentity", "")) in ok_ids
                          and ident(d.get("grandmasterIdentity", "")) in self.prov["gm_allowlist"]
                          and d.get("portState") in ("SLAVE", "UNCALIBRATED"))
            if res and all(res.values()):
                return True, res
            time.sleep(VERIFY_POLL_S)
        return False, res

    def node_of_port(self, port):
        return {"p-v-ru1": "ru1", "p-v-ru2": "ru2", "p-v-ru3": "ru3"}.get(port)

    def execute(self, rec, undo, exclude_nodes):
        rec["t_decided_rel"] = round(mono() - self.t0, 3)
        self.actions.append(rec)
        if self.args.mode != "act":
            self.log("would_act", **rec); return
        self.log("act", **rec)
        ok, detail = self.verify(exclude_nodes)
        self.log("verify", ok=ok, detail=detail, action=rec["action"], target=rec["target"])
        if not ok:
            undo()
            self.log("rollback", action=rec["action"], target=rec["target"])
            self.escalate("verification failed after " + rec["action"])

    def escalate(self, why):
        if why in self.escalated: return
        self.escalated.add(why)
        self.log("escalate", reason=why)

    # ---- main ----
    def run(self):
        self.cap.start()
        self.log("start", provisioning=self.args.provisioning, state=self.state,
                 params=dict(WINDOW_S=WINDOW_S, EVAL_PERIOD_S=EVAL_PERIOD_S, PERSIST=f"{PERSIST_K}/{PERSIST_N}",
                             WARMUP_S=WARMUP_S, SERVICE_LOSS_S=SERVICE_LOSS_S,
                             SERVICE_LOSS_MAINT_S=SERVICE_LOSS_MAINT_S, VERIFY_DEADLINE_S=VERIFY_DEADLINE_S))
        end = self.t0 + self.args.duration
        nxt = self.t0 + EVAL_PERIOD_S
        while mono() < end:
            time.sleep(max(0.0, nxt - mono())); nxt += EVAL_PERIOD_S
            now = mono()
            if now - self.t0 < WARMUP_S:
                continue
            res = self.evaluate(now)
            if res is None:
                self.log("eval", verdict="NO_EVIDENCE"); self.hist.append(None)
            else:
                self.log("eval", **res); self.hist.append(res)
            self.decide(now, res)
        self.cap.stop_flag = True
        self.log("end", actions=self.actions, isolated=sorted(self.isolated),
                 standby_active=self.standby_active, escalations=sorted(self.escalated))

    def decide(self, now, res):
        if len(self.actions) >= MAX_ACTIONS or mono() >= self.t0 + self.args.duration:
            return
        # channel 2: timing-service continuity (consequence-driven, intent-independent)
        if not self.standby_active:
            mports = self.master_ports() - {"p-bcs-dn"}
            last = max([self.cap.last_announce_from.get(p, 0.0) for p in mports] + [0.0])
            limit = SERVICE_LOSS_MAINT_S if self.state.get("maintenance_window_open") else SERVICE_LOSS_S
            if last > 0 and now - last > limit:
                rec = self.act_failover(f"no Announce from any provisioned master port for "
                                        f"{now-last:.1f}s (> {limit}s): timing service lost on segment")
                self.execute(rec, self.undo_failover, exclude_nodes=set())
                return
        if res is None:
            return
        # channel 1: frozen rule verdicts, with persistence
        votes = [h for h in self.hist if h and h["verdict"] == "ATTACK"]
        if res["verdict"] == "UNKNOWN":
            self.escalate(f"UNKNOWN: {res['reason'][:120]}")
        if len(votes) < PERSIST_K or res["verdict"] != "ATTACK":
            return
        if res["violations"] and set(res["violations"]) <= self.isolated:
            return          # every violating port is already contained; window still holds pre-isolation frames
        targets = {p: w for p, w in res["violations"].items() if p not in self.isolated}
        # SAFETY GUARD: a port provisioned in the master role (primary BC, standby BC, planned
        # replacement BC) is never isolated automatically - isolating it would itself remove the
        # timing service. Such cases are escalated to the operator instead.
        guarded = {p: w for p, w in targets.items()
                   if self.inventory.get(p, {}).get("role") == "master"}
        for p in guarded: del targets[p]
        if not targets:
            self.escalate(f"ATTACK ({res['hint']}) with no isolatable violating port"
                          + (f"; guard held master-role ports {sorted(guarded)}" if guarded else ""))
            return
        for p, why in targets.items():
            rec = self.act_isolate(p, f"rule={res['hint']}; port violations: {why}")
            node = self.node_of_port(p)
            self.execute(rec, lambda p=p: self.undo_isolate(p), exclude_nodes={node} if node else set())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["act", "observe"], required=True)
    ap.add_argument("--provisioning", default=os.path.join(HERE, "provisioning.json"))
    ap.add_argument("--state", required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--log", required=True)
    Loop(ap.parse_args()).run()

if __name__ == "__main__":
    main()
