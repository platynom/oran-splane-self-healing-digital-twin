#!/usr/bin/env python3
"""
FROZEN decision rule: benign-fault vs attack on the O-RAN S-plane.

INTEGRITY CONTRACT
------------------
* Contains NO tunable parameter. Every constant below is either fixed by a standard
  (cited inline) or is provisioned configuration read from the run's context.json.
* DEVELOPMENT SET (already seen, may NOT be used as evidence):
      baseline, A1_rogue_master, B2_gm_failover, B3_pdv_congestion  (1 run each)
  The BC-identity term was added after observing those four. They are therefore a
  development set by construction and are excluded from any reported result.
* VALIDATION = runs produced AFTER this file is hashed by run/freeze.sh.
* DEVELOPMENT ADDENDUM (rep 1, all 9 scenarios): rep-1 runs exposed a defect in this
  rule - the sequenceId counter was keyed by the responding source for Delay_Resp, but
  IEEE 1588 has Delay_Resp echo the REQUESTER's sequenceId, so a master answering
  several clients produced 799 false "regressions" on a healthy baseline. Fixed below.
  All rep-1 runs are therefore development data and are EXCLUDED from reported results.
* DEVELOPMENT ADDENDUM (rep 2): two further defects found. (a) the transient filter was
  applied to off-allow-list grandmasters but NOT to provisioned ones, so a standby GM
  announcing once at start-up (1 of 356) forced UNKNOWN on a healthy baseline;
  (b) the allow-list inspected only grandmasterIdentity, so a Sync-only injector that
  never sends Announce (1,800 forged Sync from 020000fffe0000aa) was invisible.
  Both fixed. ALL rep-2 runs are development data and are EXCLUDED.
* DEVELOPMENT ADDENDUM (reps 3-7): those reps showed the binary call was correct 45/45 but
  A5 and A8 were both ATTRIBUTED to "A1". Root cause was a SCENARIO defect, not a rule
  defect: A8 had been built as a single-port SELF-ANNOUNCING master, structurally identical
  to A1. A8 is now a genuine two-port boundary clock that slaves upstream and RELAYS the
  real grandmaster downstream with stepsRemoved incremented. The rule now orders decisions
  by what DEFINES each fault (rate -> A5, sequence reuse -> A3, relay -> A8, self-announce
  -> A1, timing-without-Announce -> A2). ALL reps 3-7 are development data and are EXCLUDED.

Standards basis
---------------
  ITU-T G.8275.1 : domain 24-43; priority1 fixed 128; logSync -4; logAnnounce -3;
                   dst MAC 01-1B-19-00-00-00 / 01-80-C2-00-00-0E
  IEEE 1588-2019 : Table 5 - clockClass 0-5 are RESERVED (illegal in an Announce)
                   cl.13.3.2.14 - logMessageInterval 0x7F = "unspecified" (legal for Delay_Req)
Provisioned context (NOT a threshold - it is operator configuration):
  gm_allowlist, expected_bc_identity, maintenance_window_open
"""
from __future__ import annotations
import csv, json, collections, sys, os

# --- constants fixed by standards (not tunable) ---
G87251_DOMAIN_LO, G87251_DOMAIN_HI = 24, 43      # G.8275.1
G87251_PRIORITY1                   = 128          # G.8275.1 (fixed, removed from BMCA compare)
IEEE1588_MIN_LEGAL_CLOCKCLASS      = 6            # IEEE 1588-2019 Table 5 (0-5 reserved)
G87251_MAX_STEPS_REMOVED           = 255          # UNH PWR.c.2.4 / G.8275.1: >=255 must be discarded
# A source appearing in fewer than this fraction of Announce messages is a start-up
# transient (a node announcing itself before it locks), not a sustained presence.
# Fixed at 1% as a structural definition of "transient", not fitted to any data.
TRANSIENT_FRACTION                 = 0.01

VERDICT_ATTACK, VERDICT_BENIGN, VERDICT_UNKNOWN = "ATTACK", "BENIGN", "UNKNOWN"

def load_context(run_dir):
    with open(os.path.join(run_dir, "context.json")) as f:
        return json.load(f)

