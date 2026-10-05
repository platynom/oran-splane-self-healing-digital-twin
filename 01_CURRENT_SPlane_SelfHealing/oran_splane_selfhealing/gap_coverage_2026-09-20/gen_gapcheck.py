#!/usr/bin/env python3
"""
COVERAGE-GAP CRAFTED-INPUT GENERATOR  (NOT a live on-wire capture)
-----------------------------------------------------------------
Builds a synthetic G.8275.1-conformant BENIGN baseline deep.csv and three
perturbed variants, one per un-run coverage item:
  item1  packet removal / selective interception   (O-RAN WG11 11.1.5.3.1)
  item2  malformed / fuzzed PTP frames              (O-RAN WG11 24.2.1.2)
  item3  whole-second field abuse (leap/UTC/trace)  (IEEE 1588-2019 7.2.4)

Each variant differs from the baseline by EXACTLY the injected signature, so a
BENIGN verdict on a variant isolates the frozen rule's blindness to that class.
This is a detection-logic fixture, clearly labelled; it is not captured traffic
and does not re-freeze or replace any frozen artefact.
"""
import csv, os, json, random

random.seed(1588)  # deterministic fixture

COLS = ["capture_ts_ns","eth_src","eth_dst","vlan_id","vlan_pcp","message_type",
"message_type_raw","version_ptp","minor_version_ptp","message_length","domain_number",
"major_sdo_id","minor_sdo_id","flag_field_hex","flag_alternateMaster","flag_twoStep",
"flag_unicast","flag_profileSpecific1","flag_profileSpecific2","flag_leap61","flag_leap59",
"flag_currentUtcOffsetValid","flag_ptpTimescale","flag_timeTraceable","flag_frequencyTraceable",
"flag_syncUncertain","correction_ns","source_clock_identity","source_port_number","sequence_id",
"control_field","log_message_interval","origin_ts_ns","current_utc_offset","gm_priority1",
"gm_clock_class","gm_clock_accuracy","gm_offset_scaled_log_variance","gm_priority2",
"gm_clock_identity","steps_removed","time_source","tlv_types","has_path_trace","path_trace_hops",
"requesting_clock_identity","requesting_port_number","clock_class_legal","bmca_fields_all_zero",
"gm_identity_equals_source","g87251_domain_ok","g87251_mcast_ok","g87251_priority1_ok",
"g87251_log_sync_ok","g87251_log_announce_ok","g87251_log_delayreq_ok"]

# provisioned inventory (matches results/runs/baseline__r32/context.json)
GM   = "020000fffe00000a"
BC   = "020000fffe000001"
CLIENTS = ["020000fffe00000c","020000fffe00000d","020000fffe00000e"]
MCAST = "011b19000000"
CONTROL = {"Sync":"0","Delay_Req":"1","Follow_Up":"2","Delay_Resp":"3","Announce":"5"}
MTRAW   = {"Sync":"0","Delay_Req":"1","Follow_Up":"8","Delay_Resp":"9","Announce":"11"}
MLEN    = {"Announce":"64","Sync":"44","Follow_Up":"44","Delay_Req":"44","Delay_Resp":"54"}

def row(**k):
    r = {c:"" for c in COLS}
    # conformant defaults
    r.update(dict(vlan_id="0",vlan_pcp="0",version_ptp="2",minor_version_ptp="0",
        domain_number="24",major_sdo_id="0",minor_sdo_id="0",flag_alternateMaster="0",
        flag_twoStep="1",flag_unicast="0",flag_profileSpecific1="0",flag_profileSpecific2="0",
        flag_leap61="0",flag_leap59="0",flag_currentUtcOffsetValid="1",flag_ptpTimescale="1",
        flag_timeTraceable="1",flag_frequencyTraceable="1",flag_syncUncertain="0",
        correction_ns="0",eth_dst=MCAST,current_utc_offset="37",time_source="32",
        tlv_types="",has_path_trace="0",path_trace_hops="0",
        g87251_domain_ok="1",g87251_mcast_ok="1"))
    r.update(k)
    return r

def eth_of(cid):  # last 6 hex of clock id as MAC-ish src
    return cid[-12:] if len(cid)>=12 else "020000"+cid[-6:]

def announce(ts,src,gm,steps,seq,port="1"):
    return row(capture_ts_ns=str(ts),eth_src=eth_of(src),message_type="Announce",
        message_type_raw=MTRAW["Announce"],message_length=MLEN["Announce"],
        source_clock_identity=src,source_port_number=port,sequence_id=str(seq),
        control_field=CONTROL["Announce"],log_message_interval="-3",
        gm_priority1="128",gm_clock_class="6",gm_clock_accuracy="33",
        gm_offset_scaled_log_variance="20061",gm_priority2="128",gm_clock_identity=gm,
        steps_removed=str(steps),clock_class_legal="1",bmca_fields_all_zero="0",
        gm_identity_equals_source=("1" if gm==src else "0"),
        g87251_priority1_ok="1",g87251_log_announce_ok="1")

def sync(ts,src,seq,port="1"):
    return row(capture_ts_ns=str(ts),eth_src=eth_of(src),message_type="Sync",
        message_type_raw=MTRAW["Sync"],message_length=MLEN["Sync"],
        source_clock_identity=src,source_port_number=port,sequence_id=str(seq),
        control_field=CONTROL["Sync"],log_message_interval="-4",origin_ts_ns=str(ts),
        g87251_log_sync_ok="1")

