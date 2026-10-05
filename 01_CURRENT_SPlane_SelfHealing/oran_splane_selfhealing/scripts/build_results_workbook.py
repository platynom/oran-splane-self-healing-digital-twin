import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY="14304F"; ACCENT="2C6FBB"; LIGHT="EEF3F9"; GOODBG="EAF5EE"; WARNBG="FDF0E6"
HDR = Font(name="Arial", bold=True, color="FFFFFF", size=11)
H2  = Font(name="Arial", bold=True, color=NAVY, size=13)
BOLD= Font(name="Arial", bold=True, size=10)
BODY= Font(name="Arial", size=10)
SMALL=Font(name="Arial", size=9, color="555555")
navyfill=PatternFill("solid", fgColor=NAVY)
accfill =PatternFill("solid", fgColor=ACCENT)
litfill =PatternFill("solid", fgColor=LIGHT)
goodfill=PatternFill("solid", fgColor=GOODBG)
warnfill=PatternFill("solid", fgColor=WARNBG)
thin=Side(style="thin", color="C9D4E2")
border=Border(left=thin,right=thin,top=thin,bottom=thin)
wrap=Alignment(wrap_text=True, vertical="top")
top =Alignment(vertical="top")
ctr =Alignment(horizontal="center", vertical="center")

wb=openpyxl.Workbook()

def sheet(title):
    ws=wb.create_sheet(title)
    return ws

def head_row(ws, r, cols, widths, fill=navyfill):
    for i,(c,w) in enumerate(zip(cols,widths),1):
        cell=ws.cell(r,i,c); cell.font=HDR; cell.fill=fill; cell.border=border
        cell.alignment=Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width=w

def data_row(ws, r, vals, zebra=False, fills=None):
    for i,v in enumerate(vals,1):
        cell=ws.cell(r,i,v); cell.font=BODY; cell.border=border; cell.alignment=wrap
        if fills and fills.get(i): cell.fill=fills[i]
        elif zebra: cell.fill=litfill

def title_block(ws, title, sub):
    ws.cell(1,1,title).font=H2
    ws.cell(2,1,sub).font=SMALL

# ---------------- 0. Overview ----------------
ws=wb.active; ws.title="0_Overview"
ws.column_dimensions["A"].width=34; ws.column_dimensions["B"].width=88
ws.cell(1,1,"AI-Native Self-Healing O-RAN Network using a Digital Twin").font=Font(name="Arial",bold=True,size=15,color=NAVY)
ws.cell(2,1,"Open Fronthaul S-Plane timing security — project results workbook").font=SMALL
rows=[
 ("What the project does","Watches the timing signals of a 5G base station, decides whether a problem is a harmless fault or a deliberate attack, checks a fix in a 'digital twin', and applies it inside the 2-second safety deadline."),
 ("The field","5G / O-RAN network security -> Open Fronthaul -> the Synchronisation plane (the clock traffic)."),
 ("Why timing matters","5G radios must agree on time to ~100 nanoseconds. If timing breaks, service fails in ~2 seconds."),
 ("Core hard problem","A benign fault (lost GPS, congestion) and a real attack look almost identical. We tell them apart (H0 vs H1)."),
 ("Two data sources","(1) a simulator we wrote = synthetic; (2) real public captures from the TIMESAFE 5G testbed = real evidence."),
 ("Status","Software: complete, 56 tests passing, commit 4e4bd16, restore tag known-good-2026-08-07. Hardware (Tier-3): not started."),
 ("Headline real-data result","~99.6-99.96% protection on real TIMESAFE attacks; benign false alarms cut from 4.49% to 2.37%."),
 ("Known hard limit","A perfectly healthy-looking GNSS spoof cannot be caught from a single time reference (0%). This is a known theoretical limit, not a bug."),
 ("Next step","An 'evasion attack' add-on (software-only) to raise research novelty. Being built separately."),
 ("How to read this book","Each tab is one topic. Grey note under a title explains it. Simulator numbers are the sandbox; real/live numbers are the evidence."),
]
r=4
for k,v in rows:
    a=ws.cell(r,1,k); a.font=BOLD; a.alignment=wrap; a.fill=litfill; a.border=border
    b=ws.cell(r,2,v); b.font=BODY; b.alignment=wrap; b.border=border
    r+=1
