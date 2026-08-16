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
SP(60)
A(Paragraph("Self-Healing 5G Timing Security",S['title']))
A(Paragraph("A plain-English walkthrough of the whole project — every part, the data, and the results",S['sub']))
SP(14); A(HRFlowable(width="62%",thickness=1.1,color=ACCENT,hAlign='CENTER')); SP(14)
A(Paragraph("Project: AI-Native Self-Healing O-RAN Network using a Digital Twin",S['sub']))
A(Paragraph("Prepared for the team — no telecom background needed",S['sub']))
SP(24)
TBL([["Item","Status"],
     ["Software","Complete — 56 automated tests passing"],
     ["Version","Commit 4e4bd16 · restore point known-good-2026-08-07"],
     ["Real-data result","~99.6–99.96% protection on real attacks; 2.37% false alarms"],
     ["Hardware (Tier-3)","Not started — the next phase"],
     ["Note","Most build work was AI-generated under human direction"]],
    [52*mm,116*mm])
A(PageBreak())

# ---------- 1. THE STORY ----------
H1("1 · The project in 30 seconds")
P("A 5G base station is split into pieces that talk over a link called the <b>fronthaul</b>. Those "
  "pieces must agree on <b>time</b> to about <b>100 nanoseconds</b> (a ten-millionth of a second). "
  "If the timing breaks, phone service fails in roughly <b>2 seconds</b>.")
P("The clock is shared using a protocol called <b>PTP</b>, which has no built-in security. So a "
  "faulty or malicious clock can knock a base station offline. The hard part: a harmless fault (lost "
  "GPS, network congestion) and a deliberate attack look <b>almost identical</b>.")
BOX("<b>What we built:</b> software that watches the timing, decides whether a problem is a "
    "<b>harmless fault</b> or a <b>real attack</b>, tests a fix in a fast simulation (a 'digital "
    "twin'), and applies it — all inside the 2-second deadline. And if it can't trust its own data, "
    "it refuses to say 'healthy'.")
H2("Where this sits in the bigger picture")
BUL(["<b>Field:</b> 5G / O-RAN network security.",
     "<b>Zoom in:</b> the Open Fronthaul link between the radio and the baseband.",
     "<b>Zoom in again:</b> the <b>S-plane</b> — the traffic that carries the clock. That is our topic."])
A(PageBreak())

# ---------- 2. THE CORE PROBLEM ----------
H1("2 · The core problem: fault vs attack")
P("When timing drifts, the symptom is the same whatever the cause. The correct response, though, is "
  "<b>opposite</b> — so telling them apart is the whole game.")
TBL([["Harmless fault (H0)","Malicious attack (H1)"],
     ["GPS signal lost — clock rides its internal backup","GPS spoofed — clock believes a fake time"],
     ["Network congestion adds delay/jitter","Attacker injects one-sided delay on purpose"],
     ["A link fails and quality drops","Attacker forges 'I am the best clock' messages"],
     ["A planned, legitimate switch-over","A rogue device impersonating the master"]],
    [84*mm,84*mm])
P("For a fault, the right move is usually to <b>wait / ride it out</b> — the real clock returns. For "
  "an attack, the right move is to <b>isolate the bad source and switch away</b>. Do the wrong one and "
  "you make the outage worse.")
BOX("<b>The project's central claim:</b> a system that only shouts 'something is wrong' leaves the "
    "operator with a coin-flip under a 2-second deadline. Telling H0 from H1 is what makes an "
    "automatic response safe enough to attempt at all.", LIGHT, ACCENT)
A(PageBreak())

# ---------- 3. HOW IT WORKS ----------
H1("3 · How it works — the pipeline")
P("Data flows through six stages. Each is a small, testable piece of software.")
NUM(["<b>Ingest</b> — read the timing data (from our simulator, a real capture file, or a live PTP program) into one common format.",
     "<b>Features</b> — cut the stream into 0.4-second windows and compute <b>28 numbers</b> per window (timing, message patterns, clock-election behaviour, oscillator health).",
     "<b>Discriminator</b> — a Random Forest labels each window: benign fault (H0) or attack (H1).",
     "<b>Open-set safety net</b> — anything unlike anything seen before is flagged <b>UNKNOWN</b> (so a brand-new attack isn't forced into a wrong box). A 2-of-3 vote ignores single noisy windows.",
     "<b>Digital twin</b> — before acting, forecast what each candidate fix would do, and rate its own confidence.",
     "<b>Healing loop</b> — pick and commit the safest fix within 1 second. If the data can't be trusted, refuse and fall back to a safe default."])
