# -*- coding: utf-8 -*-
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, ListFlowable, ListItem, HRFlowable, KeepTogether)

NAVY=colors.HexColor("#14304f"); ACCENT=colors.HexColor("#2c6fbb"); LIGHT=colors.HexColor("#eef3f9")
GREY=colors.HexColor("#5c6470"); RULE=colors.HexColor("#c9d4e2"); GOOD=colors.HexColor("#1a7f4b")
BAD=colors.HexColor("#b5480f"); WARNBG=colors.HexColor("#fdf0e6"); GOODBG=colors.HexColor("#eaf5ee")

ss=getSampleStyleSheet(); S={}
S['title']=ParagraphStyle('t',parent=ss['Title'],fontName='Helvetica-Bold',fontSize=25,textColor=NAVY,leading=29,spaceAfter=6)
S['sub']  =ParagraphStyle('s',parent=ss['Normal'],fontName='Helvetica',fontSize=12.5,textColor=GREY,leading=17,alignment=1)
S['h1']   =ParagraphStyle('h1',parent=ss['Heading1'],fontName='Helvetica-Bold',fontSize=18,textColor=NAVY,spaceBefore=6,spaceAfter=9,leading=22)
S['h2']   =ParagraphStyle('h2',parent=ss['Heading2'],fontName='Helvetica-Bold',fontSize=12.5,textColor=ACCENT,spaceBefore=11,spaceAfter=4,leading=16)
S['body'] =ParagraphStyle('b',parent=ss['Normal'],fontName='Helvetica',fontSize=10.5,leading=15.5,spaceAfter=7,alignment=TA_JUSTIFY,textColor=colors.HexColor("#1d2229"))
S['small']=ParagraphStyle('sm',parent=S['body'],fontSize=9,leading=12.5,textColor=GREY)
S['cell'] =ParagraphStyle('c',parent=S['body'],fontSize=9.4,leading=12.5,spaceAfter=0,alignment=0)
S['cellh']=ParagraphStyle('ch',parent=S['cell'],fontName='Helvetica-Bold',textColor=colors.white)
S['big']  =ParagraphStyle('big',parent=S['body'],fontSize=13,leading=18,textColor=NAVY,fontName='Helvetica-Bold')

story=[]; A=story.append
def P(t,st='body'): A(Paragraph(t,S[st]))
def H1(t): A(Paragraph(t,S['h1']))
def H2(t): A(Paragraph(t,S['h2']))
def SP(h=6): A(Spacer(1,h))
def BUL(items,st='body'):
    A(ListFlowable([ListItem(Paragraph(i,S[st]),leftIndent=8) for i in items],
      bulletType='bullet',start='•',leftIndent=13,bulletColor=ACCENT,bulletFontName='Helvetica',
      bulletFontSize=8,spaceBefore=2,spaceAfter=7))
def NUM(items):
    A(ListFlowable([ListItem(Paragraph(i,S['body']),leftIndent=8) for i in items],
      bulletType='1',leftIndent=15,bulletColor=NAVY,spaceBefore=2,spaceAfter=7))
def TBL(rows,widths,hi=None,fs=9.4):
    data=[]
    for ri,row in enumerate(rows):
        out=[Paragraph(str(c),S['cellh'] if ri==0 else S['cell']) for c in row]
        data.append(out)
    t=Table(data,colWidths=widths,repeatRows=1)
    cmds=[('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
          ('GRID',(0,0),(-1,-1),0.4,RULE),('VALIGN',(0,0),(-1,-1),'TOP'),
          ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
          ('TOPPADDING',(0,0),(-1,-1),4.5),('BOTTOMPADDING',(0,0),(-1,-1),4.5)]
    if hi:
        for r in hi: cmds.append(('BACKGROUND',(0,r),(-1,r),GOODBG))
    t.setStyle(TableStyle(cmds)); A(t)
def BOX(t,bg=GOODBG,bd=GOOD):
    p=Paragraph(t,S['body']); tb=Table([[p]],colWidths=[168*mm])
    tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('BOX',(0,0),(-1,-1),0.7,bd),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])); A(tb); SP(6)