def followup(ts,src,seq,port="1"):
    return row(capture_ts_ns=str(ts),eth_src=eth_of(src),message_type="Follow_Up",
        message_type_raw=MTRAW["Follow_Up"],message_length=MLEN["Follow_Up"],
        source_clock_identity=src,source_port_number=port,sequence_id=str(seq),
        control_field=CONTROL["Follow_Up"],log_message_interval="-4",origin_ts_ns=str(ts),
        g87251_log_sync_ok="1")

def delayreq(ts,src,seq,port="1"):
    return row(capture_ts_ns=str(ts),eth_src=eth_of(src),message_type="Delay_Req",
        message_type_raw=MTRAW["Delay_Req"],message_length=MLEN["Delay_Req"],
        source_clock_identity=src,source_port_number=port,sequence_id=str(seq),
        control_field=CONTROL["Delay_Req"],log_message_interval="-4",origin_ts_ns=str(ts),
        g87251_log_delayreq_ok="1")

def delayresp(ts,src,req_id,seq,port="1"):
    return row(capture_ts_ns=str(ts),eth_src=eth_of(src),message_type="Delay_Resp",
        message_type_raw=MTRAW["Delay_Resp"],message_length=MLEN["Delay_Resp"],
        source_clock_identity=src,source_port_number=port,sequence_id=str(seq),
        control_field=CONTROL["Delay_Resp"],log_message_interval="0",
        requesting_clock_identity=req_id,requesting_port_number="1",g87251_log_delayreq_ok="1")

def build_base(span_s=30):
    """G.8275.1 nominal: GM announces(8/s)+syncs(16/s); BC relays announce(8/s,steps1);
    clients Delay_Req(8/s); BC answers Delay_Resp echoing requester seq."""
    rows=[]
    NS=1_000_000_000
    t0=1_700_000_000*NS
    # GM announce 8/s, sync+followup 16/s (steps 0, self-announce)
    for i in range(span_s*8):
        rows.append(announce(t0+i*(NS//8), GM, GM, 0, i))
    for i in range(span_s*16):
        rows.append(sync(t0+i*(NS//16), GM, i))
        rows.append(followup(t0+i*(NS//16)+50_000, GM, i))
    # BC relays announce downstream 8/s, steps 1, port 2
    for i in range(span_s*8):
        rows.append(announce(t0+i*(NS//8)+10_000, BC, GM, 1, i, port="2"))
    # clients Delay_Req 8/s each; BC Delay_Resp echoes
    for ci,cl in enumerate(CLIENTS):
        for i in range(span_s*8):
            ts=t0+i*(NS//8)+20_000+ci*1000
            rows.append(delayreq(ts, cl, i))
            rows.append(delayresp(ts+30_000, BC, cl, i, port="2"))
    rows.sort(key=lambda r:int(r["capture_ts_ns"]))
    return rows

def write_csv(path,rows):
    with open(path,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLS); w.writeheader(); w.writerows(rows)

OUT="/tmp/rulewk/gapcheck"
base=build_base()
write_csv(f"{OUT}/synth_base.deep.csv", base)

# --- item1: packet removal / selective interception ---
# on-path attacker drops 70% of Sync/Follow_Up/Delay_Resp; Announce untouched.
import copy
def item1(rows):
    out=[]
    for r in rows:
        if r["message_type"] in ("Sync","Follow_Up","Delay_Resp") and random.random()<0.70:
            continue
        out.append(r)
    return out
write_csv(f"{OUT}/synth_item1_removal.deep.csv", item1(copy.deepcopy(base)))

# --- item2: malformed / fuzzed frames from the provisioned GM ---
# corrupt version (must be 2), message_length (impossible), control_field (>5).
def item2(rows):
    out=copy.deepcopy(rows)
    n=0
    for r in out:
        if r["source_clock_identity"]==GM and r["message_type"] in ("Announce","Sync") and n<200:
            r["version_ptp"]="3"          # IEEE1588-2019: versionPTP MUST be 2
            r["message_length"]="20"      # shorter than mandatory header+body
            r["control_field"]="99"       # outside legal 0-5
            r["message_type_raw"]="15"    # 0xF is reserved/undefined
            n+=1
    return out
write_csv(f"{OUT}/synth_item2_malformed.deep.csv", item2(base))

# --- item3: whole-second field abuse on GM Announce ---
# spurious leap61, wrong currentUtcOffset, traceability stripped while clockClass=6.
def item3(rows):
    out=copy.deepcopy(rows)
    for r in out:
        if r["source_clock_identity"]==GM and r["message_type"]=="Announce":
            r["flag_leap61"]="1"                  # spurious leap-second announcement
            r["current_utc_offset"]="0"           # wrong (true TAI-UTC=37)
            r["flag_timeTraceable"]="0"           # stripped
            r["flag_currentUtcOffsetValid"]="0"   # stripped; clockClass still claims 6
    return out
write_csv(f"{OUT}/synth_item3_wholesecond.deep.csv", item3(base))

# shared provisioned context
ctx=dict(scenario="synthetic_g87251_baseline", **{"class":"healthy"}, fault_id="none",
    gm_allowlist=[GM,"020000fffe00000b"], provisioned_backup_gm="020000fffe00000b",
    expected_bc_identity=BC, expected_client_identities=CLIENTS,
    expected_steps_removed_at_ru=1, maintenance_window_open=False, leap_window_open=False)
json.dump(ctx, open(f"{OUT}/context.json","w"), indent=2)

import collections
for f in ["synth_base","synth_item1_removal","synth_item2_malformed","synth_item3_wholesecond"]:
    rr=list(csv.DictReader(open(f"{OUT}/{f}.deep.csv")))
    mt=collections.Counter(r["message_type"] for r in rr)
    print(f"{f}: {len(rr)} rows  {dict(mt)}")
