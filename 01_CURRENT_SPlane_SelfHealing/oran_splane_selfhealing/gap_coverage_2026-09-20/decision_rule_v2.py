#!/usr/bin/env python3
"""
decision_rule_v2 -- UNFROZEN DEVELOPMENT EXTENSION.  NOT a frozen artefact.
===========================================================================
This file is NOT decision_rule.py and does NOT replace it. The frozen rule
(sha256 c362e11072344161437aaae33b2902caf9bca57dfc33f653a9c2184edae8a985) is
imported UNCHANGED and used as the base layer. v2 only ADDS three detectors
for classes the frozen rule was shown to miss on crafted inputs:
    D1  packet removal / selective interception   (O-RAN WG11 11.1.5.3.1)
    D2  malformed / fuzzed PTP frames             (O-RAN WG11 24.2.1.2)
    D3  whole-second field abuse (leap/UTC/trace) (IEEE 1588-2019 7.2.4)

Design contract:
  * ADDITIVE ONLY. v2 never turns a frozen ATTACK into BENIGN. It escalates a
    frozen BENIGN/UNKNOWN to ATTACK only when a new detector fires. So on any
    input the frozen rule already calls ATTACK, v2 == frozen.
  * Every new constant is fixed by a standard (cited inline) or is self-
    referential (compared to what the sender itself declares) -- no value is
    fitted to the crafted inputs.
  * These detectors are validated here by DETECTION-LOGIC tests on crafted
    inputs plus a false-positive check against real healthy captures. They are
    NOT yet validated on live on-wire runs and this file is NOT frozen. Using
    them in a reported result requires re-freeze + a fresh randomized campaign.
"""
from __future__ import annotations
import csv, collections, os, importlib.util, hashlib, json, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("frozen_dr", os.path.join(_HERE,"decision_rule.py"))
frozen = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(frozen)

VERDICT_ATTACK, VERDICT_BENIGN, VERDICT_UNKNOWN = "ATTACK","BENIGN","UNKNOWN"

# --- legality constants, all fixed by standards ---
PTP_VERSION            = 2       # IEEE 1588-2019: versionPTP field value 2
CONTROL_FIELD_MAX      = 5       # IEEE 1588 Table 23: legal control values 0..5
LEGAL_MSGTYPE_RAW      = {"0","1","2","3","8","9","10","11","12","13"}  # 1588-2019 Table 5
MIN_LEN = {"Announce":64,"Sync":44,"Follow_Up":44,"Delay_Req":44,"Delay_Resp":54,
           "Pdelay_Req":54,"Pdelay_Resp":54}  # 1588-2019 header(34)+body minima
RATE_STARVE_FRACTION   = 0.5     # observed < 0.5x the sender's OWN declared rate = loss
TRUE_TAI_UTC_OFFSET    = 37      # since 2017-01-01; ctx may override via 'true_utc_offset'
MALFORMED_MIN_COUNT    = 10      # >=10 malformed frames (or >0.5%) = sustained, not a glitch

def _to_int(x):
    try: return int(x)
    except Exception: return None