def _page(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE); canvas.setLineWidth(0.5)
    canvas.line(20*mm,16*mm,190*mm,16*mm)
    canvas.setFont('Helvetica',8); canvas.setFillColor(GREY)
    canvas.drawString(20*mm,12*mm,"O-RAN S-Plane Self-Healing — Project Walkthrough")
    canvas.drawRightString(190*mm,12*mm,"Page %d"%doc.page)
    canvas.restoreState()

# ---------- COVER ----------
SP(46)
A(Paragraph("Self-Healing 5G Timing Security",S['title']))
A(Paragraph("A plain-English walkthrough of the whole project — every part, the data, and the results",S['sub']))
SP(14); A(HRFlowable(width="62%",thickness=1.1,color=ACCENT,hAlign='CENTER')); SP(14)
A(Paragraph("Project: AI-Native Self-Healing O-RAN Network using a Digital Twin",S['sub']))
A(Paragraph("Prepared for the team — no telecom background needed",S['sub']))
A(Paragraph("Revised 17 September 2026 (supersedes the 16 August edition)",S['sub']))
SP(20)
TBL([["Item","Status"],
     ["Current phase","Standards-based software testbed (ITU-T G.8275.1) and a 132-run validation. Rule frozen 17 Sep 2026, 04:49:33 UTC"],
     ["Headline result","Attacks caught: <b>60 of 60</b>. Benign faults called correctly: <b>48 of 60</b> (0.800). Honest \"can't tell\": <b>12 of 12</b>. Real hardware attack captures flagged: <b>6 of 6</b>"],
     ["Earlier phase (August)","Machine-learning pipeline. Commit 4e4bd16, tag known-good-2026-08-07. Its real-data percentages are <b>no longer used as evidence</b> (see §5)"],
     ["Hardware (Tier-3)","Not started — the next phase"],
     ["Note","Most build work was AI-generated under human direction. Every number here was re-checked against the raw files"]],
    [46*mm,122*mm])
A(PageBreak())

# ---------- 1. THE STORY ----------
H1("1 · The project in 30 seconds")
P("A 5G base station is split into pieces that talk over a link called the <b>fronthaul</b>. Those "
  "pieces must agree on <b>time</b> extremely closely. The ITU-T standards allow about <b>1.5 millionths of a second</b> "
  "of time error at the end of the network (G.8271.1), and they grade individual clocks in tens of "
  "<b>nanoseconds</b> (G.8273.2: 50, 20 or 10 ns). In published tests, a timing attack on the fronthaul dropped the cell "
  "about <b>2 seconds</b> after it started (TIMESAFE, ACM 2025).")
P("The clock is shared using a protocol called <b>PTP</b> (IEEE 1588), which has no built-in security in normal "
  "use. So a faulty or malicious clock can knock a base station offline. The hard part: a harmless fault "
  "(a planned clock switch-over, network congestion) and a deliberate attack can look <b>almost identical</b>.")
BOX("<b>What the project is building:</b> software that watches the timing, decides whether a problem is a "
    "<b>harmless fault</b> or a <b>real attack</b>, and then heals the network safely. If it can't tell, it says "
    "<b>\"UNKNOWN\"</b> instead of guessing. <b>What has been validated so far</b> is the <i>decision</i> "
    "part: fault or attack, on a standards-correct software testbed and on real hardware captures. The "
    "healing loop and digital twin were built in August, but they are not part of the September validation.")
H2("Where this sits in the bigger picture")
BUL(["<b>Field:</b> 5G / O-RAN network security.",
     "<b>Zoom in:</b> the Open Fronthaul link between the radio and the baseband.",
     "<b>Zoom in again:</b> the <b>S-plane</b> — the traffic that carries the clock. That is our topic."])
H2("What is new about it")
P("Telling faults from attacks is not a new idea in general, and GPS spoof-versus-outage in 5G was "
  "published in 2026. What is still open is doing it for the <b>PTP messages on the O-RAN fronthaul</b>. The main "
  "prior work, TIMESAFE, <i>says</i> that legitimate master changes and topology changes can resemble attacks, "
  "but its \"benign\" data is only healthy traffic. It never tests faulty-but-harmless events. That untested "
  "claim is the gap this project works on.")
A(PageBreak())

# ---------- 2. THE CORE PROBLEM ----------
H1("2 · The core problem: fault vs attack")
P("When timing goes wrong, the symptom can look the same whatever the cause. The correct response, though, is "
  "<b>opposite</b> — so telling them apart is the whole game.")
