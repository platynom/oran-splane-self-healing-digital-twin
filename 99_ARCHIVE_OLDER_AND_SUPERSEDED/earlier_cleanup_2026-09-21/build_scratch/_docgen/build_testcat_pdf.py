#!/usr/bin/env python3
"""O-RAN S-Plane — Master Test Case Catalogue & Validation Record."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)

NAVY=colors.HexColor("#1F3864"); BLUE=colors.HexColor("#2E5496")
RED=colors.HexColor("#9C1B1B"); GRN=colors.HexColor("#1E5631"); AMB=colors.HexColor("#7F6000")
GREY=colors.HexColor("#3B3B3B"); LG=colors.HexColor("#EFEFEF")
LGR=colors.HexColor("#D9EAD3"); LRD=colors.HexColor("#F4CCCC"); LAM=colors.HexColor("#FFF2CC")

ss=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=ss["Heading1"],fontName="Helvetica-Bold",fontSize=14,textColor=NAVY,spaceBefore=11,spaceAfter=6)
H2=ParagraphStyle("H2",parent=ss["Heading2"],fontName="Helvetica-Bold",fontSize=10.5,textColor=BLUE,spaceBefore=9,spaceAfter=4)
BODY=ParagraphStyle("BODY",parent=ss["Normal"],fontName="Helvetica",fontSize=8.5,leading=11.5,spaceAfter=4)
SMALL=ParagraphStyle("SM",parent=BODY,fontSize=7.3,leading=9.5)
C=ParagraphStyle("C",parent=BODY,fontSize=7.0,leading=8.8,spaceAfter=0)
CB=ParagraphStyle("CB",parent=C,fontName="Helvetica-Bold")
TITLE=ParagraphStyle("T",parent=ss["Title"],fontName="Helvetica-Bold",fontSize=18,textColor=NAVY,spaceAfter=3)
SUB=ParagraphStyle("S",parent=BODY,fontSize=9.3,textColor=colors.HexColor("#444444"))

def P(t,s=C): return Paragraph(t,s)
def tb(data,w,hb=NAVY,zebra=True,statuscol=None):
    t=Table(data,colWidths=w,repeatRows=1)
    st=[("BACKGROUND",(0,0),(-1,0),hb),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#BFBFBF")),
        ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5)]
    if zebra:
        for i in range(1,len(data)):
            if i%2==0: st.append(("BACKGROUND",(0,i),(-1,i),LG))
    if statuscol is not None:
        for i in range(1,len(data)):
            v=str(data[i][statuscol])
            f=LGR if "RUN" in v else (LAM if "SPEC" in v else (LRD if "IMPOSS" in v or "BLOCK" in v else None))
            if f: st.append(("BACKGROUND",(statuscol,i),(statuscol,i),f))
    t.setStyle(TableStyle(st)); return t

S=[]; W=176*mm
S.append(Paragraph("O-RAN Open Fronthaul S-Plane",TITLE))
S.append(Paragraph("Master Test Case Catalogue, Validation Record and Coverage Statement",SUB))
S.append(Paragraph("Revised 2026-09-17 &#183; supersedes the 81-run revision. Validation record in &#167;7 is the 132-run randomised campaign (rule frozen 2026-09-17T04:49:33Z, 18 SHA-256 hashed artefacts).",SMALL))
S.append(Spacer(1,4*mm))

S.append(Paragraph("How to read this document",H1))
S.append(tb([
 [P("Status",CB),P("Meaning",CB)],
 [P("<b>RUN</b>"),P("Implemented on our testbed and executed. Results reported in §7.")],
 [P("<b>SPEC</b>"),P("Specified here and buildable in software, but <b>not yet executed</b>. Each says what it would catch.")],
 [P("<b>IMPOSSIBLE</b>"),P("Cannot be produced or measured on a software testbed. Physical reason given.")],
],[24*mm,W-24*mm],hb=NAVY,zebra=False,statuscol=0))
S.append(Spacer(1,2*mm))
S.append(Paragraph(
 "<b>On the question of exhaustiveness.</b> Test coverage of an adversarial space cannot honestly be given as a percentage — there is no fixed denominator, because an attacker can always invent a new variation. Any figure such as \"99.9% covered\" would be an invented number. "
 "This document instead reports coverage over denominators that are <b>real and countable</b>: how many catalogued cases exist, how many are executed, how many are specified-but-unrun, and how many are physically impossible here. Those figures are checkable. §8 states explicitly what is <i>not</i> covered.",BODY))

S.append(Paragraph("1 · Coverage summary",H1))
S.append(tb([
 [P("Catalogue",CB),P("Cases",CB),P("RUN",CB),P("SPEC (buildable, unrun)",CB),P("IMPOSSIBLE (hardware)",CB),P("Primary source",CB)],
 [P("Attack cases"),P("60"),P("<b>5</b>"),P("31"),P("24"),P("Research synthesis: TIMESAFE, PTPsec, Springer survey, O-RAN WG11, Concordia, TUM, MDPI, CVE records")],
 [P("Conformance / negative"),P("50+"),P("<b>6</b> (executed as negative tests, §7.3)"),P("38"),P("6"),P("UNH-IOL IEEE 1588 test plans; ITU-T G.8275.1 Amd.3; G.8273.2; G.8260")],
 [P("Benign fault scenarios"),P("58"),P("<b>6</b>"),P("37"),P("15"),P("ITU-T G.827x; vendor app notes (Calnex, Microchip, Meinberg, Cisco, Nokia); operator incident reports")],
 [P("<b>TOTAL</b>"),P("<b>168+</b>"),P("<b>17</b>"),P("<b>106</b>"),P("<b>45</b>"),P("")],
],[34*mm,14*mm,22*mm,28*mm,28*mm,W-126*mm],hb=NAVY,statuscol=None))
S.append(Spacer(1,1.5*mm))
S.append(Paragraph(
 "<b>Honest reading of these numbers.</b> 17 of 168 catalogued cases are executed — roughly <b>10%</b>. That sounds low, and it is the truthful figure. But the 17 that run are not a random sample: they are the cases that (a) map to official O-RAN WG11 S-plane test IDs, and (b) are the ones the project's research claim actually rests on. "
 "Of the faults that are <i>physically possible</i> on a software testbed, 9 of 9 fault families are exercised. The large SPEC column is the honest measure of how much room remains.",BODY))

S.append(Paragraph("2 · Standardised constants — and whether the frozen rule uses them",H1))
S.append(Paragraph("The most valuable outcome of the literature survey. The last column is checked against the <b>frozen</b> <font face='Courier'>run/decision_rule.py</font> (2026-09-17). <b>IDENTIFIED</b> means the standard value is known but the frozen rule does not use it yet; adopting it needs a re-freeze and a re-run.",BODY))
S.append(tb([
 [P("Constant",CB),P("Standardised value",CB),P("Source",CB),P("Status in the frozen rule",CB)],
 [P("Foreign-master qualification"),P("<b>FOREIGN_MASTER_THRESHOLD = 2</b> Announce within a <b>4 announce-interval</b> window (= 0.5 s at 8/s)"),P("IEEE 1588 §9.3.2.4; linuxptp <font face='Courier'>foreign.h</font>; behaviourally proven by UNH PWR.c.2.3"),P("<b>IDENTIFIED, not adopted.</b> The frozen rule still uses our own 1% transient filter (<font face='Courier'>TRANSIENT_FRACTION = 0.01</font>). This is its standard replacement.")],
 [P("Message-interval tolerance"),P("<b>±30%</b> of the stated mean, at 90% confidence"),P("IEEE 1588-2019 cl.7.7.2.1 (via Calnex PFV)"),P("<b>IDENTIFIED, not adopted.</b> The rule uses the 2× cap below.")],
 [P("Successive-interval cap"),P("Successive Sync/Announce intervals <b>must not exceed 2× the mean</b>"),P("ITU-T G.8275.1 Amd.3"),P("<b>IN RULE.</b> <font face='Courier'>CADENCE_TOLERANCE = 2.0</font>, and the standard backs this factor.")],
 [P("stepsRemoved discard"),P("Announce with <b>stepsRemoved ≥ 255</b> must be discarded"),P("UNH PWR.c.2.4; G.8275.1 maxStepsRemoved {1–255}"),P("<b>IN RULE</b>, added before the freeze. NEG-3 passes (§7.3).")],
 [P("announceReceiptTimeout"),P("<b>3</b> → 3 × 1/8 s = <b>375 ms</b> to declare Announce loss"),P("ITU-T G.8275.1 Amd.3; Cisco portDS"),P("<b>IN CONFIG.</b> Confirms the sub-2 s detection budget arithmetic.")],
 [P("Legal clockClass set"),P("<b>{6, 7, 13, 14, 135, 140, 150, 160, 165, 248, 255}</b> — anything else is a conformance failure"),P("ITU-T G.8275.1 Amd.3; Calnex Annex A"),P("<b>PARTLY.</b> The rule checks clockClass ≥ 6 (IEEE 1588 Table 5). The explicit allow-set is identified, not adopted.")],
 [P("clockAccuracy"),P("<b>0x21</b> PRTC-locked; <b>0xFE</b> non-PRTC"),P("Calnex G.8275.1 Annex A"),P("IDENTIFIED, not adopted.")],
 [P("offsetScaledLogVariance"),P("<b>0x4E5D</b> PRTC; <b>0xFFFF</b> other"),P("Calnex G.8275.1 Annex A"),P("IDENTIFIED, not adopted.")],
 [P("Transport restriction"),P("Ethernet multicast <b>only</b>; <b>VLAN tags not allowed</b>; <b>unicast prohibited</b>"),P("ITU-T G.8275.1; Calnex Annex A"),P("<b>PARTLY.</b> Domain and multicast are checked (NEG-5, NEG-11). The VLAN and unicast checks are identified, not adopted.")],
 [P("PTSF states"),P("PTSF-lossSync / lossAnnounce / lossDelayResp; port <b>ignores Announce from that source</b> while set"),P("G.8275.1/.2 §6.7.11; linuxptp"),P("IDENTIFIED, not adopted (needs live pmc telemetry).")],
],[30*mm,44*mm,44*mm,W-118*mm],hb=GRN))

S.append(PageBreak())
S.append(Paragraph("3 · ATTACK test cases",H1))
S.append(Paragraph("60 catalogued. Families A–K. O-RAN column gives the official WG11 Security Test Specification ID where one exists (ETSI TS 104 105).",BODY))

S.append(Paragraph("3.1 Announce / BMCA / rogue master",H2))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Mechanism / field",CB),P("Detector signature",CB),P("O-RAN ID",CB),P("Status",CB)],
 [P("A1"),P("Rogue grandmaster"),P("Announce with superior priority1/clockClass/accuracy/variance/priority2"),P("Unknown GM identity wins BMCA; illegal clockClass; drift >40,000 ns"),P("11.1.5.2.1"),P("RUN")],
 [P("A2"),P("GM impersonation"),P("Clone legitimate GM identity + MAC"),P("Same identity from two ports/MACs"),P("11.1.5.2.1"),P("SPEC")],
 [P("A3"),P("clockIdentity forcing"),P("Crafted identity (e.g. embedded ffff) to win tiebreak"),P("Anomalous identity byte pattern"),P("11.1.5.2.2"),P("SPEC")],
 [P("A4"),P("stepsRemoved manipulation"),P("Advertise stepsRemoved=0 to appear closer to PRTC"),P("stepsRemoved inconsistent with physical hop count"),P("—"),P("SPEC")],
 [P("A5"),P("BMCA oscillation / flapping"),P("Two near-equal crafted masters alternate wins"),P("Rapid repeated GM/port-state transitions; servo never settles"),P("—"),P("SPEC")],
 [P("A6"),P("Foreign-master table exhaustion"),P("Flood many spoofed clockIdentities to overflow foreignMasterDS (min capacity 5)"),P("Explosion of tracked foreign masters; election instability"),P("—"),P("SPEC")],
 [P("A7"),P("Announce-timeout starvation"),P("Suppress legit Announce until timeout, then inject"),P("announceReceiptTimeout expiries then rogue takeover"),P("11.1.5.3.1"),P("SPEC")],
 [P("A8"),P("alternateMasterFlag abuse"),P("Abuse optional alternate-master to inject Sync from non-elected port"),P("Sync accepted from a port that is not the elected GM"),P("—"),P("SPEC")],
],[8*mm,30*mm,50*mm,46*mm,16*mm,W-166*mm],hb=RED,statuscol=5))

S.append(Paragraph("3.2 Timestamp forgery / correctionField / replay",H2))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Mechanism / field",CB),P("Detector signature",CB),P("O-RAN ID",CB),P("Status",CB)],
 [P("B1"),P("preciseOriginTimestamp forgery"),P("Alter T1 in Follow_Up"),P("Offset step with no matching path-delay change"),P("—"),P("SPEC (A2_sync_spoof forges Sync, not Follow_Up)")],
 [P("B2"),P("originTimestamp forgery"),P("Alter T1 in one-step Sync"),P("Offset jump without delay anomaly"),P("—"),P("RUN (as A2_sync_spoof)")],
 [P("B3"),P("<b>Coherent T1+T4 attack</b>"),P("Increment Follow_Up T1 and Delay_Resp T4 together so delay math stays consistent"),P("<b>No delay anomaly</b> — documented as \"devious, hard to detect\""),P("—"),P("SPEC — high value")],
 [P("B5"),P("twoStepFlag confusion"),P("Flip twoStepFlag / send Follow_Up for a one-step Sync"),P("Follow_Up presence inconsistent with flag"),P("24.2.1.2"),P("SPEC")],
 [P("C1"),P("correctionField tamper (fwd)"),P("Modify C2 in Follow_Up"),P("Desync 100 µs–98 ms; negative path delays"),P("—"),P("SPEC")],
 [P("C3"),P("TC residence-time falsification"),P("Compromised transparent clock writes false residence"),P("correctionField inconsistent with measured residence"),P("—"),P("SPEC — needs a TC in topology")],
 [P("C4"),P("Boundary-clock compromise"),P("Compromised T-BC re-originates manipulated timing downstream"),P("Whole downstream branch desyncs coherently"),P("11.1.5.2.2"),P("RUN (as A8_rogue_bc)")],
 [P("D1"),P("Full replay"),P("Retransmit captured Sync/Follow_Up"),P("sequenceId regression; delay spikes >20 M ns"),P("—"),P("RUN (as A3_replay)")],
 [P("D2"),P("Selective / partial replay"),P("Replay only chosen messages"),P("Intermittent stale sequenceId"),P("—"),P("SPEC")],
 [P("D3"),P("Delay_Req/Resp replay"),P("Replay reverse-path exchange"),P("Asymmetric delay estimate"),P("—"),P("SPEC")],
],[8*mm,32*mm,48*mm,46*mm,14*mm,W-164*mm],hb=RED,statuscol=5))

S.append(Paragraph("3.3 Delay attacks — the hardest family",H2))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Mechanism",CB),P("Signature",CB),P("Status",CB)],
 [P("E1"),P("Static asymmetric delay"),P("MitM adds constant delay one direction only"),P("Persistent offset; RTT asymmetry α≠0"),P("IMPOSSIBLE to measure")],
 [P("E2"),P("Incremental slow-ramp"),P("Gradually growing one-way delay (e.g. 285 ns/s) to evade thresholds"),P("Slow offset drift; caught only by cyclic asymmetry"),P("IMPOSSIBLE to measure")],
 [P("E3"),P("Symmetric large-step delay"),P("Equal both-direction delay; servo overshoots (~84 ms after 200 s)"),P("Delay-variance indicator"),P("IMPOSSIBLE to measure")],
 [P("E4"),P("Cyclic / periodic delay"),P("Periodic modulation inside servo bandwidth, mimics diurnal jitter"),P("Periodic offset oscillation"),P("IMPOSSIBLE to measure")],
 [P("E6"),P("Flooding-induced queueing delay"),P("Congest queues to add asymmetric delay (~18 µs @ 83 Mbps)"),P("Piecewise-linear delay; HW timestamping bypasses it"),P("SPEC (injectable)")],
 [P("E7"),P("Link-speed asymmetry"),P("Force asymmetric speed negotiation (100→10 Mbps), ~2 µs fixed delay"),P("Abnormal speed negotiation"),P("SPEC")],
 [P("E9"),P("Slave spoofing (early Delay_Req)"),P("Inject Delay_Req with expected seq before the real slave"),P("Duplicate/early Delay_Req"),P("SPEC")],
],[8*mm,34*mm,54*mm,42*mm,W-164*mm],hb=RED,statuscol=4))
S.append(Paragraph("<b>Why the E-family is marked impossible.</b> netem <i>can</i> inject every one of these asymmetries. What cannot be done is <i>measuring</i> the resulting time error: a passive capture yields only t1 and t4; the client's t2 and t3 never appear on the wire. Detection requires live per-client <font face='Courier'>pmc</font> telemetry (now logged but not yet evaluated) or a redundant second path. This is a measurement gap, not an injection gap.",SMALL))

S.append(PageBreak())
S.append(Paragraph("3.4 DoS / resource exhaustion",H2))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Mechanism",CB),P("O-RAN ID",CB),P("Status",CB)],
 [P("F1"),P("PTP message flooding"),P("High-rate PTP frames overwhelm nodes"),P("11.1.5.1.1 / 24.2.1.1"),P("RUN (A5)")],
 [P("F2"),P("Complete packet removal"),P("Drop all PTP at an intermediate node → slave free-runs"),P("11.1.5.3.1"),P("SPEC — O-RAN mandated")],
 [P("F3"),P("Selective Delay_Req removal"),P("Drop only Delay_Req; delay estimate freezes"),P("11.1.5.3.1"),P("SPEC")],
 [P("F4"),P("ARP/MAC spoof blocking O-RU"),P("Bind attacker MAC to O-RU IP so PTP never arrives"),P("—"),P("SPEC")],
 [P("F5"),P("Crypto-engine exhaustion"),P("Bogus MACsec frames exhaust receiver crypto CPU — crypto <i>worsens</i> DoS"),P("—"),P("IMPOSSIBLE (no MACsec)")],
 [P("F6"),P("Unicast-negotiation exhaustion"),P("Flood REQUEST_UNICAST_TRANSMISSION; no requestor auth"),P("—"),P("IMPOSSIBLE (G.8275.2 only)")],
 [P("F7"),P("L1 physical flooding"),P("Physical fibre access, flood L1"),P("—"),P("IMPOSSIBLE (no PHY)")],
],[8*mm,36*mm,66*mm,22*mm,W-164*mm],hb=RED,statuscol=4))

S.append(Paragraph("3.5 Protocol-field abuse — the least-defended surface",H2))
S.append(Paragraph("These are trivially craftable, produce whole-second errors, and are almost absent from the attack literature. Our extractor already collects every field involved; none is yet exercised.",BODY))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Field",CB),P("Effect",CB),P("Status",CB)],
 [P("H1"),P("versionPTP downgrade"),P("<font face='Courier'>versionPTP</font>"),P("Messages dropped; slave free-runs"),P("SPEC")],
 [P("H2"),P("Domain crossing"),P("<font face='Courier'>domainNumber</font>"),P("Cross-domain injection or forced discard"),P("SPEC")],
 [P("H3"),P("currentUtcOffset manipulation"),P("<font face='Courier'>currentUtcOffset</font>"),P("<b>Whole-second UTC jump</b>, no servo anomaly"),P("SPEC — novel")],
 [P("H4"),P("leap61 / leap59 injection"),P("leap flags"),P("<b>Spurious ±1 s step</b>"),P("SPEC — novel")],
 [P("H5"),P("Traceability stripping"),P("<font face='Courier'>timeTraceable</font>/<font face='Courier'>frequencyTraceable</font>"),P("Tricks QL/holdover logic"),P("SPEC — novel")],
 [P("H6"),P("ptpTimescale confusion"),P("<font face='Courier'>ptpTimescale</font>"),P("Epoch misinterpretation (~37 s TAI-UTC)"),P("SPEC")],
 [P("H8"),P("PATH_TRACE TLV abuse"),P("PATH_TRACE"),P("Hide timing loops / fake topology"),P("SPEC")],
 [P("H10"),P("AUTHENTICATION TLV strip/downgrade"),P("Annex P TLV"),P("Force fallback to unauthenticated PTP"),P("SPEC")],
 [P("H11"),P("Management SET abuse"),P("§15 management msgs"),P("In-band dataset reconfiguration"),P("SPEC")],
 [P("H12"),P("Malformed / fuzzed frames"),P("Header & TLV lengths"),P("Parser crash; daemon fault"),P("SPEC — O-RAN 24.2.1.2")],
 [P("H13"),P("CVE-2021-3570 (linuxptp)"),P("Forwarded msg length check"),P("Daemon crash / info leak on a BC"),P("SPEC")],
],[8*mm,42*mm,34*mm,48*mm,W-164*mm],hb=RED,statuscol=4))

S.append(Paragraph("3.6 Below-the-wire and cross-layer",H2))
S.append(tb([
 [P("ID",CB),P("Attack",CB),P("Why it matters",CB),P("Status",CB)],
 [P("G1–G4"),P("GNSS jam / spoof / meaconing / PRTC firmware compromise"),P("Upstream of PTP entirely; receiver reports healthy while time is wrong"),P("IMPOSSIBLE (no GNSS; RF illegal outside a chamber)")],
 [P("I1–I3"),P("<b>Kernel-level time interception</b> — hook clock_gettime / ADJ_FREQUENCY"),P("<b>Defeats every packet-based detector and all crypto.</b> The servo reports \"locked\" while time is wrong. Sharpest challenge to this entire approach."),P("SPEC — novel, high value")],
 [P("I4–I5"),P("PHC ioctl exploit (CVE-2025-21814), adjtimex leak (CVE-2018-11508)"),P("Kernel fault / privilege bypass"),P("SPEC")],
 [P("J1–J3"),P("SyncE ESMC QL spoofing, timing-loop induction, QL-DNU injection"),P("Hijacks frequency-source selection; explicitly noted as uncovered by O-RAN WG11"),P("IMPOSSIBLE (no PHY/ESMC)")],
 [P("J4–J6"),P("VLAN/MAC spoofing, MACsec bypass/downgrade"),P("S-plane VLAN often unprotected; enables most other families"),P("SPEC (VLAN) / IMPOSSIBLE (MACsec)")],
 [P("K1–K4"),P("LLS-C1 direct-link injection; LLS-C2/C3 BC-chain poisoning; LLS-C4 local-GNSS spoof; cross-domain handover desync"),P("Topology-specific composites"),P("K2 RUN (same run as C4 / A8_rogue_bc); others SPEC/IMPOSSIBLE")],
],[13*mm,54*mm,62*mm,W-164*mm],hb=RED,statuscol=3))

S.append(PageBreak())
S.append(Paragraph("4 · CONFORMANCE and NEGATIVE test cases",H1))
S.append(Paragraph("From the UNH-IOL IEEE 1588 conformance test plans and ITU-T G.8275.1 Amd.3. These are <i>protocol-legality</i> tests — Class A in our threshold taxonomy, meaning the standard states the exact pass criterion and no calibration is required.",BODY))
S.append(tb([
 [P("UNH ID",CB),P("Test",CB),P("Pass criterion",CB),P("Our status",CB)],
 [P("c.1.1 / c.1.2"),P("logAnnounceInterval / logSyncInterval"),P("Interval within ±30% of mean at 90% CI; logMessageInterval field correct"),P("PARTLY. Cadence checked with the G.8275.1 2× cap, not the ±30% criterion")],
 [P("c.1.3"),P("announceReceiptTimeout"),P("Value 3; must not claim master before timeout, must by N intervals"),P("SPEC")],
 [P("c.1.5"),P("priority1 / priority2"),P("Defaults in Announce; G.8275.1 fixes priority1=128"),P("RUN")],
 [P("c.1.7"),P("<b>domainNumber isolation</b>"),P("Announce in a non-matching domain <b>must be ignored</b>"),P("<b>RUN</b> as NEG-5: PASS")],
 [P("c.2.1"),P("Disqualify by own clockIdentity"),P("Announce whose sourcePortIdentity matches DUT's own identity must be rejected (loop protection)"),P("SPEC")],
 [P("c.2.2"),P("Disqualify by most recent"),P("Only the latest Announce per source affects selection"),P("SPEC")],
 [P("c.2.3"),P("<b>Foreign-master window</b>"),P("≥2 Announce within 4 intervals to qualify; &lt;2 must be ignored; foreignMasterDS ≥5 records"),P("IDENTIFIED, not adopted (frozen rule uses a 1% transient filter)")],
 [P("c.2.4"),P("stepsRemoved limit"),P("≥255 must be discarded; 254 accepted"),P("<b>RUN</b> as NEG-3: PASS")],
 [P("c.2.5"),P("alternateMasterFlag"),P("Announce with flag TRUE must be discarded"),P("<b>RUN</b> as NEG-2: PASS")],
 [P("c.2.6"),P("Dataset comparison"),P("Ordering: priority1 → clockClass → clockAccuracy → offsetScaledLogVariance → priority2 → grandmasterIdentity"),P("SPEC. The testbed now runs the G.8275.1 <i>alternate</i> BMCA (dataset_comparison G.8275.x), which orders differently; this default-BMCA case is not tested")],
 [P("c.2.8"),P("State decision algorithm"),P("Correct BMC_MASTER / BMC_PASSIVE / BMC_SLAVE outputs"),P("SPEC")],
 [P("c.2.9"),P("stepsRemoved ±1 rule"),P("If received ≥ own+1 → yield; ≤ own−1 → continue announcing"),P("SPEC")],
 [P("c.7.1"),P("Mean path delay"),P("Correct computation from Delay_Req/Delay_Resp"),P("Partially RUN")],
 [P("—"),P("<b>PTSF states</b>"),P("lossSync / lossAnnounce / lossDelayResp; port ignores Announce from a failed source"),P("SPEC")],
 [P("—"),P("<b>Transport legality</b>"),P("Ethernet multicast only; VLAN tags not allowed; unicast prohibited"),P("RUN: multicast (NEG-11) and domain (NEG-5). SPEC: VLAN and unicast")],
],[16*mm,38*mm,70*mm,W-164*mm],hb=BLUE,statuscol=3))

S.append(Paragraph("5 · BENIGN fault scenarios — the look-alikes",H1))
S.append(Paragraph("58 catalogued. These are the events that <b>resemble attacks but are not</b>, and they are where a detector actually fails in deployment. Our benign coverage is the weakest part of the work.",BODY))
S.append(tb([
 [P("ID",CB),P("Benign scenario",CB),P("Observable change",CB),P("Mistakable for",CB),P("Status",CB)],
 [P("B-01"),P("Planned GM failover"),P("New grandmasterIdentity; brief UNCALIBRATED→SLAVE; no clockClass degradation"),P("A1 rogue master"),P("RUN")],
 [P("B-02"),P("<b>Unplanned GM failover</b>"),P("Announce timeout → BMCA reselect; clockClass may pass 7→52"),P("Announce DoS / suppression"),P("<b>RUN</b> — 12/12 correct UNKNOWN")],
 [P("B-03"),P("GM cold reboot"),P("clockClass walks <b>248→52→7→6</b> monotonically over minutes"),P("Spoofer injecting degraded Announce"),P("SPEC")],
 [P("B-05"),P("GM priority reconfiguration"),P("Attribute change, no clockClass change; deterministic domain-wide reselect"),P("Priority-manipulation attack"),P("SPEC")],
 [P("B-06"),P("New GM added to domain"),P("New clockIdentity; commissioning Announce burst"),P("Rogue GM insertion"),P("SPEC")],
 [P("B-08"),P("<b>Dual-GM BMCA flapping</b>"),P("Repeated GM flips between two <i>known</i> GMs; O-RAN calls this \"S-1 Grandmaster flapping\""),P("Intermittent rogue-master attack"),P("SPEC — high value")],
 [P("B-09"),P("GM clockIdentity change after card swap"),P("\"New\" GM at same topological position, same attributes"),P("GM impersonation"),P("SPEC")],
 [P("B-10"),P("GNSS loss → reselect to alternate GM"),P("Phase step equal to known cTE difference between GM paths; reproducible"),P("Time-shift attack"),P("IMPOSSIBLE (no GNSS)")],
 [P("B-11"),P("Commissioning Announce burst"),P("Rate spike correlated with site power restore, decays monotonically"),P("Announce-flood DoS"),P("SPEC")],
 [P("—"),P("PDV / congestion"),P("meanPathDelay variance, load-correlated, no protocol anomaly"),P("Delay attack"),P("RUN")],
 [P("—"),P("Topology / BC reconfiguration"),P("stepsRemoved change consistent with new hop count"),P("Rogue BC insertion"),P("RUN")],
 [P("—"),P("<b>Legitimate BC replacement</b>"),P("New BC identity in path, provisioned"),P("A8 rogue BC"),P("<b>RUN</b> — 12/12 FP, schema limit")],
 [P("—"),P("Real leap-second event"),P("Genuine leap61 flag and 1 s step"),P("H4 leap injection"),P("SPEC")],
 [P("—"),P("SyncE / EEC degradation, oscillator drift, holdover"),P("QL downgrade; drift within mask"),P("GNSS jam"),P("IMPOSSIBLE (no PHY / oscillator)")],
],[12*mm,40*mm,58*mm,32*mm,W-164*mm],hb=GRN,statuscol=4))

S.append(PageBreak())
S.append(Paragraph("6 · What we actually built and ran",H1))
S.append(tb([
 [P("Scenario",CB),P("Truth",CB),P("O-RAN / source ID",CB),P("How produced on the wire",CB),P("Reps",CB)],
 [P("baseline"),P("BENIGN"),P("—"),P("All nodes nominal, GM-A → BC → 3 O-RU clients"),P("12")],
 [P("A1_rogue_master"),P("ATTACK"),P("11.1.5.2.1"),P("ptp4l instance, randomised off-allow-list identity, randomised superior priority2 (1–90) and clockClass (6/7/13), self-announcing"),P("12")],
 [P("A2_sync_spoof"),P("ATTACK"),P("B1/B2 family"),P("scapy-forged Sync with a randomised implausible originTimestamp and burst; never sends Announce"),P("12")],
 [P("A3_replay"),P("ATTACK"),P("D1"),P("Live slice captured then retransmitted with tcpreplay; randomised slice size (300–500 frames) and loop count (4–10)"),P("12")],
 [P("A5_dos_flood"),P("ATTACK"),P("11.1.5.1.1 / 24.2.1.1"),P("scapy PTP flood; randomised burst (100–300 frames) and gap (30–70 ms)"),P("12")],
 [P("A8_rogue_bc"),P("ATTACK"),P("11.1.5.2.2"),P("<b>Two-port</b> ptp4l (randomised priority2 105–118) slaving upstream, relaying downstream with stepsRemoved incremented"),P("12")],
 [P("B2_gm_failover"),P("BENIGN"),P("B-01"),P("GM-A withdrawn; BMCA elects GM-B, which IS on the allow-list, maintenance window open"),P("12")],
 [P("B3_pdv_congestion"),P("BENIGN"),P("—"),P("netem normal-distribution delay (3/5/8 ms) ± jitter (2/3/4 ms), randomised, on client links"),P("12")],
 [P("B7_topology_change"),P("BENIGN"),P("—"),P("RU3 link bounced and re-homed during an open maintenance window"),P("12")],
 [P("<b>B_bc_replacement</b> <i>(new)</i>"),P("BENIGN"),P("— (benign catalogue: BC replacement)"),P("Provisioned boundary clock swapped for a different, equally provisioned BC identity — the hardest benign case in the catalogue"),P("12")],
 [P("<b>B_unplanned_failover</b> <i>(new)</i>"),P("UNKNOWN"),P("B-02"),P("GM-A crashes with <b>no</b> maintenance window; BMCA elects GM-B. Packet-indistinguishable from a suppression attack — the correct answer is abstention, not a verdict"),P("12")],
],[34*mm,16*mm,26*mm,74*mm,W-160*mm],hb=NAVY))
S.append(Paragraph("<b>11 scenarios × 12 replicates = 132 admissible runs</b> (replicates 30–41). Every replicate draws fresh attacker identities, priorities, timings and burst sizes from <font face='Courier'>run/randparams.py</font>, seeded by replicate number — so the replicates are genuinely independent and the confidence intervals in §7 mean what they state. This closes the &quot;runs are not independent&quot; limitation of the previous revision, which is why the prior CIs were labelled optimistic and these are not.",SMALL))

S.append(Paragraph("7 · Validation results",H1))
S.append(Paragraph("7.1 &nbsp; Randomised campaign — 132 runs",H2))
S.append(tb([
 [P("Metric",CB),P("Value",CB),P("95% Wilson CI",CB),P("n",CB)],
 [P("Sensitivity (attack recall)"),P("<b>1.000</b>"),P("[0.940, 1.000]"),P("60")],
 [P("Specificity — <b>all</b> decidable benign runs (TN 48, FP 12)"),P("<b>0.800</b>"),P("[0.682, 0.882]"),P("60")],
 [P("Specificity — excluding the known <font face='Courier'>B_bc_replacement</font> schema limitation"),P("<b>1.000</b>"),P("[0.926, 1.000]"),P("48")],
 [P("Abstention correctness (ambiguous benign → UNKNOWN)"),P("<b>1.000</b>"),P("[0.757, 1.000]"),P("12")],
 [P("Fault-attribution accuracy"),P("0.817"),P("[0.701, 0.894]"),P("60")],
],[70*mm,20*mm,30*mm,W-120*mm],hb=GRN))
S.append(Paragraph("Confusion — attack: TP 60, FN 0, UNKNOWN 0 · decidable benign: TN 48, FP 12, UNKNOWN 0 · ambiguous benign: 12 correct abstentions, 0 over-claims, 0 false alarms. Per-fault attribution: A1 8/12 · A2 12/12 · A3 12/12 · A5 12/12 · A8 5/12. Method: rule frozen (18 SHA-256 hashed artefacts, <font face='Courier'>verify_frozen.sh</font> passed before every run) at 2026-09-17T04:49:33Z; earlier replicates exposed defects, were used to fix them, and are excluded; replicates 30–41 produced after the final freeze with the rule untouched. Zero infrastructure failures.",SMALL))
S.append(Spacer(1,2*mm))
S.append(Paragraph("<b>Where it loses, and why nothing was patched.</b> All 12 specificity false positives are the single scenario <font face='Courier'>B_bc_replacement</font>: the scenario provisions the replacement BC in the run's context file (<font face='Courier'>expected_bc_identity_secondary</font>), but the frozen rule reads only the single <font face='Courier'>expected_bc_identity</font>, so the legitimate replacement is read as a rogue BC. That is a schema limitation, not a detection failure — and fixing it means a BC allow-<i>list</i>, a re-freeze and a re-run, so it is reported here rather than folded into the number. "
 "The attribution misses are signature overlap, not defects: A1→A3 (×4) and A8→A3 (×7) both occur because inserting a rogue master or a rogue BC makes downstream clients re-parent, which produces <i>real</i> sequenceId restarts that the A3 clause matches first. <b>The binary ATTACK verdict was correct in all 60.</b> Re-ordering the rule after seeing the result would convert validation data into development data, so it was left alone.",BODY))

S.append(Paragraph("7.2 &nbsp; Cross-domain check on real TIMESAFE hardware captures",H2))
S.append(Paragraph("The rule was built only on the software testbed and then applied, unchanged and frozen (SHA-256 <font face='Courier'>c362e110…dae8a985</font>), to six real hardware attack captures it had never seen.",BODY))
S.append(tb([
 [P("Capture",CB),P("Packets",CB),P("Caught by standards / protocol rules alone",CB),P("Verdict",CB)],
 [P("2024-10-16-announce_attack"),P("260,525"),P("YES — clockClass&lt;6 ×24,653 (IEEE 1588 Table 5) and priority1≠128 ×24,653 (G.8275.1)"),P("ATTACK")],
 [P("2024-10-08-announce_attack_1"),P("6,024"),P("YES — clockClass&lt;6 ×457 and priority1≠128 ×457"),P("ATTACK")],
 [P("prod_successful_announce_attack_ptp"),P("13,565"),P("YES — clockClass&lt;6 ×39"),P("ATTACK")],
 [P("2024-10-08-sync_attack_1"),P("8,440"),P("YES — sequenceId regression ×2,500 (IEEE 1588 cl.11.3)"),P("ATTACK")],
 [P("2024-10-08-sync_attack_singlestep_1"),P("9,078"),P("YES — sequenceId regression ×2,455"),P("ATTACK")],
 [P("<b>15min_announce_attack</b>"),P("46,998"),P("<b>NO</b> — every Announce field conformant, no sequence regression. Needs the provisioned allow-list to resolve"),P("ATTACK")],
],[46*mm,17*mm,84*mm,W-147*mm],hb=BLUE))
S.append(Paragraph("<b>6 of 6 classified ATTACK by the frozen rule; 5 of 6 on standards and protocol rules alone</b> — three on Announce-field legality, two on sequenceId monotonicity — with nothing fitted and no allow-list. The single case that standards alone cannot reach is a <i>healthy-looking spoof</i>: conformant priority1 and clockClass, monotonic sequence numbers. That is precisely the hard case the catalogue predicts is indistinguishable by attribute inspection, and it is the case that justifies carrying provisioned context at all. Reported as a boundary, not hidden.",SMALL))

S.append(Paragraph("7.3 &nbsp; Conformance-negative tests — 7/7",H2))
S.append(Paragraph("Each crafted violation must be caught <i>by its own cited clause</i>, not merely produce the right verdict for an unrelated reason. A fixture defect that made five of the six fire on a spurious sequenceId collision instead of on their own clause was found and fixed before the run.",BODY))
S.append(tb([
 [P("Case",CB),P("Clause it must fire on",CB),P("Expected",CB),P("Result",CB)],
 [P("NEG-1 illegal clockClass 0"),P("IEEE 1588-2019 Table 5 (0–5 reserved)"),P("ATTACK"),P("PASS (A1)")],
 [P("NEG-2 alternateMasterFlag"),P("UNH PWR.c.2.5 — must be discarded"),P("ATTACK"),P("PASS (A8)")],
 [P("NEG-3 stepsRemoved ≥ 255"),P("UNH PWR.c.2.4 — must be discarded"),P("ATTACK"),P("PASS (A4)")],
 [P("NEG-5 wrong domain"),P("G.8275.1 domain 24–43 / UNH c.1.7"),P("ATTACK"),P("PASS (A5)")],
 [P("NEG-11 wrong multicast group"),P("G.8275.1 forwardable multicast 01:1B:19:00:00:00"),P("ATTACK"),P("PASS (A5)")],
 [P("NEG-15 priority1 ≠ 128"),P("G.8275.1 fixes priority1 = 128"),P("ATTACK"),P("PASS (A1)")],
 [P("CONTROL all-legitimate"),P("(no violation present)"),P("BENIGN"),P("PASS")],
],[44*mm,66*mm,20*mm,W-130*mm],hb=GRN))

S.append(Paragraph("8 · What these numbers do NOT establish",H1))
S.append(tb([
 [P("Limitation",CB),P("Detail",CB)],
 [P("<b>A provisioned BC swap is misread as an attack</b>"),P("The replacement BC is provisioned in the context file (<font face='Courier'>expected_bc_identity_secondary</font>), but the frozen rule reads only the single <font face='Courier'>expected_bc_identity</font>, so the legitimate replacement is flagged A8. <b>This one scenario accounts for all 12 false positives and is the entire gap between specificity 0.800 and 1.000.</b> The fix is a BC allow-<i>list</i>; it requires re-freezing the rule and re-running the campaign, so it is future work and is deliberately not folded into the reported number.")],
 [P("<b>Attribution is weaker than detection</b>"),P("Attribution 0.817 against sensitivity 1.000. A1→A3 (×4) and A8→A3 (×7): inserting a rogue master or BC re-parents downstream clients, producing genuine sequenceId restarts that the A3 clause matches first. The binary verdict is unaffected, but the <i>named</i> fault can be wrong, which matters for automated remediation.")],
 [P("<b>Self-designed attacks</b>"),P("The testbed attacks were written by the same author as the detector — an easier test than an independent adversary. Partly mitigated by §7.2: six real TIMESAFE hardware captures, authored elsewhere, were classified correctly by the frozen rule.")],
 [P("<b>Provisioned context is handed to the rule</b>"),P("The allow-list tells the rule which clocks are legitimate. This is genuine operator configuration, but it narrows the claim to \"detect unprovisioned or non-conformant clocks\" rather than \"detect attacks from traffic alone\". §7.2 quantifies the dependence exactly: 5 of 6 real captures need no allow-list, 1 of 6 does.")],
 [P("<b>10% catalogue coverage</b>"),P("17 of 168 catalogued cases executed. The 106 SPEC cases are the honest measure of remaining work.")],
 [P("<b>No hardware-dependent fault tested</b>"),P("GNSS spoof/jam, GNSS holdover, SyncE/EEC, oscillator drift, and all delay-attack <i>measurement</i> remain untested for physical reasons stated in §3.3 and §3.6.")],
],[42*mm,W-42*mm],hb=RED))

S.append(Paragraph("9 · Highest-value next tests — and what this revision closed",H1))
S.append(Paragraph("The first three rows were the top priorities of the previous revision. They are now executed, and each one tested the result harder: randomisation made the replicates independent so the CIs are honest, and the two hard benign cases took specificity from a clean 1.000 down to 0.800. That is the point of running them.",BODY))
S.append(tb([
 [P("Priority",CB),P("Test",CB),P("Status",CB),P("Outcome / why",CB)],
 [P("1"),P("Randomise attack parameters per replicate"),P("<b>RUN</b>"),P("Done via <font face='Courier'>run/randparams.py</font>, seeded per replicate. The identity-based checks (A1/A2/A8) held; the rate-based A5 check held at 12/12. The CIs in §7.1 are now honest rather than optimistic.")],
 [P("2"),P("Legitimate BC replacement"),P("<b>RUN</b>"),P("Failed, as a specificity FP — and the failure is a context-schema limit, not a detection limit. This is the single most valuable negative result in the campaign.")],
 [P("3"),P("Unplanned GM failover (B-02)"),P("<b>RUN</b>"),P("Passed as 12/12 correct abstentions. The rule refuses to guess where the packets genuinely cannot decide — the behaviour the whole fail-closed design exists for.")],
 [P("4"),P("Conformance negatives (c.1.7, c.2.4, c.2.5)"),P("<b>RUN</b>"),P("7/7, each firing on its own cited clause (§7.3).")],
 [P("5"),P("BC allow-<i>list</i> in the context schema"),P("SPEC"),P("The direct fix for priority 2. Needs a re-freeze and a full re-run of the 132-run campaign — it cannot be retrofitted to this result.")],
 [P("6"),P("Packet removal / selective interception (F2/F3)"),P("SPEC"),P("O-RAN mandated test 11.1.5.3.1 — still not covered at all.")],
 [P("7"),P("Malformed / fuzzed input (H12)"),P("SPEC"),P("O-RAN mandated test 24.2.1.2 — robustness of the parser itself.")],
 [P("8"),P("Whole-second field abuse (H3/H4/H5)"),P("SPEC"),P("Trivial to craft, produce 1 s errors, essentially absent from the literature, and every field is already collected by our extractor.")],
 [P("9"),P("Coherent T1+T4 attack (B3)"),P("SPEC"),P("Documented as hard to detect because it leaves delay math intact. Directly probes the known blind spot.")],
 [P("10"),P("Kernel-level time interception (I1–I3)"),P("SPEC"),P("Defeats every packet-based detector and all cryptography. The sharpest challenge to this entire approach.")],
],[14*mm,44*mm,14*mm,W-72*mm],hb=BLUE,statuscol=2))

S.append(Paragraph("10 · Sources",H1))
S.append(tb([
 [P("Source",CB),P("Used for",CB)],
 [P("O-RAN WG11 Security Test Specification — ETSI TS 104 105 V7.0.0"),P("Official S-plane security test IDs 11.1.5.1.1/.2, 11.1.5.2.1/.2, 11.1.5.3.1/.2, 24.2.1.1/.2")],
 [P("O-RAN WG11 Threat Modeling — ETSI TR 104 106 V3.0.0"),P("Threat identifiers T-SPLANE-01…04")],
 [P("UNH-IOL IEEE 1588 Default PTP Profiles Conformance Test Plan v0.0.2"),P("Numbered conformance tests c.1.x, c.2.x, c.7.x; foreign-master window behavioural proof")],
 [P("IEEE 1588-2019"),P("cl.7.7.2.1 ±30% interval tolerance; §9.3.2.4 foreign master; Table 5 clockClass; cl.11.3 Delay_Resp sequenceId; §15 management; §16 TLVs; Annex P")],
 [P("ITU-T G.8275.1 + Amd.3"),P("Profile values, alternate BMCA, clockClass ladder, maxStepsRemoved, successive-interval cap")],
 [P("ITU-T G.8271.1 / G.8272 / G.8273.2 / G.8260 / G.8261 / G.8262 / G.8264"),P("Network limits, PRTC accuracy, clock classes, metric definitions, wander, SyncE")],
 [P("TIMESAFE — ACM ToPS 2025, doi:10.1145/3775060 (arXiv:2412.13049)"),P("Fronthaul attack behaviour; real hardware captures; ~2 s cell-drop timeline")],
 [P("PTPsec — arXiv:2401.10664"),P("Cyclic path-asymmetry analysis for delay-attack detection")],
 [P("Springer Cybersecurity s42400-021-00080-y"),P("PTP attack taxonomy; why delay attacks defeat MACsec/Annex P")],
 [P("Concordia NCC — S-plane in O-RAN: Overview, Security, Research Directions"),P("Threats T1–T8; LLS-C topology-specific attacks")],
 [P("TUM — Feasible Time Delay Attacks Against PTP"),P("Flooding-induced and link-speed asymmetry delay attacks")],
 [P("MDPI Electronics 9/9/1398"),P("Coherent T1+T4 time-reference attack; correctionField tampering")],
 [P("arXiv:2510.06421 — Breaking Precision Time"),P("Kernel/OS-level time interception; CVE-2025-21814, CVE-2018-11508")],
 [P("CVE-2021-3570 / USN-6097-1"),P("linuxptp forwarding length-check vulnerability")],
 [P("linuxptp v4.0 source (foreign.h, ds.h, tlv.h)"),P("FOREIGN_MASTER_THRESHOLD=2; pmc datasets; PORT_STATS_NP / PORT_SERVICE_STATS_NP")],
 [P("Calnex / Microchip / Meinberg / Cisco / Nokia application notes"),P("Profile restatements, clockClass semantics, benign failure modes, operator practice")],
],[62*mm,W-62*mm],hb=GREY))
S.append(Spacer(1,2*mm))
S.append(Paragraph("<i>Full catalogues (60 attack cases, 50+ conformance tests, 58 benign scenarios) with complete URLs are provided as accompanying markdown files. This document is the systematic summary.</i>",SMALL))

doc=SimpleDocTemplate("/mnt/user-data/outputs/ORAN_SPlane_Master_Test_Catalogue.pdf",pagesize=A4,
    leftMargin=16*mm,rightMargin=16*mm,topMargin=14*mm,bottomMargin=14*mm,
    title="O-RAN S-Plane Master Test Case Catalogue and Validation Record",author="Samsung PRISM Project")
doc.build(S)
print("built")
