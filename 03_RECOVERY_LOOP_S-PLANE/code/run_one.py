#!/usr/bin/env python3
"""One recovery-loop run: run_one.py <scenario> <rep> <arm: control|loop>

Re-uses the frozen 168-run campaign harness unchanged (topology.sh, start.sh, stop.sh,
clean_all.sh, cfg/*, inject.py, flood.py, inject_malformed.py, inject_wholesecond.py,
bg_traffic.py, randparams.py) and the same fault mechanisms as scenarios.sh / run_gap.sh.

Differences from the campaign, all deliberate and recorded in PREREGISTRATION.md:
  * a cold-standby boundary clock 'bcs' (identity 020000fffe0000c5) is cabled to both bridges in
    EVERY run of BOTH arms; its daemon is started only if the loop executes a failover;
  * the fault starts at T0 = 20 s and PERSISTS to the end of the run (no restore tail), because
    the question here is whether service is restored while the attacker is still present;
  * the loop (act) or the identical loop in observe-only mode (control) runs from t = 0.
"""
import json, os, subprocess, sys, time

SPTB = "/opt/sptb"; RL = f"{SPTB}/recovery"
SC, REP, ARM = sys.argv[1], int(sys.argv[2]), sys.argv[3]
T0_S, END_S = 20.0, 60.0
RUN = f"{SC}__r{REP}__{ARM}"
OUT = f"{SPTB}/cap/{RUN}"

def sh(cmd, check=False, bg=False):
    if bg:
        return subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stderr}")
    return r

P = json.loads(sh(f"python3 {SPTB}/run/randparams.py {REP}", check=True).stdout)
MAINT = SC in ("B2_gm_failover", "B7_topology_change", "B_bc_replacement")
CLASS = ("healthy" if SC == "baseline" else "attack" if SC[0] in "AC" else "benign")

def clean():
    sh(f"bash {SPTB}/run/clean_all.sh")
    sh("pkill -f 'recovery_loop.py|observer.py|inject|flood.py|bg_traffic.py|tcpreplay' ; true")
    for n in ("bcs", "rogue", "rbc", "bc2"):
        sh(f"ip netns del {n} 2>/dev/null; true")
    sh("nft delete table bridge rl 2>/dev/null; true")
    for l in ("v-bcs-up", "v-bcs-dn", "p-bcs-up", "p-bcs-dn"):
        sh(f"ip link del {l} 2>/dev/null; true")

def add_dev(ns, ports):
    sh(f"ip netns add {ns}", check=True)
    for ifn, br, mac in ports:
        sh(f"ip link add {ifn} type veth peer name p-{ifn[2:]} && ip link set p-{ifn[2:]} master {br} && "
           f"ip link set p-{ifn[2:]} up && ip link set {ifn} netns {ns} && "
           f"ip netns exec {ns} ip link set {ifn} address {mac} && ip netns exec {ns} ip link set {ifn} up", check=True)
    sh(f"ip netns exec {ns} ip link set lo up")

def base_cfg(extra):
    return open(f"{SPTB}/cfg/g87251.base").read() + extra

clean()
os.makedirs(OUT, exist_ok=True)
sh(f"bash {SPTB}/run/topology.sh", check=True)
# cold-standby boundary clock: cabled, configured, daemon NOT started (both arms)
add_dev("bcs", [("v-bcs-up", "brUP", "02:00:00:00:00:c5"), ("v-bcs-dn", "brDN", "02:00:00:00:00:c6")])
open(f"{SPTB}/cfg/bcs.cfg", "w").write(base_cfg(
    "\npriority2                       125\n[v-bcs-up]\nserverOnly                      0\n"
    "[v-bcs-dn]\nserverOnly                      1\n"))

state = {"maintenance_window_open": MAINT,
         "planned_replacement": ({"port": "p-bc2-dn", "identity": "020000fffe0000b1"}
                                 if SC == "B_bc_replacement" else None)}