TBL([["Harmless fault (benign)","Malicious attack"],
     ["<b>B2</b> — planned switch to the backup grandmaster during maintenance","<b>A1</b> — a rogue device announces itself as the best clock"],
     ["<b>B3</b> — network congestion adds delay and jitter","<b>A5</b> — an attacker floods the link with PTP messages"],
     ["<b>B7</b> — a link is re-wired during maintenance","<b>A8</b> — a rogue boundary clock is inserted into the path"],
     ["Planned boundary-clock replacement","<b>A3</b> — old messages are recorded and replayed"],
     ["GPS signal lost, clock rides its backup <i>(needs hardware)</i>","<b>A2</b> — forged Sync messages carry a fake time"]],
    [84*mm,84*mm])
P("For a fault, the right move is usually to <b>wait it out</b>, because the real clock returns. For "
  "an attack, the right move is to <b>isolate the bad source and switch away</b>. Do the wrong one and "
  "you make the outage worse.")
BOX("<b>The headline experiment is A1 vs B2.</b> In both, a new \"best clock\" appears. The packets alone "
    "cannot say which is which. The difference is <b>context the operator already has</b>: is that clock on "
    "the approved list (the <i>allow-list</i>), and is a maintenance window open?", LIGHT, ACCENT)
A(PageBreak())

# ---------- 2b. PTP IN PLAIN WORDS ----------
H1("3 · PTP in plain words")
P("PTP is a conversation between a <b>master</b> (which has the right time) and <b>clients</b> (which want it). "
  "There are four main message types:")
TBL([["Message","What it says","How often (G.8275.1)"],
     ["<b>Announce</b>","\"I am a clock, and this is how good I am\" (my quality and priority)","8 per second (one every 125 ms)"],
     ["<b>Sync</b> + <b>Follow_Up</b>","\"The time was T1 when I sent this\"","16 per second"],
     ["<b>Delay_Req</b> / <b>Delay_Resp</b>","The client asks \"how long does the cable take?\" and the master answers","16 per second"]],
    [36*mm,88*mm,44*mm])
P("The client notes when Sync arrived (T2), sends Delay_Req (T3), and learns when the master got it (T4). "
  "The trip there and back is measured, and <b>half</b> of it is taken as the one-way delay, because the standard "
  "assumes both directions take the same time. <b>That assumption is exactly what a delay attack abuses.</b>")
H2("Who becomes the master? The election (BMCA)")
P("Every clock sends Announce messages, and the clients run an election called the <b>BMCA</b> "
  "(Best Master Clock Algorithm). They compare fields such as <b>clockClass</b> (how good the time source is) "
  "and <b>priority2</b> (an operator's preference). The best one wins. A rogue device wins by <i>lying</i> in "
  "these fields.")
H2("The telecom rulebook we follow: ITU-T G.8275.1")
BUL(["<b>domain 24</b> — the network \"channel\" number (the telecom range is 24–43).",
     "<b>priority1 is fixed at 128</b> — so any other value is a red flag.",
     "<b>clockClass 0–5 is reserved</b> (IEEE 1588 Table 5) — a real clock never sends it.",
     "Messages go to one fixed Ethernet group address, <b>01:1B:19:00:00:00</b>.",
     "Every relay (a <b>boundary clock</b>) adds 1 to <b>stepsRemoved</b>, so hop count is visible.",
     "Each sender numbers its messages with a <b>sequenceId</b> that only goes up. A replay makes it go backwards."])
A(PageBreak())

# ---------- 3. HOW IT WORKS ----------
H1("4 · How it works")
H2("Phase 1 (August): a machine-learning pipeline")
P("Timing data was cut into 0.4-second windows, 28 numbers were computed per window, and a Random "
  "Forest labelled each window as fault or attack. There was also an \"UNKNOWN\" safety net, a digital twin that "
  "forecasts each fix, and a healing loop. Later checks showed that 12 of the 28 numbers only carry "
  "information in <i>simulated</i> data (GPS and oscillator fields are constant or missing in real captures). "
  "That is one reason Phase 2 was built.")