BOX("<b>The 28 features, in plain groups:</b> timing (offset, delay, jitter) · message regularity · "
    "message rate · clock-election (BMCA) behaviour · time-source (GPS/SyncE) status · oscillator "
    "consistency. Grouping them is what lets the system catch attacks it was never explicitly taught.",
    LIGHT, ACCENT)
A(PageBreak())

# ---------- 4. DATASETS ----------
H1("4 · The data — where the numbers come from")
P("This is the question people ask most, so it's worth being exact. There are <b>two</b> sources, "
  "and they carry very different weight.")
H2("Source 1 — our simulator (synthetic)")
P("Physics-based software that fakes a realistic PTP clock and lets us stamp in perfectly-labelled "
  "faults and attacks. It's our <b>sandbox</b> — great for building and debugging. Most of the "
  "big-looking simulator percentages come from here, so they're the <b>weakest</b> evidence.")
H2("Source 2 — real TIMESAFE captures (the real evidence)")
P("Actual PTP recordings from a real 5G testbed at Northeastern University, published with their "
  "research. Five independent sessions of Announce and Sync attacks, each with a benign baseline. "
  "<b>When we claim ~99% on real attacks, it's on these.</b>")
TBL([["Real session","Type","Rows"],
     ["announce_session_1 / 2 / 3","Real Announce attacks + benign","~4.5k–47k each"],
     ["sync_followup_session","Real Sync/Follow-Up attack + benign","~8.4k"],
     ["sync_singlestep_session","Real single-step attack + benign","~9k"],
     ["Live netem runs (ours)","Real ptp4l over a virtual link","5,665 windows"]],
    [58*mm,74*mm,36*mm])
P("<b>Honest limit:</b> only five independent real sessions, and no recording of a benign "
  "<i>planned</i> master change — the one confounder we'd most like to have.", 'small')
A(PageBreak())

# ---------- 5. RESULTS ----------
H1("5 · Results")
H2("On the simulator (sandbox — 8 random seeds)")
TBL([["Metric","Value","Meaning"],
     ["Accuracy","0.991 ± 0.002","Benign-vs-attack called correctly"],
     ["Recovery success","1.000","The loop fixed every scenario"],
     ["Wrong-action rate","0.000","Never applied the opposite fix"],
     ["Time to recovery","0.933 s","Inside the 2-second deadline"]],
    [46*mm,34*mm,88*mm])
H2("On REAL data (the evidence that counts)")
TBL([["Test","Result","Reading"],
     ["Real Announce/BMCA attack","99.96%","protection"],
     ["Real Sync/Follow-Up attack","99.66%","protection"],
     ["Real single-step attack","99.66%","protection"],
     ["Benign false alarms","4.49% → 2.37%","cut by the 2-of-3 vote"],
     ["Unseen healthy-looking GNSS spoof","0.00%","the known hard limit"]],
    [58*mm,34*mm,76*mm], hi=[1,2,3])
H2("Live (real ptp4l running)")
BUL(["<b>5,665</b> real-trace windows captured across four impairment scenarios.",
     "Decision latency: mean <b>0.081 s</b>, worst <b>0.404 s</b> — far inside 2 s.",
     "After the master clock was killed: <b>0</b> windows wrongly called 'healthy'."])
A(PageBreak())

# ---------- 6. THE BUG + LIMITS ----------
H1("6 · The one real bug we found — and fixed")
P("Live testing exposed a genuine safety flaw. Under heavy packet loss, the timing tool returned "
  "nothing, our software substituted a <b>zero</b>, and a zero looks exactly like <b>perfect</b> "
  "synchronisation. So the system reported 'healthy' at the very moment it had gone blind — and an "
  "attacker could trigger this on purpose by flooding the link.")