json.dump(state, open(f"{OUT}/state.json", "w"), indent=2)
ctx = {"scenario": SC, "class": CLASS, "rep": REP, "arm": ARM,
       "gm_allowlist": ["020000fffe00000a", "020000fffe00000b"], "provisioned_backup_gm": "020000fffe00000b",
       "expected_bc_identity": "020000fffe000001",
       "expected_client_identities": ["020000fffe00000c", "020000fffe00000d", "020000fffe00000e"],
       "expected_steps_removed_at_ru": 1, "maintenance_window_open": MAINT, "randomised_params": P}
if SC == "B_bc_replacement":
    ctx["expected_bc_identity_secondary"] = "020000fffe0000b1"
json.dump(ctx, open(f"{OUT}/context.json", "w"), indent=2)

sh(f"bash {SPTB}/run/start.sh {RUN} >{OUT}/start.log 2>&1 </dev/null", check=True)
t_start = time.monotonic()
obs = sh(f"python3 {RL}/observer.py {OUT}/observer.jsonl {END_S + 2}", bg=True)
mode = "act" if ARM == "loop" else "observe"
loop = sh(f"python3 {RL}/recovery_loop.py --mode {mode} --state {OUT}/state.json --duration {END_S} "
          f"--outdir {OUT} --log {OUT}/loop.jsonl", bg=True)

def at(t):
    time.sleep(max(0.0, t_start + t - time.monotonic()))

tl = {"t_start_mono": round(t_start, 3)}
if SC == "A3_replay":     # capture the frames to be replayed before T0 (same mechanism as campaign)
    at(T0_S - 12)
    sh(f"timeout 10 tcpdump -i brDN -w {OUT}/replay_src.pcap -s0 -c {P['replay_count']} 2>/dev/null; true")
at(T0_S)
tl["t0_mono"] = round(time.monotonic(), 3)
DUR_ATT = int(END_S - T0_S) + 2
procs = []
if SC == "A1_rogue_master":
    open(f"{SPTB}/cfg/rogue.cfg", "w").write(base_cfg(
        f"\npriority2                       {P['rogue_priority2']}\nclockClass                      {P['rogue_clockclass']}\n"
        f"[v-rogue]\nserverOnly                      1\n"))
    add_dev("rogue", [("v-rogue", "brDN", P["rogue_mac"])])
    procs.append(sh(f"ip netns exec rogue ptp4l -f {SPTB}/cfg/rogue.cfg -i v-rogue -m >{OUT}/rogue.log 2>&1", bg=True))
elif SC == "A2_sync_spoof":
    procs.append(sh(f"ip netns exec ru3 python3 {SPTB}/run/inject.py v-ru3 sync {DUR_ATT} {P['inject_id']} "
                    f"{P['inject_burst']} {P['inject_gap_ms']} {P['inject_seconds']} >{OUT}/inject.log 2>&1", bg=True))
elif SC == "A3_replay":
    procs.append(sh(f"ip netns exec ru3 tcpreplay -i v-ru3 --loop={P['replay_loops']} {OUT}/replay_src.pcap "
                    f">{OUT}/replay.log 2>&1", bg=True))
elif SC == "A5_dos_flood":
    procs.append(sh(f"ip netns exec ru3 python3 {SPTB}/run/flood.py v-ru3 {DUR_ATT} {P['flood_burst']} "
                    f"{P['flood_gap_ms']} {P['flood_src']} >{OUT}/flood.log 2>&1", bg=True))
elif SC == "A8_rogue_bc":
    open(f"{SPTB}/cfg/rbc.cfg", "w").write(base_cfg(
        f"\npriority2                       {P['rbc_priority2']}\n[v-rbc-up]\nserverOnly                      0\n"
        f"[v-rbc-dn]\nserverOnly                      1\n"))
    add_dev("rbc", [("v-rbc-up", "brUP", P["rbc_up_mac"]), ("v-rbc-dn", "brDN", P["rbc_dn_mac"])])
    procs.append(sh(f"ip netns exec rbc ptp4l -f {SPTB}/cfg/rbc.cfg -i v-rbc-up -i v-rbc-dn -m >{OUT}/rbc.log 2>&1", bg=True))