H2("Phase 2 (September): a standards-correct testbed and a frozen rule")
P("<b>The testbed.</b> Six small virtual machines (Linux network namespaces) run the real <b>linuxptp</b> "
  "software, configured to G.8275.1:")
A(Paragraph("<font face='Courier' size='8.6'>[GM-A p2=100]  [GM-B p2=110] -- bridge UP -- [Boundary Clock p2=120] -- bridge DOWN -- [RU1] [RU2] [RU3]</font>",S['cell'])); SP(6)
BUL(["<b>GM-A</b> is the main grandmaster. <b>GM-B</b> is the approved backup, which makes planned failover (B2) possible.",
     "The <b>boundary clock</b> sits between two network segments, like O-RAN setups LLS-C2/C3, so hop counts change.",
     "<b>Three radio units</b> (RU1–RU3) are the clients."])
P("<b>The rule.</b> Instead of a trained model, a fixed rule checks the evidence in this order. The first match wins:")
NUM(["Is any source sending Announce far faster than it says it will? → <b>A5 flood</b>",
     "Does any sequenceId go backwards? → <b>A3 replay</b>",
     "Is an unapproved clock relaying the real grandmaster with an extra hop? → <b>A8 rogue boundary clock</b>",
     "Is an unapproved clock announcing <i>itself</i> as grandmaster? Is clockClass below 6, or priority1 not 128? → <b>A1 rogue master</b> "
     "(stepsRemoved ≥ 255 and alternateMasterFlag are also illegal and are flagged)",
     "Is an unapproved source sending timing but never Announce? → <b>A2 Sync spoof</b>",
     "Wrong domain, wrong group address, or wrong message rate? → <b>out-of-profile attack</b>",
     "Grandmaster changed to an approved clock <b>during</b> maintenance? → <b>BENIGN (B2)</b>. "
     "Changed with <b>no</b> maintenance window? → <b>UNKNOWN</b>, because the packets can't tell a crash from an attack.",
     "Otherwise, with only approved clocks and no violations → <b>BENIGN</b>."])
BOX("<b>Why a rule and not a model?</b> Every constant in it comes from a standard (domain, priority1, clockClass, "
    "stepsRemoved, the 2× message-rate cap) or from operator configuration (the allow-list and maintenance window). "
    "There is <b>one</b> self-chosen value: a clock seen in under <b>1%</b> of Announce messages counts as a start-up "
    "blip. The standard's own rule (<b>2 Announce within 4 intervals</b>, IEEE 1588 §9.3.2.4) has been identified "
    "but not yet adopted, because changing the rule means re-freezing and re-running everything.", WARNBG, BAD)
SP(10)

# ---------- 4. DATASETS ----------
H1("5 · The data — where the numbers come from")
P("This is the question people ask most, so it's worth being exact. There are three sources, and they "
  "carry very different weight.")
H2("Source 1 — the August simulator (synthetic): not used as evidence")
P("This is software that fakes a PTP clock with perfectly labelled faults. It was useful for building and debugging. "
  "A check found that one simulator field alone gives away the source: offsetScaledLogVariance is <b>4096</b> in every "
  "simulated row and <b>65535</b> in every real row. So any mix of simulated and real data can be told apart by that one number.")
H2("Source 2 — real TIMESAFE hardware captures (the real-world evidence)")
P("These are actual PTP recordings of attacks on a real 5G testbed at Northeastern University, published with the TIMESAFE paper. "
  "Counted directly from the packets: the six attack captures hold <b>344,630</b> PTP packets, all on domain 24, "
  "with no optional add-on fields (no TLVs) at all.")
TBL([["Capture","PTP packets","Attack type"],
     ["2024-10-16-announce_attack","260,525","Forged Announce (rogue master)"],
     ["15min_announce_attack","46,998","Announce attack, fully standard-looking fields"],
     ["prod_successful_announce_attack_ptp","13,565","Announce attack"],
     ["2024-10-08-sync_attack_singlestep_1","9,078","Sync attack (one-step)"],
     ["2024-10-08-sync_attack_1","8,440","Sync attack (two-step)"],
     ["2024-10-08-announce_attack_1","6,024","Announce attack"]],
    [72*mm,30*mm,66*mm])