def detect_removal(rows, ctx, ev):
    """D1: a provisioned source delivering Sync far below the rate it itself declares."""
    ts=[int(r["capture_ts_ns"]) for r in rows if r.get("capture_ts_ns")]
    if len(ts)<2: return None
    span=(max(ts)-min(ts))/1e9
    if span<=2.0: return None
    known = set(ctx.get("gm_allowlist",[])) | {ctx.get("expected_bc_identity")} \
            | set(ctx.get("expected_client_identities",[]))
    findings={}
    for mtype in ("Sync","Announce"):
        per=collections.defaultdict(list)
        for r in rows:
            if r.get("message_type")==mtype and r.get("source_clock_identity"):
                per[r["source_clock_identity"]].append(r)
        for sid,frames in per.items():
            if sid not in known: continue          # unknown source is the frozen rule's job
            decl=[_to_int(f.get("log_message_interval")) for f in frames]
            decl=[d for d in decl if d is not None]
            if not decl: continue
            declared_hz=2.0**(-sorted(decl)[len(decl)//2])   # median declared
            obs_hz=len(frames)/span
            if declared_hz>0 and obs_hz < RATE_STARVE_FRACTION*declared_hz:
                findings[f"{sid}/{mtype}"]=dict(observed_hz=round(obs_hz,2),
                    declared_hz=round(declared_hz,2), n=len(frames))
    ev["D1_rate_starvation"]=findings
    if findings:
        return ("A_intercept", f"Provisioned source delivering far below its own declared "
                f"rate -> packet removal / selective interception: {findings}")
    return None

def detect_malformed(rows, ev):
    """D2: frames violating IEEE 1588-2019 field legality."""
    bad=collections.Counter()
    examples={}
    for r in rows:
        reasons=[]
        v=_to_int(r.get("version_ptp"))
        if v is not None and v!=PTP_VERSION: reasons.append("version!=2")
        cf=_to_int(r.get("control_field"))
        if cf is not None and cf>CONTROL_FIELD_MAX: reasons.append("control>5")
        mtr=r.get("message_type_raw")
        if mtr not in ("",None) and mtr not in LEGAL_MSGTYPE_RAW: reasons.append("msgtype_raw illegal")
        ml=_to_int(r.get("message_length")); mt=r.get("message_type")
        if ml is not None and mt in MIN_LEN and ml<MIN_LEN[mt]: reasons.append("length<min")
        if reasons:
            for x in reasons: bad[x]+=1
            examples.setdefault(tuple(reasons), dict(r))
    total=len(rows) or 1
    n_bad=sum(1 for r in rows if any([
        (_to_int(r.get("version_ptp")) not in (None,PTP_VERSION)),
        (_to_int(r.get("control_field")) is not None and _to_int(r.get("control_field"))>CONTROL_FIELD_MAX),
        (r.get("message_type_raw") not in ("",None) and r.get("message_type_raw") not in LEGAL_MSGTYPE_RAW),
        (_to_int(r.get("message_length")) is not None and r.get("message_type") in MIN_LEN
             and _to_int(r.get("message_length"))<MIN_LEN[r.get("message_type")]),
    ]))
    ev["D2_malformed_reasons"]=dict(bad); ev["D2_malformed_frames"]=n_bad
    if n_bad>=MALFORMED_MIN_COUNT or n_bad>0.005*total:
        return ("A_malformed", f"IEEE 1588-2019 field-legality violations in {n_bad} frames: {dict(bad)}")
    return None

def detect_wholesecond(rows, ctx, ev):
    """D3: leap/UTC-offset/traceability abuse in Announce."""
    ann=[r for r in rows if r.get("message_type")=="Announce"]
    if not ann: return None
    leap_ok = bool(ctx.get("leap_window_open", False))
    true_utc = ctx.get("true_utc_offset", TRUE_TAI_UTC_OFFSET)
    findings=[]
    # (a) spurious leap flag outside a provisioned leap window
    leap=[r for r in ann if r.get("flag_leap61")=="1" or r.get("flag_leap59")=="1"]
    if leap and not leap_ok:
        findings.append(f"leap61/59 asserted in {len(leap)} Announce with no leap window open")
    # (b) currentUtcOffset not constant, or != true offset while declared valid
    per=collections.defaultdict(set)
    wrong_valid=0
    for r in ann:
        u=_to_int(r.get("current_utc_offset"))
        if u is None: continue
        per[r.get("source_clock_identity")].add(u)
        if r.get("flag_currentUtcOffsetValid")=="1" and u!=true_utc: wrong_valid+=1
    stepped={s:sorted(v) for s,v in per.items() if len(v)>1}
    if stepped: findings.append(f"currentUtcOffset not constant per source: {stepped}")
    if wrong_valid: findings.append(f"{wrong_valid} Announce assert UTCOffsetValid but offset!={true_utc}")
    # (c) a clock claiming traceable class (<=6) but deasserting traceability
    incon=[r for r in ann if (_to_int(r.get("gm_clock_class")) is not None
           and _to_int(r.get("gm_clock_class"))<=6
           and (r.get("flag_timeTraceable")=="0" or r.get("flag_currentUtcOffsetValid")=="0"))]
    if incon: findings.append(f"{len(incon)} Announce claim traceable clockClass<=6 but deassert "
                              f"timeTraceable/currentUtcOffsetValid")
    ev["D3_wholesecond"]=findings
    if findings:
        return ("A_wholesecond", "Timescale/whole-second metadata abuse: " + "; ".join(findings))
    return None

def decide_v2(deep_csv, ctx):
    # base layer: the FROZEN rule, unchanged
    v,hint,why,ev = frozen.decide(deep_csv, ctx)
    ev["v2_base_verdict"]=v
    if v==VERDICT_ATTACK:
        return v,hint,why,ev            # additive-only: never soften a frozen ATTACK
    try:
        rows=list(csv.DictReader(open(deep_csv)))
    except Exception:
        return v,hint,why,ev
    for det in (lambda: detect_removal(rows,ctx,ev),
                lambda: detect_malformed(rows,ev),
                lambda: detect_wholesecond(rows,ctx,ev)):
        hit=det()
        if hit:
            new_hint,reason=hit
            return VERDICT_ATTACK, new_hint, [reason]+["(v2 detector; frozen base said "+v+")"], ev
    return v,hint,why,ev

def _frozen_hash_ok():
    frz=json.load(open(os.path.join(_HERE,"..","FROZEN.json"))) if os.path.exists(os.path.join(_HERE,"..","FROZEN.json")) else None
    h=hashlib.sha256(open(os.path.join(_HERE,"decision_rule.py"),"rb").read()).hexdigest()
    return h, (frz["artifacts"]["run/decision_rule.py"]["sha256"] if frz else None)

if __name__=="__main__":
    run_dir=sys.argv[1]; deep=sys.argv[2]
    ctx=json.load(open(os.path.join(run_dir,"context.json")))
    v,hint,why,ev=decide_v2(deep,ctx)
    print(json.dumps(dict(verdict=v,hint=hint,reasons=why),indent=2))
