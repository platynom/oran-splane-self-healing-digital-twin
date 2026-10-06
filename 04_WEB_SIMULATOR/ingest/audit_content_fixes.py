#!/usr/bin/env python3
"""Apply the 2026-10-06 independent content audit to content/architecture.json.

Input: an audit JSON (one verdict per sentence: VERIFIED / WRONG_CLAUSE / UNSUPPORTED / SOURCE_NEEDED, with the verbatim
supporting quote and where it was found), produced by an auditor that had no access to the builder's reasoning.

  python3 ingest/audit_content_fixes.py <audit.json> [<reverify.json> ...]

Rules applied:
  * VERIFIED (auditor opened the cited source and quoted support)  -> status VERIFIED, quote stored under "verification".
  * WRONG_CLAUSE -> citation corrected to where the auditor found the text; status UNVERIFIED until re-verified.
  * UNSUPPORTED  -> text narrowed to what the source says (or the sentence is split so each part has its own source);
                    status UNVERIFIED until re-verified.
  * SOURCE_NEEDED -> unchanged (hidden by the UI).
  * <reverify.json> ... (optional): later independent passes over the changed and new sentences, applied in order; a
    sentence is promoted to VERIFIED only if a pass VERIFIED exactly its current text. Findings of pass 2 are fixed in
    section 3b (texts and clauses), and those fixes are re-checked by pass 3.
Every change is listed in content/architecture.json under "audit_log".
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "content", "architecture.json")
AUDIT_BY = "independent subagent audit 2026-10-06"

arch = json.load(open(PATH))
audit = {s["id"]: s for s in json.load(open(sys.argv[1]))["sentences"]}
passes = [{s["id"]: s for s in json.load(open(f))["sentences"]} for f in sys.argv[2:]]
log = []

NEW_SOURCES = [
    ("SCEN", "Campaign scenario driver scenarios.sh (frozen copy)", "03_RECOVERY_LOOP_S-PLANE/testbed_frozen_copy/run/scenarios.sh", "testbed code; shows where each scenario's traffic originates"),
    ("B6R1", "B6 run 1 drift report", "outputs/B6_two_machine_2026-10-02/DRIFT_REPORT.md", "run 1 analysis output"),
    ("B6REC", "B6 two-machine measurement record", "outputs/B6_two_machine_2026-10-02/B6_MEASUREMENT_RECORD_2026-10-02.md", "run 1 record incl. scope limits"),
    ("APPX", "Simulator extractor ingest/extract.py", "04_WEB_SIMULATOR/ingest/extract.py", "this app's own processing code (how replay packet counts are attributed)"),
    ("RUNS", "Recovery-loop run archive r13-r17", "03_RECOVERY_LOOP_S-PLANE/results/recovery_eval_runs_r13-r17.tgz", "raw per-run captures and logs (dn.pcap.gz, loop.jsonl); counts computed from it"),
]
SRC = {s["id"]: s for s in arch["sources"]}
for sid, title, path, note in NEW_SOURCES:
    if sid not in SRC:
        arch["sources"].append(dict(id=sid, title=title, path_or_url=path, openable_in_this_session=True, note=note))
        SRC[sid] = arch["sources"][-1]


def cite(sid, clause, locator, status="UNVERIFIED"):
    s = SRC[sid]
    return dict(source=s["title"], source_id=sid, clause=clause, locator=locator, url_or_repo_path=s["path_or_url"], status=status)


EL = {e["id"]: e for e in arch["elements"]}


def find(sid):
    for e in arch["elements"]:
        for i, s in enumerate(e["sentences"]):
            if s["id"] == sid:
                return e, i
    raise KeyError(sid)


def replace(sid, text, kind, citation, why):
    e, i = find(sid)
    old = e["sentences"][i]
    e["sentences"][i] = dict(id=sid, kind=kind, text=text, citation=citation)
    log.append(dict(sentence=sid, action="rewritten", verdict=audit[sid]["verdict"], old=old["text"], new=text, why=why))


def add(el, sid, text, kind, citation, why):
    assert not any(s["id"] == sid for e in arch["elements"] for s in e["sentences"]), f"sentence id {sid} already exists"
    EL[el]["sentences"].append(dict(id=sid, kind=kind, text=text, citation=citation))
    log.append(dict(sentence=sid, action="added", new=text, why=why))


# ---------------------------------------------------------------- 1. statuses from the audit
for e in arch["elements"]:
    for s in e["sentences"]:
        a = audit.get(s["id"])
        if a and a["verdict"] == "VERIFIED":
            s["citation"]["status"] = "VERIFIED"
            s["verification"] = dict(by=AUDIT_BY, quote=a.get("quote", ""), where=a.get("where_found", ""))

# ---------------------------------------------------------------- 2. WRONG_CLAUSE
e, i = find("osc-drift.s2")
e["sentences"][i]["citation"] = cite("B6R1", "Verdict against pre-registered criteria; Headline", "C1 row (A=348, B=658) and headline +20.161 ppm")
log.append(dict(sentence="osc-drift.s2", action="citation corrected", verdict="WRONG_CLAUSE", why="run-1 figures are in DRIFT_REPORT.md, not the run-2 report"))

# ---------------------------------------------------------------- 3. UNSUPPORTED -> narrowed / split
U = "audit: part of the sentence not in the cited source; narrowed to the quoted text"
replace("gm-a.s3", "The operator's allow-list holds GM-A and GM-B (identities …00000a and …00000b).", "CONFIGURED",
        cite("GUIDE", "Chapter 9", "p.14"), "allow-list role was not stated by provisioning.json; identity-to-GM mapping is in the Guide")
replace("gm-a.s4", "No GNSS receiver exists in the testbed, so GNSS spoofing and jamming cannot be produced; all namespaces share the host clock, with free_running 1 set.", "UNKNOWN",
        cite("V8", "slide 18, verified platform constraints", "'No GNSS receiver'; 'One shared oscillator'"), "'stands in for the PRTC/T-GM role' and holdover were not on the cited slide")
add("gm-a", "gm-a.s5", "The lab has no PRTC/GPS, so every node truthfully advertises clockClass 248.", "CONFIGURED",
    cite("TBREF", "§2 G.8275.1 profile configuration", "clock_class_threshold 248 row"), "label correction: GM-A is a T-GM without a PRTC")
replace("gm-b.s2", "When GM-A fails with no maintenance window open and GM-B takes over, the frozen rule returned UNKNOWN in 12 of 12 campaign runs.", "MEASURED",
        cite("EVAL4", "frozen.per_scenario.B_unplanned_failover", "correct 12 / n 12, expect UNKNOWN"), "causal clause not in EVALUATION_V4")
replace("bc.s1", "The boundary clock (T-BC, priority2 120) connects the grandmaster bridge brUP and the radio-unit bridge brDN; the Testbed Configuration Reference lists its role as 'stepsRemoved 0→1'.", "CONFIGURED",
        cite("TBREF", "§4 Topology and node roles", "topology line and node table, row bc"), "slave/master sides not in TBREF; 'RUs see stepsRemoved 1' conflicts with topology.sh ('RUs see stepsRemoved=2')")
replace("o-ru.s2", "The Testbed Configuration Reference labels the three radio units 'O-RU proxies (T-TSC)', each with priority2 128.", "CONFIGURED",
        cite("TBREF", "§4 Topology and node roles", "node table, row ru1/ru2/ru3"), "clientOnly is not in TBREF; moved to its own sentence citing the cfg")
add("o-ru", "o-ru.s5", "The radio units' ptp4l configurations set clientOnly 1, so they only take time.", "CONFIGURED",
    cite("CFG", "ru1.cfg, ru2.cfg, ru3.cfg", "clientOnly 1 (ru1.cfg line 49)"), "split from o-ru.s2")
replace("o-ru.s4", "130 ns is scoped by the project's verification to the relative time-alignment error for 5G FR2 intra-band contiguous carrier aggregation, Timing Category A, not presented as a universal O-RAN limit.", "REFERENCE",
        cite("V5DIS", "item 5", "130 ns scope"), "qualifier 'FR2' restored")
replace("fh-splane.s3", "ITU-T G.8271.1 frames ±1.5 µs as an end-application, reference-point-E absolute time-error limit relative to a common recognised time standard.", "REFERENCE",
        cite("V5LOG", "item 32", "G.8271.1 ±1.5 µs scope"), "1100 ns clause not in item 32; moved to fh-splane.s5")
add("fh-splane", "fh-splane.s5", "The project's deck gives the total budget at reference point E and the network limit at reference point C as 1100 ns.", "REFERENCE",
    cite("V8", "slide 7", "budget column: 'Total budget at reference point E; the network limit at reference point C is 1100 ns'"), "split from fh-splane.s3")
replace("fh-splane.s4", "SyncE is a physical-layer function and was not implemented in the testbed, which exercised PTP only.", "UNKNOWN",
        cite("V8", "slide 16", "Scope disclosure"), "inference about frequency measurement removed")
replace("injector.s1", "Attacks enter on the radio-unit segment (A1, A2, A3, A5, C2, C3), across both bridges for the rogue relay (A8), and by blackholing the boundary clock's downstream port (C1).", "CONFIGURED",
        cite("GUIDE", "Chapter 7", "figure caption, p.12"), "'inside RU3's namespace' was wrong for A1 and not in the cited Guide")
add("injector", "injector.s5", "The A1 rogue grandmaster is a separate ptp4l in its own network namespace 'rogue', attached to the radio-unit bridge brDN through port p-rogue.", "CONFIGURED",
    cite("SCEN", "case A1_rogue_master", "lines 40-50"), "corrects the A1 location")
replace("injector.s4", "Where the injector shares RU3's port (A2, A3, A5, C2, C3), isolating that port also stops RU3's own Delay_Req.", "MEASURED",
        cite("RESULTS", "§6 Limits", "Collateral on RU3"), "'reported separately' is in PREREG, not RESULTS §6")
replace("fh-mplane.s2", "The project wrote fixture-testable parsers for pmc and synce4l synchronization status text; the code names O-RU M-plane NETCONF/YANG synchronization telemetry as the authoritative production equivalent but does not implement it.", "CONFIGURED",
        cite("SYNCPY", "module docstring", "lines 3-8"), "it is not an M-plane NETCONF/YANG parser")
replace("fh-mplane.s3", "Management queries in the testbed were made with pmc; on this testbed pmc without -d 24 returns no data, and with -d 24 it returns PARENT_DATA_SET and PORT_DATA_SET.", "MEASURED",
        cite("RESULTS", "§4", "table row 3 (pmc)"), "'the testbed has no M-plane' is not stated in RESULTS")
replace("smo-nonrt.s1", "In the project's architecture figure (v8 slide 4) the SMO / Non-RT RIC box ('policy and lifecycle') sits beside the Near-RT RIC, above the O-RU, O-DU, O-CU and 5G Core.", "REFERENCE",
        cite("V8", "slide 4", "architecture figure"), "placement corrected: beside the Near-RT RIC, not above the RICs")
replace("smo-nonrt.s3", "The recovery loop runs as a standalone process in the testbed's root namespace, on the same software testbed and frozen detector, and does not change any frozen artefact.", "CONFIGURED",
        cite("DESIGN", "opening paragraph", "and architecture diagram"), "no source places such a loop in the SMO domain")
replace("smo-nonrt.s4", "No digital twin rehearses the action before it is taken; actions are verified after execution.", "UNKNOWN",
        cite("RESULTS", "§6 Limits", "No digital twin"), "'rApp / SMO function not decided' is not stated in any opened source")
replace("osc-drift.s3", "These are consumer laptop crystals measured against NTP, not telecom-class oscillators.", "UNKNOWN",
        cite("DESIGN", "Oscillator drift (B6)", "paragraph, line 60"), "raw-file absence not stated in DESIGN")
add("osc-drift", "osc-drift.s4", "The two-laptop run measures B6's physical premise; it is not an end-to-end B6 detection test, because no PTP ran between the two machines.", "UNKNOWN",
    cite("B6REC", "§7 Scope limits", "item 1"), "scope of the B6 measurement (B6 is no longer listed as 'not measured')")
add("osc-drift", "osc-drift.s5", "The B6 record states that the Fault Detectability workbook row B6 is not changed by this run, because that row describes detectability on the software testbed.", "UNKNOWN",
    cite("B6REC", "§7 Scope limits", "closing paragraph"), "explains why the workbook's 'HARDWARE required' for B6 stands")
replace("fh-cplane.s2", "The testbed does not emulate the O-DU, so it carries no C-plane traffic to observe.", "UNKNOWN",
        cite("V8", "slide 6", "OUR TESTBED box: 'The O-DU itself is not emulated.'"), "narrowed to the slide's statement")
replace("fh-uplane.s2", "The testbed does not emulate the O-DU, so no U-plane traffic was present to measure.", "UNKNOWN",
        cite("V8", "slide 6", "OUR TESTBED box: 'The O-DU itself is not emulated.'"), "narrowed to the slide's statement")
replace("air-interface.s2", "The cited 3GPP limits are TDD cell phase synchronization better than 3 µs (TS 38.133) and time-alignment error of at most 65 ns for MIMO and 260 ns for intra-band contiguous carrier aggregation (TS 38.104, clause 9.6.3.2).", "REFERENCE",
        cite("V8", "slide 12", "'Service limits at stake' footer"), "qualifier 'TDD' restored")
replace("ue.s2", "Measured impact in this project is protocol-level; time-error and service impact come from the cited literature.", "UNKNOWN",
        cite("V8", "slide 12", "footer"), "RESULTS §6 does not mention user equipment")
replace("lls-c2.s2", "The Testbed Configuration Reference says the testbed 'models O-RAN LLS-C2/C3'.", "CONFIGURED",
        cite("TBREF", "§4 Topology and node roles", "section subtitle"), "the app's policy is not a sourced fact; moved to the audit")
add("lls-c2", "lls-c2.s3", "The deck's quoted LLS-C2 definition puts the O-DU in the synchronization chain, while the deck describes the testbed as having no O-DU in the timing chain.", "REFERENCE",
    cite("V8", "slide 6", "LLS-C2 row and OUR TESTBED box"), "why LLS-C2 does not fit the testbed")
replace("lls-c4.s2", "The testbed has no GNSS receiver, so GNSS spoofing and jamming cannot be produced in it.", "UNKNOWN",
        cite("V8", "slide 18", "'No GNSS receiver'"), "'not the testbed's configuration' is on slide 6, not 18")
add("lls-c3", "lls-c3.s4", "The lab has no PRTC/GPS, so every node truthfully advertises clockClass 248.", "CONFIGURED",
    cite("TBREF", "§2 G.8275.1 profile configuration", "clock_class_threshold 248 row"), "why LLS-C3 is the closest match rather than an exact one")
replace("bmca-contest.s2", "The testbed sets priority1 128, domain 24 and the alternate BMCA (dataset_comparison G.8275.x).", "CONFIGURED",
        cite("CFG", "g87251.base", "[global]"), "'the profile fixes priority1' is not in the cfg file")
replace("attack-packets.s1", "In the loop arm the isolation target was p-rogue in A1, p-rbc-dn in A8 and p-v-ru3 in A2, A3, A5, C2 and C3.", "MEASURED",
        cite("RLEVAL", "summary.<scenario>.loop.action_kinds", "A1, A2, A3, A5, A8, C2, C3"), "RESULTS names no ports; port names are in EVALUATION_RL.json")
replace("attack-packets.s2", "Spoofing, replay, flooding, malformed-frame and whole-second-abuse injectors run on the radio-unit segment; the rogue boundary clock spans both bridges; interception blackholes the boundary clock's downstream port.", "CONFIGURED",
        cite("GUIDE", "Chapter 7", "figure caption, p.12"), "'inside RU3's namespace' not in the Guide and wrong for A1")
replace("attack-packets.s3", "In the loop arm the nft bridge rule drops PTP at the isolated port; the final ruleset shows the rule in 35 of 35 isolations.", "MEASURED",
        cite("RESULTS", "§5", "'35/35 isolations present in the final nft ruleset'"), "frame-count claim moved to attack-packets.s4 with its own source")
add("attack-packets", "attack-packets.s4", "From 1 s after the isolation, the attacker sender had 0 frames on brDN in all 30 loop-arm isolations with a distinct attacker MAC (A1, A2, A5, A8, C2, C3; 5 each), while the matching control runs kept 216 to 78,218 frames; A3 replays carry the boundary clock's MAC and cannot be separated.", "MEASURED",
    cite("RUNS", "per-run dn.pcap.gz, counted by 04_WEB_SIMULATOR/ingest/extract.py", "loop vs control, t ≥ act + 1 s"), "auditor recomputation over all isolations (replaces the unsupported frame-count claim)")
replace("port-counts.s2", "The live loop tags every PTP frame with its bridge ingress port (AF_PACKET per port, ingress only); the archived dn/up captures are bridge-level captures.", "CONFIGURED",
        cite("DESIGN", "Localisation: provisioned port roles", "and capture diagram"), "MAC attribution is the app's method, not DESIGN's")
add("port-counts", "port-counts.s3", "In this app's replay, capture frames are attributed to senders by source MAC address, not by bridge ingress port; frames from unprovisioned MACs, GM MACs on brDN and master-role frames from RU3's MAC are counted as the injector.", "CONFIGURED",
    cite("APPX", "packets block", "lines 243-283"), "documents the app's own attribution method")
replace("loop-decide.s1", "The loop acts only when at least 2 of the last 3 evaluations say ATTACK, never automatically isolates a provisioned master-role port, and fails over when no Announce arrives from any provisioned master port for 2 s (10 s while a maintenance window is open).", "CONFIGURED",
        cite("PREREG", "§3 Loop parameters", "Persistence, Service-loss trigger, Safety guard rows"), "'(it escalates instead)' is in DESIGN, not PREREG §3")
replace("loop-act.s1", "Isolation is an nftables bridge rule dropping ethertype 0x88F7 at the offending port; failover starts the cold-standby boundary clock.", "CONFIGURED",
        cite("DESIGN", "Policy table", "ISOLATE and ACTIVATE STANDBY BC rows"), "control-arm clause moved to loop-act.s2 (PREREG §2)")
add("loop-act", "loop-act.s2", "In the control arm the identical loop runs in observe-only mode: it detects, decides and logs would_act, and executes nothing.", "CONFIGURED",
    cite("PREREG", "§2", "arm definition 'control'"), "split from loop-act.s1")
replace("ds-raw-missing.s2", "The raw per-sample CSVs of the B6 two-laptop measurement are named, with their sha256, in the analysis output.", "UNKNOWN",
        cite("B6", "Provenance", "laptopA / laptopB CSV names and sha256"), "absence is not stated by the cited report")
add("hw-faults", "hw-faults.s3", "The B6 two-laptop run does not unlock B1, B4, A6 or A7, and adds no hardware timestamping.", "UNKNOWN",
    cite("B6REC", "§7 Scope limits", "item 5"), "B6 is shown separately as measured on two laptops")

# ---------------------------------------------------------------- 3b. findings of re-verification pass 2
def fix(sid, why, text=None, kind=None, citation=None):
    e, i = find(sid)
    s_ = e["sentences"][i]
    old = s_["text"]
    if text: s_["text"] = text
    if kind: s_["kind"] = kind
    if citation: s_["citation"] = dict(citation)  # copy: one citation dict must never be shared by two sentences
    log.append(dict(sentence=sid, action="pass-2 fix", old=old, new=s_["text"], why=why))

T3 = cite("TBREF", "§3 Declared deviations from a production deployment", "p.4, clock_class_threshold 248 row")
fix("gm-a.s5", "pass 2 WRONG_CLAUSE: text is in §3, not §2", citation=T3)
fix("lls-c3.s4", "pass 2 WRONG_CLAUSE: text is in §3, not §2", citation=T3)
fix("attack-packets.s2", "pass 2 WRONG_CLAUSE: attack classes are named in the Chapter 8 table",
    citation=cite("GUIDE", "Chapters 7-8", "p.12 figure caption (positions) and p.13 'Eight attacks' table (classes)"))
fix("gm-b.s2", "pass 2: scenario description not in EVALUATION_V4.json; moved to gm-b.s4",
    text="In the unplanned grandmaster failover scenario (B_unplanned_failover) the frozen rule returned UNKNOWN in 12 of 12 campaign runs.")
add("gm-b", "gm-b.s4", "In that scenario GM-A is killed with no maintenance window open and the provisioned GM-B takes over; the scenario script notes that from packets alone this is indistinguishable from an attack that suppressed GM-A.", "CONFIGURED",
    cite("SCEN", "case B_unplanned_failover", "lines 94-101"), "pass 2: the causal statement has a source in the scenario script")
fix("bc.s1", "pass 2: 'stepsRemoved 0→1' is in the Purpose column, not Role",
    text="The boundary clock (T-BC, priority2 120) connects the grandmaster bridge brUP and the radio-unit bridge brDN; the Testbed Configuration Reference gives its purpose as 'stepsRemoved 0→1; enables A8 and B7'.")
fix("fh-splane.s5", "pass 2: sentence read as if both were 1100 ns",
    text="The project's deck gives the total budget at reference point E as ±1.5 µs and the network limit at reference point C as 1100 ns.")
fix("smo-nonrt.s3", "pass 2: 'standalone process' not in DESIGN",
    text="The recovery loop runs in the testbed's root namespace, on the same software testbed and frozen detector, and does not change any frozen artefact.")
fix("fh-cplane.s2", "pass 2: consequence not on the slide", text="The testbed does not emulate the O-DU.")
fix("fh-uplane.s2", "pass 2: consequence not on the slide", text="The testbed does not emulate the O-DU.")
fix("port-counts.s2", "pass 2: 'bridge-level captures' not in DESIGN",
    text="The live loop captures with AF_PACKET on every bridge port, ingress only, and tags every PTP frame with its ingress port.")
fix("port-counts.s3", "pass 2: injector relabelling applies only to A2, A3, A5, C2 and C3",
    text="In this app's replay, capture frames are attributed to senders by source MAC address, not by bridge ingress port; in A2, A3, A5, C2 and C3, frames from unprovisioned MACs, GM MACs on brDN and master-role frames from RU3's MAC are counted as the injector, and in A1 and A8 the rogue devices' MACs are mapped to the rogue grandmaster and rogue boundary clock.")
fix("loop-decide.s1", "pass 2: PREREG §3 does not name the failover action, and the persistence rule applies to isolation only",
    text="Isolation requires at least 2 of the last 3 evaluations to say ATTACK; a provisioned master-role port is never isolated automatically; the service-loss trigger is no Announce from any provisioned master port for 2 s (10 s while a maintenance window is open).")
fix("attack-packets.s4", "pass 2: auditor's raw recount (own alignment) gave control counts 220-79,597, not 216-78,218; narrowed to what both counts support",
    text="From 1 s after the isolation, the attacker sender had 0 frames on brDN in all 30 loop-arm isolations with a distinct attacker MAC (A1, A2, A5, A8, C2, C3; 5 each), while every matching control run still had more than 200 such frames; A3 replays reuse provisioned MACs and cannot be separated.")

# ---------------------------------------------------------------- 4. names, roles and tiers (labels must not overclaim)
def rename(el, **kw):
    for k, v in kw.items():
        log.append(dict(element=el, action=f"{k} changed", old=EL[el][k], new=v))
        EL[el][k] = v

rename("gm-a", name="GM-A: primary grandmaster (T-GM)")
rename("o-ru", name="O-RU proxies (RU1–RU3, T-TSC)")
rename("fh-splane", name="Open Fronthaul S-plane (PTP in the testbed)",
       role="Carries time (and, with SyncE, frequency) to the O-RU; the testbed exercised PTP only.")
rename("smo-nonrt", role="Project framing: where a closed loop like ours would sit in O-RAN; not implemented there.")
rename("lls-c3", name="LLS-C3 (closest match to the testbed)")
rename("hw-faults", name="Faults that need hardware on the testbed")
rename("hw-faults", tier=2)
rename("ds-raw-missing", tier=2)

arch["tier_log"].append(dict(element="hw-faults", requested=1, final=2, result="DEMOTED to tier 2",
    basis="Not built or measured on the testbed (V8 slide 18; TBREF: 'Neither unlocks GNSS (A6/A7/B1) or SyncE (B4)'); tier 1 is reserved for what the project built and measured."))
arch["tier_log"].append(dict(element="ds-raw-missing", requested=1, final=2, result="DEMOTED to tier 2",
    basis="Lists data the repository does not contain; nothing measured is shown for it."))
arch["tier_log"].append(dict(element="fh-splane", requested=1, final=1, result="kept, label narrowed to PTP",
    basis="V8 slide 16: 'The testbed exercised PTP only; SyncE is a physical-layer function and was not implemented.' SyncE stays a tier-2 element."))
arch["tier_log"].append(dict(element="gm-a, o-ru", requested=1, final=1, result="kept, labels corrected",
    basis="TBREF §4 node table: gma 'Primary grandmaster (T-GM)'; ru1-3 'O-RU proxies (T-TSC)'; TBREF §2: 'the lab has no PRTC/GPS'."))
arch["tier_log"].append(dict(element="lls-c3", requested="testbed configuration", final="closest match", result="relabelled",
    basis="V8 slide 6 quoted O-RAN.WG4.CUS.0 definitions: LLS-C1/C2 put the O-DU in the sync chain; the testbed has no O-DU (V8 slide 6, TBREF §4 topology). TBREF §4 says 'models O-RAN LLS-C2/C3'; LLS-C2 does not fit the quoted definition. LLS-C3 is the closest match, not exact: the lab has no PRTC (TBREF §2)."))

# ---------------------------------------------------------------- 4b. the five recorded checks: final resolution (2026-10-06 audit)
CHK = {c["id"]: c for c in arch["checks"]}
def resolve(cid, result, finding, evidence):
    log.append(dict(check=cid, action="resolved", old=CHK[cid]["result"], new=result))
    CHK[cid].update(result=result, finding=finding, evidence=CHK[cid]["evidence"] + evidence)

resolve("lls-mapping", "resolved: LLS-C3 is the closest match; LLS-C2 does not fit",
    "Definitions (O-RAN.WG4.CUS.0 v06.00 as quoted on v8 slide 6 via Armstrong, ATIS WSTS 2023): LLS-C1 and LLS-C2 put the O-DU in the "
    "synchronization chain; LLS-C3 has the O-DU outside it, with timing from PRTC/T-GM to the O-RU through the network. The testbed is "
    "GM -> T-BC -> O-RU proxies with no O-DU (TBREF §4 topology; v8 slide 6 'no O-DU in the timing chain'; cfg files). TBREF §4's 'models "
    "O-RAN LLS-C2/C3' is therefore not defensible for C2. C3 is the closest match, not an exact one: the lab has no PRTC/GPS (TBREF §3). "
    "The UI shows 'LLS-C3 · closest match (reference doc says C2/C3)'. The definitions are secondary (quoted), not read from the O-RAN specification.",
    ["v8 slide 6 LLS table and OUR TESTBED box", "TBREF §3 clock_class_threshold row", "TBREF §4 topology line"])
resolve("mplane-yang", "SOURCE_NEEDED (unchanged; hidden in the UI)",
    "Two further independent attempts on 2026-10-06 found 'o-ran-sync' only in project-authored code and docs; github.com/o-ran-sc/scp-oam-modeling "
    "showed no such file, a guessed YANG path returned 404, and code search was unavailable. Not confirmed.",
    ["docs/audit/content_audit_pass1.json Q2"])
resolve("g8271-budget", "resolved: ±1.5 µs is scoped to G.8271.1 reference point E; no source ties it to TDD",
    "Every openable source scopes ±1.5 µs to ITU-T G.8271.1: absolute time error at reference point E (end application) relative to a "
    "common time standard, with 1100 ns as the network limit at reference point C (V5LOG item 32; v8 slide 7). No openable source ties ±1.5 µs "
    "to TDD; the only TDD figure is the separate 3 µs TDD cell phase-synchronization limit (3GPP TS 38.133, v8 slide 12). The app's text uses "
    "the reference-point-E scope and keeps 'TDD' only on the 3 µs limit.",
    ["docs/audit/content_audit_pass1.json Q3", "v8 slide 12 footer"])

# ---------------------------------------------------------------- 5. second independent pass
for n, reverify in enumerate(passes, start=2):
    for e in arch["elements"]:
        for s in e["sentences"]:
            r = reverify.get(s["id"])
            if not r or s["citation"]["status"] == "VERIFIED":
                continue
            same = r.get("text") == s["text"]
            if r["verdict"] == "VERIFIED" and same:
                s["citation"]["status"] = "VERIFIED"
                s["verification"] = dict(by=f"independent re-verification pass {n}, 2026-10-06", quote=r.get("quote", ""), where=r.get("where_found", ""))
                log.append(dict(sentence=s["id"], action=f"pass {n}", verdict="VERIFIED"))
            else:
                log.append(dict(sentence=s["id"], action=f"pass {n}", verdict=r["verdict"] if same else f"{r['verdict']} (text since revised)", problem=r.get("problem", "")))

arch["audit_log"] = log
arch["status_note"] = ("Every sentence cites a source. VERIFIED: an independent auditor opened the cited source and quoted the supporting text "
                       "(stored under 'verification'). UNVERIFIED: cited but not independently confirmed. SOURCE_NEEDED: hidden by the UI.")
counts = {}
for e in arch["elements"]:
    for s in e["sentences"]:
        counts[s["citation"]["status"]] = counts.get(s["citation"]["status"], 0) + 1
json.dump(arch, open(PATH, "w"), indent=1, ensure_ascii=False)
open(PATH, "a").write("\n")
print(json.dumps(counts), "changes:", len(log))