P("<b>What the attacker actually sends</b> (read from the raw fields of the 2024-10-16 capture): source "
  "<font face='Courier'>b8cef6ffff5e6afa</font>, one character different from <font face='Courier'>b8cef6fffe5e6afa</font>, "
  "claims to be grandmaster with <b>priority1 = 0, priority2 = 0, clockClass = 0</b>, in 24,653 Announce messages. "
  "clockClass 0 is illegal. The approved grandmaster <font face='Courier'>fcaf6afffe02babe</font> advertises 128 / 120 / 6.", 'small')
BOX("<b>A duplicate-file trap we found.</b> The folders held 21 capture files, but only <b>14 are unique</b>. Three "
    "\"separate\" sessions (announce_session_1, announce_session_2 and a UE-data capture) are byte-for-byte the "
    "same file as 15min_announce_attack. The August edition counted \"five independent sessions\", so some of its "
    "\"unseen session\" tests may have been run on data the model had already seen.", WARNBG, BAD)
H2("Source 3 — our own G.8275.1 testbed (the September evidence)")
P("<b>11 scenarios × 12 repeats = 132 runs.</b> Each repeat uses fresh random attacker identities, priorities, timings "
  "and burst sizes (<font face='Courier'>run/randparams.py</font>), so the 12 repeats are genuinely different. "
  "The August netem data could not be reused. It announced once every <b>2 s</b> instead of every <b>125 ms</b>, a "
  "16× mismatch with the real captures, so any classifier could have told the two apart by rhythm alone.")
A(PageBreak())

# ---------- 5. RESULTS ----------
H1("6 · Results")
H2("How to read the numbers")
BUL(["<b>Sensitivity</b> = of the real attacks, how many were caught.",
     "<b>Specificity</b> = of the harmless faults, how many were correctly left alone.",
     "<b>95% range</b> (Wilson interval) = where the true value probably lies, given a limited number of runs. "
     "Narrower is more certain.",
     "The rule was <b>frozen</b> (fingerprinted with SHA-256, 18 files) <b>before</b> these runs and never changed after. "
     "Earlier runs that exposed bugs are development data and are not counted."])
H2("The 132-run campaign (repeats 30–41)")
TBL([["Measure","Result","95% range","Plain meaning"],
     ["Sensitivity","<b>1.000</b> (60/60)","0.940–1.000","Every attack run was flagged"],
     ["Specificity, all benign","<b>0.800</b> (48/60)","0.682–0.882","12 harmless runs were wrongly flagged"],
     ["Specificity without the BC-swap case","1.000 (48/48)","0.926–1.000","All 12 mistakes come from one scenario"],
     ["Honest \"UNKNOWN\"","<b>1.000</b> (12/12)","0.757–1.000","Unplanned crash: never guessed"],
     ["Naming the right attack","0.817 (49/60)","0.701–0.894","Detected, but sometimes given the wrong name"]],
    [44*mm,32*mm,28*mm,64*mm])
P("Per attack, correctly named: A1 8/12 · A2 12/12 · A3 12/12 · A5 12/12 · A8 5/12. When a rogue master or rogue "
  "boundary clock appears, the radio units switch to it, and that makes their message numbers genuinely restart. "
  "The replay check (step 2) fires first, so A1 and A8 are sometimes named \"A3\". The attack is still caught.", 'small')
BOX("<b>Why specificity is 0.800, not 1.000.</b> In the <i>planned boundary-clock replacement</i> scenario, the "
    "replacement clock <b>is</b> approved: it is written into the context file as a second boundary clock. But the "
    "frozen rule reads only <b>one</b> approved boundary-clock identity, so the legitimate new one looks like a rogue one. "
    "This is a limit of the rule's input format, not a detection failure. It was <b>reported, not patched</b>: fixing it "
    "after seeing the result would turn test data into tuning data.", WARNBG, BAD)
H2("Real hardware captures — rule applied unchanged")
TBL([["Capture","Caught by the standards alone?","Verdict"],
     ["2024-10-16-announce_attack","Yes — clockClass &lt; 6 and priority1 ≠ 128 (24,653 each)","ATTACK"],
     ["2024-10-08-announce_attack_1","Yes — clockClass &lt; 6 and priority1 ≠ 128 (457 each)","ATTACK"],
     ["prod_successful_announce_attack_ptp","Yes — clockClass &lt; 6 (39)","ATTACK"],
     ["2024-10-08-sync_attack_1","Yes — sequenceId goes backwards (2,500)","ATTACK"],
     ["2024-10-08-sync_attack_singlestep_1","Yes — sequenceId goes backwards (2,455)","ATTACK"],
     ["15min_announce_attack","<b>No</b> — every field looks legal; needs the allow-list","ATTACK"]],
    [60*mm,84*mm,24*mm])