def decide(deep_csv, ctx):
    """Return (verdict, fault_hint, reasons[], evidence{}). Fail-closed: any missing
    evidence yields UNKNOWN, never BENIGN."""
    reasons, ev = [], {}
    try:
        rows = list(csv.DictReader(open(deep_csv)))
    except Exception as e:
        return VERDICT_UNKNOWN, None, [f"capture unreadable: {e}"], ev
    if not rows:
        return VERDICT_UNKNOWN, None, ["empty capture"], ev

    ann = [r for r in rows if r.get("message_type") == "Announce"]
    ev["n_packets"], ev["n_announce"] = len(rows), len(ann)
    if not ann:
        return VERDICT_UNKNOWN, None, ["no Announce messages - cannot assess BMCA"], ev

    allow = set(ctx["gm_allowlist"]) | {ctx["expected_bc_identity"]}
    ev["allowlist"] = sorted(allow)

    # ---- T1 / Class-A checks: protocol legality, straight from the standards ----
    illegal_cc = [r for r in ann
                  if r.get("gm_clock_class") not in ("", None)
                  and int(r["gm_clock_class"]) < IEEE1588_MIN_LEGAL_CLOCKCLASS]
    ev["illegal_clockclass_pkts"] = len(illegal_cc)

    bad_p1 = [r for r in ann
              if r.get("gm_priority1") not in ("", None)
              and int(r["gm_priority1"]) != G87251_PRIORITY1]
    ev["nonconformant_priority1_pkts"] = len(bad_p1)

    bad_domain = [r for r in rows
                  if r.get("domain_number") not in ("", None)
                  and not (G87251_DOMAIN_LO <= int(r["domain_number"]) <= G87251_DOMAIN_HI)]
    ev["out_of_profile_domain_pkts"] = len(bad_domain)

    bad_mcast = [r for r in rows if r.get("g87251_mcast_ok") == "0"]
    ev["wrong_multicast_pkts"] = len(bad_mcast)

    # stepsRemoved >= 255 must be discarded (UNH PWR.c.2.4 / G.8275.1 maxStepsRemoved);
    # its presence in a received Announce is a conformance violation / ring-loop or rogue frame.
    bad_steps = [r for r in ann if r.get("steps_removed") not in ("", None)
                 and int(r["steps_removed"]) >= G87251_MAX_STEPS_REMOVED]
    ev["stepsRemoved_ge_255_pkts"] = len(bad_steps)
    # alternateMasterFlag = TRUE Announce must be discarded (UNH PWR.c.2.5).
    alt_master = [r for r in ann if r.get("flag_alternateMaster") == "1"]
    ev["alternate_master_flag_pkts"] = len(alt_master)

    # ---- grandmaster provenance ----
    gm = collections.Counter(r["gm_clock_identity"] for r in ann if r.get("gm_clock_identity"))
    total = sum(gm.values()) or 1
    off = {g: n for g, n in gm.items() if g not in allow}
    off_sustained = {g: n for g, n in off.items() if n > TRANSIENT_FRACTION * total}
    ev["gm_identities"] = dict(gm)
    ev["off_allowlist_sustained"] = off_sustained
    # Apply the SAME transient filter to provisioned grandmasters. A standby GM that
    # announces once at start-up before losing the election has not "changed" anything.
    provisioned_gms_seen = [g for g, n in gm.items()
                            if g in set(ctx["gm_allowlist"]) and n > TRANSIENT_FRACTION * total]
    gm_changed = len(provisioned_gms_seen) > 1
    ev["provisioned_gms_seen"] = provisioned_gms_seen
    maint = bool(ctx.get("maintenance_window_open", False))
    ev["maintenance_window_open"] = maint

    # ---- source-identity provenance ----
    # In a provisioned fronthaul segment only known clocks transmit PTP at all. A source
    # that never sends Announce (e.g. a Sync-only injector) carries no grandmasterIdentity
    # and is therefore invisible to the GM check above - it must be caught here.
    known_sources = set(ctx["gm_allowlist"]) | {ctx["expected_bc_identity"]} \
                    | set(ctx.get("expected_client_identities", []))
    src = collections.Counter(r["source_clock_identity"] for r in rows
                              if r.get("source_clock_identity"))
    src_total = sum(src.values()) or 1
    unknown_src = {sid: n for sid, n in src.items()
                   if sid not in known_sources and n > TRANSIENT_FRACTION * src_total}
    ev["ptp_sources"] = dict(src)
    ev["unknown_sources_sustained"] = unknown_src

    # ---- per-source cadence self-consistency (DoS) ----
    # G.8275.1 mandates Announce at logInterval -3 (8/s). Each frame also DECLARES the
    # sender's own interval. A source transmitting far faster than the rate it declares
    # contradicts itself; that self-inconsistency is the defining feature of flooding,
    # whatever the payload. The 2x factor is a structural tolerance for burstiness and
    # capture duplication - it is not fitted to any observation.
    CADENCE_TOLERANCE = 2.0
    tspan = None
    try:
        ts = [int(r["capture_ts_ns"]) for r in rows if r.get("capture_ts_ns")]
        tspan = (max(ts) - min(ts)) / 1e9
    except Exception:
        tspan = None
    flooders = {}
    if tspan and tspan > 1.0:
        per_src = collections.Counter(r["source_clock_identity"] for r in ann
                                      if r.get("source_clock_identity"))
        for sid, n in per_src.items():
            obs = n / tspan
            decl = [int(r["log_message_interval"]) for r in ann
                    if r.get("source_clock_identity") == sid
                    and r.get("log_message_interval") not in ("", None)]
            declared_rate = 2.0 ** (-decl[0]) if decl else 8.0   # 8/s is the profile rate
            if obs > CADENCE_TOLERANCE * declared_rate:
                flooders[sid] = dict(observed_hz=round(obs, 2),
                                     declared_hz=round(declared_rate, 2), n=n)
    ev["announce_rate_self_inconsistent"] = flooders
    ev["capture_span_s"] = round(tspan, 3) if tspan else None

    # ---- relay vs self-announce, per unknown source (A8 vs A1) ----
    # A rogue GRANDMASTER announces ITSELF (gm_identity == source, stepsRemoved 0).
    # A rogue BOUNDARY CLOCK inserted in the path RELAYS another clock's grandmaster
    # identity with stepsRemoved incremented. These are different faults.
    relaying_unknown, selfann_unknown = {}, {}
    for sid in unknown_src:
        mine = [r for r in ann if r.get("source_clock_identity") == sid]
        if not mine:
            continue
        self_n = sum(1 for r in mine if r.get("gm_identity_equals_source") == "1")
        steps = [int(r["steps_removed"]) for r in mine
                 if r.get("steps_removed") not in ("", None)]
        if self_n == 0 and steps and max(steps) > 0:
            relaying_unknown[sid] = dict(n=len(mine), max_steps_removed=max(steps),
                                         relays=sorted({r["gm_clock_identity"] for r in mine}))
        else:
            selfann_unknown[sid] = dict(n=len(mine), self_announce_pkts=self_n)
    ev["unknown_relaying_sources"] = relaying_unknown
    ev["unknown_selfannouncing_sources"] = selfann_unknown

    # ---- sequence integrity (replay) ----
    # IEEE 1588 cl.11.3 / 13.8: a Delay_Resp ECHOES the sequenceId of the Delay_Req it
    # answers. A master interleaving replies to several clients therefore emits a
    # non-monotonic sequence by design. The counter belongs to the REQUESTING port, not
    # the responding source. Keying it wrongly makes legal traffic look like replay.
    seq_reg = 0
    by_src = collections.defaultdict(list)
    for r in rows:
        if r.get("sequence_id") in ("", None):
            continue
        if r.get("message_type") == "Delay_Resp":
            owner = r.get("requesting_clock_identity") or ""
            port = r.get("requesting_port_number") or ""
        else:
            owner = r.get("source_clock_identity") or ""
            port = r.get("source_port_number") or ""
        by_src[(owner, port, r.get("message_type"))].append(int(r["sequence_id"]))
    for k, v in by_src.items():
        seq_reg += sum(1 for a, b in zip(v, v[1:]) if b < a and (a - b) < 30000)
    ev["sequence_regressions"] = seq_reg

    # ---- rate legality (DoS) ----
    bad_sync = sum(1 for r in rows if r.get("g87251_log_sync_ok") == "0")
    bad_ann  = sum(1 for r in rows if r.get("g87251_log_announce_ok") == "0")
    ev["nonconformant_sync_cadence_pkts"], ev["nonconformant_announce_cadence_pkts"] = bad_sync, bad_ann

    # =============== ORDERED DECISION (first match wins) ===============
    # Ordered by what DEFINES each fault, not by convenience.
    # 1) Flooding is defined by RATE, whatever the payload looks like.
    if flooders:
        reasons.append("Source(s) transmitting Announce far above the rate they themselves "
                       f"declare (G.8275.1 mandates 8/s): {flooders}")
        return VERDICT_ATTACK, "A5", reasons, ev
    # 2) Replay is defined by reuse of a sequence a compliant sender never reuses.
    if seq_reg > 0:
        reasons.append(f"sequenceId regressions={seq_reg} (counter keyed per requesting port "
                       f"for Delay_Resp); a compliant sender is strictly increasing")
        return VERDICT_ATTACK, "A3", reasons, ev
    # 3) An unauthorised clock RELAYING a real grandmaster = rogue boundary clock in path.
    if relaying_unknown:
        reasons.append("Unauthorised clock inserted in the timing path, relaying another "
                       f"grandmaster with stepsRemoved incremented: {relaying_unknown}")
        return VERDICT_ATTACK, "A8", reasons, ev
    # 4) An unauthorised clock SELF-announcing as grandmaster = rogue grandmaster.
    if selfann_unknown and off_sustained:
        reasons.append("Unauthorised clock advertising ITSELF as grandmaster (not in the "
                       f"provisioned allow-list): {selfann_unknown}")
        return VERDICT_ATTACK, "A1", reasons, ev
    # 5) Protocol-illegal Announce content.
    if illegal_cc:
        reasons.append(f"IEEE 1588-2019 Table 5: clockClass < {IEEE1588_MIN_LEGAL_CLOCKCLASS} "
                       f"(RESERVED/illegal) in {len(illegal_cc)} Announce messages")
        return VERDICT_ATTACK, "A1", reasons, ev
    if bad_p1:
        reasons.append(f"G.8275.1 fixes priority1={G87251_PRIORITY1}; {len(bad_p1)} Announce violate it")
        return VERDICT_ATTACK, "A1", reasons, ev
    if bad_steps:
        reasons.append(f"UNH PWR.c.2.4 / G.8275.1: stepsRemoved>={G87251_MAX_STEPS_REMOVED} "
                       f"(must be discarded) in {len(bad_steps)} Announce")
        return VERDICT_ATTACK, "A4", reasons, ev
    if alt_master:
        reasons.append(f"UNH PWR.c.2.5: alternateMasterFlag=TRUE in {len(alt_master)} Announce "
                       f"(must be discarded)")
        return VERDICT_ATTACK, "A8", reasons, ev
    if off_sustained:
        reasons.append(f"Grandmaster identity not in the provisioned allow-list, sustained: "
                       f"{sorted(off_sustained)}")
        return VERDICT_ATTACK, "A1", reasons, ev
    # 6) An unauthorised source transmitting timing but never Announce = Sync/Follow_Up spoof.
    if unknown_src:
        reasons.append("PTP transmitted by source(s) not in the provisioned inventory, "
                       f"sustained: {sorted(unknown_src)}")
        return VERDICT_ATTACK, "A2", reasons, ev
    # 7) Out-of-profile transport.
    if bad_domain or bad_mcast:
        reasons.append(f"Out-of-profile transport: domain={len(bad_domain)} pkts, "
                       f"wrong multicast={len(bad_mcast)} pkts")
        return VERDICT_ATTACK, "A5", reasons, ev
    if bad_sync or bad_ann:
        reasons.append(f"Cadence outside G.8275.1 (Sync -4 / Announce -3): "
                       f"sync={bad_sync}, announce={bad_ann}")
        return VERDICT_ATTACK, "A5", reasons, ev
    # ---- benign ----
    if gm_changed and maint:
        reasons.append("Grandmaster changed to another PROVISIONED clock during an open "
                       "maintenance window - planned failover")
        return VERDICT_BENIGN, "B2", reasons, ev
    if gm_changed and not maint:
        reasons.append("Grandmaster changed between provisioned clocks with NO maintenance "
                       "window open - cannot attribute intent")
        return VERDICT_UNKNOWN, "B2?", reasons, ev
    reasons.append("Only provisioned clocks present; no protocol-legality violation")
    return VERDICT_BENIGN, None, reasons, ev

def main():
    run_dir = sys.argv[1]
    deep = sys.argv[2] if len(sys.argv) > 2 else None
    if deep is None:
        cands = [f for f in os.listdir(run_dir) if f.endswith("dn.deep.csv")]
        deep = os.path.join(run_dir, cands[0]) if cands else None
    ctx = load_context(run_dir)
    v, hint, why, ev = decide(deep, ctx)
    out = dict(scenario=ctx.get("scenario"), truth_class=ctx.get("class"),
               truth_fault=ctx.get("fault_id"), verdict=v, fault_hint=hint,
               reasons=why, evidence=ev)
    print(json.dumps(out, indent=2))
    with open(os.path.join(run_dir, "decision.json"), "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