BOX("<b>The fix:</b> treat missing data as its own state, never as a number. The software now tracks "
    "whether each measurement was really observed, and refuses to call anything 'healthy' unless it "
    "can prove it saw the data. This is called <b>failing closed</b>. Ten tests, written before the "
    "fix, lock it in.")
P("We then proved it on <b>real</b> PTP software: when we killed the master clock, the tool kept "
  "confidently reporting its <b>last known numbers</b> forever — worse than a zero. Our software reads "
  "the connection state instead of trusting the numbers, so it caught both versions.")
H2("Honest limitations")
BUL(["No real hardware yet (no PTP timing card, GPS receiver, or radio unit tested).",
     "Only five independent real attack sessions.",
     "A perfectly healthy-looking GPS spoof can't be caught from a single clock — a known theoretical limit, not a coding bug.",
     "These are research measurements, not telecom certification."])
A(PageBreak())

# ---------- 7. STATUS + NEXT ----------
H1("7 · What's done, and what's next")
TBL([["Area","Status"],
     ["Software build","Complete. 56 tests passing, one command reproduces everything."],
     ["Software validation","Complete on real recorded data and live real ptp4l."],
     ["The safety bug","Found, fixed, hardened, and verified on real software."],
     ["Hardware (Tier-3)","Not started — real timing card, GPS grandmaster, authenticated GPS."],
     ["Research novelty add-on","Designed: an 'evasion attack' (software-only) to strengthen the paper."]],
    [46*mm,122*mm])
H2("The next step in one line")
P("Build an <b>evasion attack</b>: instead of only defending, act as the attacker and design a timing "
  "attack that slips past the detector while still breaking the clock. It needs no hardware, reuses "
  "what we already built, and turns the story into 'new attack → our defence stops it' — which is what "
  "strong publications want. This is being built separately.")
SP(6); A(HRFlowable(width="100%",thickness=1,color=NAVY)); SP(8)
BOX("<b>One-sentence summary for the slide:</b> we built and validated, on real 5G timing data, a "
    "system that tells timing faults from attacks and heals inside the 2-second deadline — failing "
    "safely when it can't trust its data — with the hardware validation and an evasion-attack study "
    "as the clear next steps.", LIGHT, ACCENT)

# ---------- 8. GLOSSARY ----------
A(PageBreak())
H1("8 · Mini-glossary")
gl=[("O-RAN","Open, multi-vendor way of building 5G base stations."),
    ("Fronthaul","The link between the radio unit and the baseband unit."),
    ("S-plane","The fronthaul traffic that carries the clock. Our topic."),
    ("PTP (IEEE 1588)","The protocol that shares time across the network. No built-in security."),
    ("GNSS / GPS","Satellite time source. Can be jammed or spoofed."),
    ("Holdover","Running on an internal backup clock after losing the reference. Benign."),
    ("BMCA","The 'best clock wins' election attackers exploit by forging attributes."),
    ("H0 / H1","Our labels: H0 = benign fault, H1 = malicious attack."),
    ("Digital twin","A fast model that predicts what a fix will do before we apply it."),
    ("Fail-closed","Refusing to certify 'healthy' when the data can't be trusted."),
    ("Open-set / UNKNOWN","Being able to answer 'none of the above' for a brand-new attack."),
    ("Evasion attack","An attack shaped to slip past the detector — the planned next study.")]
TBL([["Term","Meaning"]]+[[a,b] for a,b in gl],[42*mm,126*mm])

OUT=os.environ.get("PRES_OUT","/sessions/festive-nice-curie/mnt/outputs/ORAN_Project_Walkthrough.pdf")
doc=SimpleDocTemplate(OUT,pagesize=A4,topMargin=18*mm,bottomMargin=20*mm,leftMargin=21*mm,rightMargin=21*mm,
                      title="O-RAN S-Plane Self-Healing — Project Walkthrough")
doc.build(story,onFirstPage=_page,onLaterPages=_page)
print("WROTE",OUT)