P("<b>6 of 6 flagged; 5 of 6 by the standards alone.</b> The sixth is a \"healthy-looking spoof\", exactly the case "
  "that needs operator context. <b>Rule-breaking test messages:</b> 7 of 7 caught, each by its own cited rule "
  "(illegal clockClass, alternateMasterFlag, stepsRemoved ≥ 255, wrong domain, wrong group address, priority1 ≠ 128, and one clean control).")
H2("Earlier (August) results — kept for the record, no longer used as evidence")
P("August reported 99.96% (Announce), 99.66% (Sync/Follow_Up) and 99.66% (single-step) protection on real "
  "data, false alarms cut from 4.49% to 2.37%, simulator accuracy 0.991, recovery in 0.933 s, and live decisions in 0.081 s on average "
  "(0.404 s at worst) over 5,665 windows. Those numbers are <b>not re-used</b>, for three reasons: some \"unseen\" sessions were "
  "duplicates of training files; 12 of the 28 features carry information only in simulated data; and the benign netem "
  "data announced at the wrong rate. The September campaign does <b>not</b> re-measure decision time. It judges each run as a whole.", 'small')
A(PageBreak())

# ---------- 6. THE BUGS + LIMITS ----------
H1("7 · Bugs we found — and fixed")
H2("August: the \"silent zero\" safety flaw")
P("Under heavy packet loss, the timing tool returned nothing, the software filled in a zero, and a zero looks "
  "exactly like perfect timing. So the system reported 'healthy' at the very moment it had gone blind. "
  "<b>Fix:</b> treat missing data as its own state, and never call anything healthy without proof. This is "
  "called <b>failing closed</b>. The September rule keeps this principle: missing evidence gives <b>UNKNOWN</b>, never BENIGN.")
H2("September: found while building the testbed (all fixed before the freeze)")
TBL([["What went wrong","Why it mattered","Fix"],
     ["The replay check tracked Delay_Resp by the <i>answering</i> clock","The standard echoes the <i>asking</i> client's number, so a healthy run showed 799 false \"replays\"","Track by the asking client"],
     ["The allow-list only checked grandmaster names","A spoofer sending 1,800 fake Sync messages and no Announce was invisible","Check every sender"],
     ["A8 was first built as a one-port fake master","That is just A1 again: the same attack built twice","Rebuilt as a real two-port relay"],
     ["The G.8275.1 election setting was missing","linuxptp ran the ordinary election, not the telecom one. A capture can't show this","Added dataset_comparison G.8275.x"],
     ["PATH_TRACE was switched on","Real captures never carry it, so it gave away \"testbed vs real\"","Switched off"],
     ["Software sometimes started before the virtual link","Empty captures","Wait for the link; one retry; failures discarded openly"]],
    [52*mm,74*mm,42*mm])
P("Four \"give-away\" fields (<b>provenance leaks</b>) were found in total: the 16× rhythm mismatch, the 4096/65535 "
  "simulator constant, PATH_TRACE, and the PTP minor-version number (testbed 1, real 0). The first three are gone. The last "
  "one is built into the software, so it is excluded from any mixed dataset.", 'small')
A(PageBreak())

# ---------- 7. STATUS + NEXT ----------
H1("8 · What's done, what isn't, and what's next")
TBL([["Area","Status"],
     ["G.8275.1 software testbed","<b>Built and validated</b>: 132 runs, zero infrastructure failures, rule frozen before the runs"],
     ["Real-capture check","6 of 6 flagged by the unchanged rule"],
     ["Rule-breaking message tests","7 of 7"],
     ["Test catalogue","168+ cases researched: 17 run, 106 specified but not run, 45 need hardware"],
     ["Hardware (Tier-3)","Not started — timing NIC, second machine, GPS grandmaster"]],
    [52*mm,116*mm])