for rr in range(4,r): ws.row_dimensions[rr].height=30

# ---------------- 1. File index ----------------
ws=sheet("1_File_Index")
title_block(ws,"Every code file, in plain terms","Line counts are exact (measured on disk). Grouped by pipeline stage.")
head_row(ws,4,["File","Lines","What it does (simple)"],[40,8,92])
files=[
 ("PIPELINE — turning signals into a decision","",""),
 ("fronthaul_sim/simulator.py","124","The simulator. Fakes a realistic PTP clock (offset, delay, drift, holdover) so we can generate data."),
 ("faults/injectors.py","261","Stamps in labelled events: benign faults (GPS loss, congestion) and attacks (spoof, replay, DoS, GNSS jam)."),
 ("dataset/build.py","40","Builds the labelled table of time-windows from the simulator."),
 ("telemetry/features.py","228","Cuts the stream into 0.4s windows and computes the 28 features per window (timing, protocol, BMCA, etc.)."),
 ("discriminator/model.py","72","The Random Forest that labels a window benign-fault (H0) or attack (H1)."),
 ("discriminator/openset.py","197","Safety net: flags anything unlike training data as UNKNOWN; the 2-of-3 voting rule."),
 ("twin/model.py","86","The digital twin. Forecasts what each fix would do, and scores its own confidence (fidelity)."),
 ("healing/loop.py","200","The decision loop. Picks and commits a fix in <1s. Holds the fail-closed safety gate."),
 ("benchmark/run.py","82","Compares the smart loop against naive baselines."),
 ("config/default.yaml","76","All the settings: 100ns budget, 2s window, features on/off, voting, action list."),
 ("INGEST — reading real data","",""),
 ("ingest/schema.py","179","The common data format every source must produce. Holds the 'was this really observed?' flags."),
 ("ingest/ptp_wire.py","189","Reads/writes real PTP-over-Ethernet packets to the nanosecond."),
 ("ingest/pcap_ingest.py","160","Turns a real packet-capture (.pcap) file into telemetry."),
 ("ingest/linuxptp_ingest.py","77","Reads the output of the real Linux PTP program (ptp4l)."),
 ("ingest/sync_status.py","95","Reads SyncE quality and GNSS status from management tools."),
 ("EVALUATION — proving it works honestly","",""),
 ("stats/multiseed.py","158","Runs 8 random seeds to get confidence intervals, not one lucky number."),
 ("stats/openset_eval.py","442","Tests the UNKNOWN detector per attack family; tunes thresholds."),
 ("stats/gnss_eval.py","324","GNSS spoof/jam experiments and the fundamental-limit test."),
 ("stats/multisource_eval.py","276","The cross-source experiment (a negative result)."),
 ("stats/persistence_eval.py","110","Tunes the 2-of-3 voting trade-off."),
 ("stats/twin_validation.py","71","Checks the twin's forecasts match the simulator physics."),
 ("scripts/calibrate_real.py","384","Leakage-proof evaluation on real captures (keeps sessions separate)."),
 ("LIVE + HARNESS — real Linux PTP","",""),
 ("scripts/live_collect.py","338","Live collector; reads a running ptp4l, never fakes missing data."),
 ("scripts/live_loop.py","194","Live demo loop; recommends actions only."),
 ("scripts/analyze_live_validation.py","195","Analyses live runs: latency, coverage, metrics."),
 ("harness/netem_harness.sh","109","Sets up two real ptp4l clocks over a virtual link with injected impairments."),
 ("harness/run_netem_scenarios.py","90","Runs all 4 live scenarios with isolation."),
 ("harness/planned_gm_failover.sh","89","Legitimate two-master failover (a benign confounder)."),
 ("ENTRY POINTS + GOVERNANCE","",""),
 ("scripts/run_all.py","88","One command -> full Tier-1 pipeline + SUMMARY.md."),
 ("scripts/run_tier2.py","198","One command -> Tier-2 suite (CIs, generalisation, real ingest) + report."),
 ("scripts/audit_state.py","198","Mechanical truth-check of the repo (catches agents overstating completion)."),
 ("scripts/make_synthetic_pcap.py","85","Makes a known-answer PTP capture to test the parser."),
 ("scripts/prepare_timesafe_sessions.py","77","Prepares the real TIMESAFE captures into clean sessions."),
 ("scripts/build_technical_report.py","1200","Generates the 30-page technical report PDF."),
 ("TESTS — 56 total across 15 files","",""),
 ("tests/test_missing_data_safety.py","231","The fail-closed safety tests (incl. real pmc captures)."),
 ("tests/test_ingest_tier2.py","179","pcap round-trip, linuxptp parsing, holdover."),
 ("tests/test_openset.py","128","Novelty detection + voting."),
 ("tests/test_gnss_timesource.py","119","GNSS scenarios + time-source features."),
 ("tests/test_live_validation.py","122","The live path."),
 ("tests/(10 more test files)","~400","DoS, BMCA, multisource, stats, dataset, healing, simulator, persistence, calibrate."),
]
r=5
for name,lines,desc in files:
    if lines=="" and desc=="":
        c=ws.cell(r,1,name); c.font=Font(name="Arial",bold=True,color="FFFFFF",size=10); c.fill=accfill; c.border=border
        ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=3)
        for cc in range(2,4): ws.cell(r,cc).fill=accfill; ws.cell(r,cc).border=border
    else:
        data_row(ws,r,[name,lines,desc], zebra=(r%2==0))
        ws.cell(r,2).alignment=ctr
    r+=1