elif SC == "C1_removal":   # sustained blackhole of the BC downstream port, NOT restored
    sh("ip netns exec bc ip link set v-bc-dn down")
elif SC == "C2_malformed":
    procs.append(sh(f"ip netns exec ru3 python3 {SPTB}/run/inject_malformed.py v-ru3 {DUR_ATT} 020000fffe00000a "
                    f"{P['c2_gap_ms']} >{OUT}/inject.log 2>&1", bg=True))
elif SC == "C3_wholesecond":
    procs.append(sh(f"ip netns exec ru3 python3 {SPTB}/run/inject_wholesecond.py v-ru3 {DUR_ATT} 020000fffe00000a "
                    f"{P['c3_gap_ms']} >{OUT}/inject.log 2>&1", bg=True))
elif SC == "B2_gm_failover":
    sh(f"kill $(cat {OUT}/gma.pid)")
elif SC == "B_unplanned_failover":
    sh(f"kill -9 $(cat {OUT}/gma.pid)")
elif SC == "B_bc_replacement":
    sh(f"kill $(cat {OUT}/bc.pid)")
    open(f"{SPTB}/cfg/bc2.cfg", "w").write(base_cfg(
        "\npriority2                       120\n[v-bc2-up]\nserverOnly                      0\n"
        "[v-bc2-dn]\nserverOnly                      1\n"))
    add_dev("bc2", [("v-bc2-up", "brUP", "02:00:00:00:00:b1"), ("v-bc2-dn", "brDN", "02:00:00:00:00:b2")])
    procs.append(sh(f"ip netns exec bc2 ptp4l -f {SPTB}/cfg/bc2.cfg -i v-bc2-up -i v-bc2-dn -m "
                    f"--uds_address=/var/run/p.bc2 --uds_ro_address=/var/run/pr.bc2 >{OUT}/bc2.log 2>&1", bg=True))
elif SC == "B3_pdv_congestion":
    burst = (P["pdv_delay_ms"] + 5) // 2; gap = 100 - 15 * P["pdv_jitter_ms"]
    r = sh("ip netns exec bc tc qdisc add dev v-bc-dn root tbf rate 1mbit burst 3000 limit 40000")
    open(f"{OUT}/impair.log", "w").write(f"tbf rc={r.returncode} {r.stderr}; bg burst={burst} gap={gap}ms\n")
    procs.append(sh(f"ip netns exec bc python3 {SPTB}/run/bg_traffic.py v-bc-dn {DUR_ATT} {burst} {gap} >>{OUT}/impair.log 2>&1", bg=True))
elif SC == "B7_topology_change":
    sh("ip netns exec ru3 ip link set v-ru3 down"); time.sleep(8); sh("ip netns exec ru3 ip link set v-ru3 up")
elif SC == "baseline":
    pass
else:
    raise SystemExit(f"unknown scenario {SC}")
tl["t_inject_done_mono"] = round(time.monotonic(), 3)
at(END_S + 1)
loop.wait(timeout=30); obs.wait(timeout=10)
tl["t_end_mono"] = round(time.monotonic(), 3)
for p in procs:
    p.terminate()
sh(f"nft list ruleset > {OUT}/nft_final.txt 2>&1; true")
sh(f"bash {SPTB}/run/stop.sh {RUN} >/dev/null 2>&1 </dev/null")
sh(f"[ -f {OUT}/bcs.pid ] && kill $(cat {OUT}/bcs.pid); true")
json.dump(tl, open(f"{OUT}/timeline.json", "w"), indent=2)
clean()
sh(f"cd {OUT} && gzip -f up.pcap dn.pcap 2>/dev/null; true")
print(f"{RUN} done")