BOX("<b>Is the software testbed \"complete with no compromise\"?</b> Not quite, and it is safer to say so. "
    "What is true: everything that was built follows the standard, was run properly, and reports its limits. "
    "<b>Still open in software:</b> (1) a list of approved boundary clocks, which would fix all 12 false alarms; "
    "(2) adopting the standard's foreign-master rule and the other identified checks (±30% timing, full clockClass list, "
    "VLAN/unicast); (3) better attack naming (0.817); (4) using the logged pmc management data; (5) the O-RAN tests for "
    "packet removal and malformed messages. Items 1 and 2 need a new freeze and a full re-run.", WARNBG, BAD)
H2("What software can never do here")
BUL(["All virtual machines share <b>one crystal</b>, so real clock drift (B6) can't happen. A <b>second PC</b> fixes this.",
     "There is no hardware timestamping. Measured noise: offset median <b>0.9 µs</b> (95th percentile 5.6 µs), cable-delay "
     "estimate median <b>7.2 µs</b>, against a nanosecond target. A timing NIC (for example Intel i210/i226) fixes this and makes delay attacks measurable.",
     "GPS spoofing, jamming and holdover, and SyncE, need real GPS and physical-layer hardware. A second PC alone does not unlock them."])
BOX("<b>One-sentence summary:</b> on a standards-correct software testbed and on real 5G hardware captures, a frozen, "
    "standards-based rule caught every attack and correctly refused to guess when the packets couldn't decide. It wrongly "
    "flagged one harmless scenario (a planned boundary-clock swap) for a known, named reason. Hardware testing and the "
    "open software items above are the next steps.", LIGHT, ACCENT)
A(PageBreak())

# ---------- 8. GLOSSARY ----------
H1("9 · Mini-glossary")
TBL([["Term","Meaning"],
     ["O-RAN","Open, multi-vendor way of building 5G base stations."],
     ["Fronthaul","The link between the radio unit and the baseband unit."],
     ["S-plane","The fronthaul traffic that carries the clock. Our topic."],
     ["PTP (IEEE 1588)","The protocol that shares time across the network."],
     ["G.8275.1","The ITU-T telecom rulebook for PTP: domain 24–43, 8 Announce/s, 16 Sync/s, priority1 = 128."],
     ["Grandmaster (GM)","The top clock everyone follows."],
     ["Boundary clock (BC)","A relay clock between network segments. It adds 1 to stepsRemoved."],
     ["Announce / Sync","\"I am a clock, this good\" / \"the time was T1\"."],
     ["BMCA","The 'best clock wins' election that attackers exploit by lying."],
     ["clockClass / priority1 / priority2","Fields used in the election. clockClass 0–5 is illegal; G.8275.1 fixes priority1 at 128."],
     ["sequenceId","A message counter that only goes up. Going backwards suggests a replay."],
     ["Allow-list","The operator's list of approved clocks."],
     ["Maintenance window","A declared period when planned changes are expected."],
     ["GNSS / GPS, SyncE","Satellite time source / physical-layer frequency sharing. Both need hardware."],
     ["Holdover","Running on an internal backup clock after losing the reference. Benign."],
     ["Sensitivity / specificity","Share of attacks caught / share of harmless events correctly left alone."],
     ["Wilson 95% range","The likely range of the true value, given the number of runs."],
     ["Freeze (pre-registration)","Fingerprinting the rule before testing, so it can't be tuned to the answers."],
     ["Provenance leak","A field that reveals <i>where</i> data came from rather than what happened."],
     ["Fail-closed / UNKNOWN","Refusing to say 'healthy' (or guess) when the evidence isn't there."],
     ["TIMESAFE","The 2025 ACM study whose real hardware attack captures we test against."],
     ["Digital twin","A fast model that predicts what a fix will do before it is applied (August phase)."]],
    [46*mm,122*mm])

OUT=os.environ.get("PRES_OUT","ORAN_Project_Walkthrough.pdf")
doc=SimpleDocTemplate(OUT,pagesize=A4,topMargin=18*mm,bottomMargin=20*mm,leftMargin=21*mm,rightMargin=21*mm,
    title="Self-Healing 5G Timing Security — Project Walkthrough",author="Project team")
doc.build(story,onFirstPage=_page,onLaterPages=_page)
print("WROTE",OUT)