# ---------------- 2. Datasets ----------------
ws=sheet("2_Datasets")
title_block(ws,"The two datasets (this is the question people ask most)","Simulator = our sandbox (synthetic). TIMESAFE captures = the real evidence.")
head_row(ws,4,["Dataset / file","Type","Rows","What it is"],[40,14,10,74])
ds=[
 ("Our simulator (fronthaul_sim)","SYNTHETIC","generated","Physics-based fake PTP clock. We control the labels perfectly. Source of the big simulator %."),
 ("--- Real TIMESAFE public captures (data/external/timesafe_sessions/) ---","","",""),
 ("announce_session_1__announce.csv","REAL attack","46,987","Real Announce/BMCA attack traffic, session 1."),
 ("announce_session_1__benign.csv","REAL benign","11","Benign baseline, session 1."),
 ("announce_session_2__announce.csv","REAL attack","46,992","Real Announce attack, session 2."),
 ("announce_session_2__benign.csv","REAL benign","6","Benign baseline, session 2."),
 ("announce_session_3__announce.csv","REAL attack","4,538","Real Announce attack, session 3."),
 ("announce_session_3__benign.csv","REAL benign","1,485","Benign baseline, session 3."),
 ("sync_followup_session__benign.csv","REAL benign","1,016","Benign baseline for the Sync/Follow-Up session."),
 ("sync_followup_session__sync_follow_up.csv","REAL attack","7,424","Real Sync/Follow-Up attack traffic."),
 ("sync_singlestep_session__benign.csv","REAL benign","1,707","Benign baseline for the single-step session."),
 ("sync_singlestep_session__sync_single_step.csv","REAL attack","7,370","Real single-step Sync attack traffic."),
 ("Raw .pcap files (data/external/s-plane_security_repo/)","REAL packets","several","Original packet captures the CSVs are derived from."),
 ("Live netem captures (results/tier2/)","REAL-live","5,665 windows","Our own runs of REAL ptp4l over a virtual link with impairments."),
]
r=5
for name,typ,rows,desc in ds:
    if typ=="" and rows=="":
        c=ws.cell(r,1,name); c.font=Font(name="Arial",bold=True,color="FFFFFF",size=10); c.fill=accfill; c.border=border
        ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=4)
        for cc in range(2,5): ws.cell(r,cc).fill=accfill; ws.cell(r,cc).border=border
    else:
        f={}
        if "REAL" in typ: f[2]=goodfill
        if typ=="SYNTHETIC": f[2]=warnfill
        data_row(ws,r,[name,typ,rows,desc], zebra=(r%2==0), fills=f)
        ws.cell(r,2).alignment=ctr; ws.cell(r,3).alignment=ctr
    r+=1
ws.cell(r+1,1,"Honest limitation: only 5 independent real sessions, and no benign 'planned grandmaster change' capture.").font=SMALL

# ---------------- 3. Results core ----------------
ws=sheet("3_Results_Core")
title_block(ws,"Core results — the discriminator and the healing loop","From the simulator, averaged over 8 random seeds. These prove the method is sound, not field performance.")
head_row(ws,4,["Metric","Value","Plain meaning"],[42,20,66])
core=[
 ("Discriminator accuracy","0.991 +/- 0.002","How often benign-vs-attack is called correctly."),
 ("Macro F1","0.991 +/- 0.002","Balanced across both classes (not fooled by imbalance)."),
 ("ROC-AUC (H1)","1.000 +/- 0.000","Near-perfect separability in the simulator's feature space."),
 ("Recovery success","1.000 +/- 0.000","The loop restored timing in every benchmark scenario."),
 ("Wrong-action rate","0.000 +/- 0.000","Never applied the opposite of the correct fix."),
 ("Mean time to recovery","0.933 +/- 0.008 s","Well inside the 2-second failure window."),
]
r=5
for k,v,m in core:
    data_row(ws,r,[k,v,m], zebra=(r%2==0)); ws.cell(r,2).alignment=ctr; ws.cell(r,2).font=BOLD
    r+=1
r+=1
ws.cell(r,1,"Baseline comparison (benchmark_results.csv)").font=H2; r+=1
head_row(ws,r,["Method","Recovery","Wrong-action","MTTR (s)","Peak error (ns)","Within 2s"],[26,12,14,12,16,12]); r+=1
bench=[
 ("Governed loop (ours)","1.00","0.00","0.935","43.5","100%"),
 ("Always failover","0.50","0.00","0.635","91.5","100%"),
 ("Always holdover","0.50","0.50","1.175","91.5","100%"),
 ("Detection only (no fix)","0.00","0.00","2.000","98.9","0%"),
]
for i,row in enumerate(bench):
    f={1:goodfill} if i==0 else {}
    data_row(ws,r,list(row), zebra=(i%2==1), fills=f)
    for cc in range(2,7): ws.cell(r,cc).alignment=ctr
    r+=1

# ---------------- 4. Generalization ----------------
ws=sheet("4_Generalization")
title_block(ws,"Can it catch an attack family it never saw? (leave-one-out)","Remove one whole attack type from training, then test on it. This is the honest, hard test.")
head_row(ws,4,["Held-out family (never trained on)","Recall on unseen family","Reading"],[36,22,60])
gen=[
 ("Spoof","1.000","Caught perfectly even when unseen."),
 ("Replay","0.592","Partially caught."),
 ("DoS / message flood","0.000","Missed by the plain classifier -> this is WHY the open-set + BMCA layers exist."),
 ("GNSS spoof","0.000","The fundamental limit: a healthy-looking spoof is invisible from one reference."),
 ("GNSS jam","0.000","Plain classifier misses it; oscillator-consistency features recover it elsewhere."),
]
r=5
for fam,rec,rd in gen:
    f={2:goodfill} if rec=="1.000" else ({2:warnfill} if rec=="0.000" else {})
    data_row(ws,r,[fam,rec,rd], zebra=(r%2==0), fills=f); ws.cell(r,2).alignment=ctr; ws.cell(r,2).font=BOLD
    r+=1
r+=1
ws.cell(r,1,"Note: these plain-classifier gaps are exactly what the open-set novelty layer + BMCA features + oscillator consistency were added to fix. See the Real-data tab for the recovered numbers.").font=SMALL
ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=3); ws.row_dimensions[r].height=44

# ---------------- 5. Real + live ----------------
ws=sheet("5_Real_and_Live")
title_block(ws,"Results on REAL data and LIVE runs","This is the evidence that counts. Real TIMESAFE captures + our own real ptp4l runs.")
head_row(ws,4,["Test","Result","Reading"],[42,18,68])
real=[
 ("REAL TIMESAFE — Announce/BMCA attack","99.96%","Protection on real Announce attack traffic."),
 ("REAL TIMESAFE — Sync/Follow-Up attack","99.66%","Protection on real Sync/Follow-Up attack."),
 ("REAL TIMESAFE — Single-step Sync attack","99.66%","Protection on real single-step attack."),
 ("Benign false alarms (1-of-1)","4.49%","Before the voting rule."),
 ("Benign false alarms (2-of-3 voting)","2.37%","After voting, with no loss against the 2s deadline."),
 ("Unseen healthy-looking GNSS spoof","0.00%","The known hard limit. Needs authenticated GNSS hardware to solve."),
 ("--- LIVE runs with real ptp4l over netem ---","",""),
 ("Total real-trace windows captured","5,665","baseline 2,669 / pdv 2,589 / loss 392 / holdover 15."),
 ("Live decision latency (mean / max)","0.081 s / 0.404 s","Two orders of magnitude inside the 2s budget."),
 ("Fail-closed test: windows after master killed","47 UNKNOWN + 1 pending","Zero wrongly called 'healthy' during a total blackout."),
 ("Digital twin vs simulator agreement","Pearson 0.998","Twin forecasts track real physics."),
 ("pcap parser accuracy","14.68 ns error","Offset recovery error vs known ground truth."),
]
r=5
for t,res,rd in real:
    if res=="" and "---" in t:
        c=ws.cell(r,1,t.replace("---","").strip()); c.font=Font(name="Arial",bold=True,color="FFFFFF",size=10); c.fill=accfill; c.border=border
        ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=3)
        for cc in range(2,4): ws.cell(r,cc).fill=accfill; ws.cell(r,cc).border=border
    else:
        f={2:goodfill} if "%" in res and res not in ("4.49%","0.00%") else ({2:warnfill} if res in ("0.00%","4.49%") else {})
        data_row(ws,r,[t,res,rd], zebra=(r%2==0), fills=f); ws.cell(r,2).alignment=ctr; ws.cell(r,2).font=BOLD
    r+=1

# ---------------- 6. Reproduce ----------------
ws=sheet("6_Reproduce")
title_block(ws,"How to reproduce every number","Run these on the project. No hardware needed for the first two.")
head_row(ws,4,["Step","Command","Produces"],[26,52,50])
rep=[
 ("1. Setup","python -m venv .venv  &&  pip install -r requirements.txt","The environment."),
 ("2. Tier-1 pipeline","python scripts/run_all.py","results/SUMMARY.md (core numbers, ~1 min)."),
 ("3. Tier-2 suite","python scripts/run_tier2.py","results/tier2/TIER2_REPORT.md (CIs, generalisation, real ingest, ~3 min)."),
 ("4. All tests","python -m pytest tests -q","56 tests pass (~5 min)."),
 ("5. Live (Linux+root)","sudo python3 -m harness.run_netem_scenarios --scenarios baseline pdv loss holdover --duration 90","results/tier2/netem/ real-trace windows."),
 ("6. Verify repo truth","python scripts/audit_state.py","Pass/fail truth-check of the whole repo."),
 ("7. Restore if broken","git reset --hard known-good-2026-08-07","Rolls back to the verified-good commit."),
]
r=5
for s,c,p in rep:
    data_row(ws,r,[s,c,p], zebra=(r%2==0)); ws.cell(r,2).font=Font(name="Consolas",size=9)
    r+=1
ws.cell(r+1,1,"Result CSVs already on disk under results/ and results/tier2/ — every number in this book traces to one of them.").font=SMALL

# freeze headers + save
for name in wb.sheetnames:
    w=wb[name]
    w.sheet_view.showGridLines=False
    if name!="0_Overview": w.freeze_panes="A5"

out="/sessions/festive-nice-curie/mnt/outputs/ORAN_Project_Results.xlsx"
wb.save(out); print("saved", out)
