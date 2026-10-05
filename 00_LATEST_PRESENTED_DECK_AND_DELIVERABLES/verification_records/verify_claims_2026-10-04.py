# Independent re-verification of every documented figure (run 2026-10-04).
# Usage on the project machine (Linux shell with the project folder mounted): extract splane_campaign_CORRECTED_2026-09-20.tgz to ~/verify/camp and results_2026-09-17/g87251_testbed_v2.tgz to ~/verify/tb, write the archive sha256 to ~/verify/archive.sha and entry count to ~/verify/archive.entries, then run this file.
import json,os,re,glob,csv,collections,statistics as st,hashlib
R=[]
def chk(cid,claim,ok,detail): R.append((cid,'PASS' if ok else 'FAIL',claim,detail))
V=os.path.expanduser('~/verify'); C=V+'/camp'; PR=glob.glob(os.path.expanduser('~/mnt/AI*'))[0]
OS=PR+'/01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing'
LOGS=OS+'/ml_comparison_input/extracted_168run_ptp4l_logs'
# --- archive
sha=open(V+'/archive.sha').read().strip(); n=int(open(V+'/archive.entries').read())
chk('A1','archive sha256 6149b4fb…',sha.startswith('6149b4fb15940cdac694'),sha[:16])
chk('A2','archive has 1,096 entries',n==1096,n)
runs=sorted(os.listdir(C+'/cap')); chk('A3','168 run directories',len(runs)==168,len(runs))
# packet records
tot=0
for r in runs:
    for f in glob.glob(f'{C}/cap/{r}/*.deep.csv'):
        tot+=sum(1 for _ in open(f))-1
chk('A4','1,451,909 packet records in deep extracts',tot==1451909,tot)
pcaps=[f for f in glob.glob(C+'/**/*.pcap*',recursive=True)]; chk('A5','no raw PCAPs in archive',len(pcaps)==0,len(pcaps))
cfgs=glob.glob(C+'/**/*.cfg',recursive=True); chk('A6','no runtime .cfg in archive',len(cfgs)==0,len(cfgs))
# --- verdicts
def vd(r,f):
    p=f'{C}/cap/{r}/{f}'; return json.load(open(p)) if os.path.exists(p) else None
diff=sum(1 for r in runs if vd(r,'decision_v2.json')['verdict']!=vd(r,'decision_v3.json')['verdict'])
chk('B1','v2 and v3 verdicts identical on all 168 runs',diff==0,f'{diff} differ')
f2=json.load(open(C+'/FROZEN_V2.json'))['frozen_at']; log=open(C+'/results/campaign_v3.log').readline()
chk('B2','v2 frozen 2026-09-20T11:41:31Z',f2.startswith('2026-09-20T11:41:31'),f2)
chk('B3','campaign starts 11:43:15',log.startswith('[11:43:15]'),log.strip()[:40])
ev=json.load(open(C+'/results/EVALUATION_V4.json'))
chk('B4','macro sensitivity base 0.625 / v2 0.9896 / v3 0.9896',(ev['frozen']['macro_sensitivity'],ev['v2']['macro_sensitivity'],ev['v3']['macro_sensitivity'])==(0.625,0.9896,0.9896),(ev['frozen']['macro_sensitivity'],ev['v2']['macro_sensitivity'],ev['v3']['macro_sensitivity']))
chk('B5','macro specificity 0.7833 (all rules)',ev['v3']['macro_specificity']==0.7833==ev['frozen']['macro_specificity'],ev['v3']['macro_specificity'])
# per-scenario recompute
exp={'attack':'ATTACK','benign':'BENIGN','healthy':'BENIGN'}
sc=collections.defaultdict(lambda:[0,0])
for r in runs:
    d=vd(r,'decision_v3.json'); s=r.split('__r')[0]
    want='UNKNOWN' if s=='B_unplanned_failover' else exp[d['truth_class']]
    sc[s][0]+=d['verdict']==want; sc[s][1]+=1
ben=['baseline','B2_gm_failover','B3_pdv_congestion','B7_topology_change','B_bc_replacement']
att=[s for s in sc if s not in ben and s!='B_unplanned_failover']
sens=sum(sc[s][0]/12 for s in att)/len(att); spec=sum(sc[s][0]/12 for s in ben)/5
ex=sum(sc[s][0] for s in ben if s!='B_bc_replacement')
chk('B6','recomputed v3 sensitivity 0.9896 over 8 attack scenarios',abs(sens-0.98958)<1e-4 and len(att)==8,round(sens,5))
chk('B7','recomputed specificity 0.7833; excl. B_bc = 47/48',abs(spec-0.78333)<1e-4 and ex==47,(round(spec,4),ex))
chk('B8','C1 11/12, B3 11/12, B_bc 0/12, B_unplanned 12/12 UNKNOWN',(sc['C1_removal'][0],sc['B3_pdv_congestion'][0],sc['B_bc_replacement'][0],sc['B_unplanned_failover'][0])==(11,11,0,12),dict((k,sc[k][0]) for k in ['C1_removal','B3_pdv_congestion','B_bc_replacement','B_unplanned_failover']))
# attribution
mis=collections.Counter(); hit=0; natt=0
amap={'A1_rogue_master':'A1','A2_sync_spoof':'A2','A3_replay':'A3','A5_dos_flood':'A5','A8_rogue_bc':'A8','C1_removal':'A_intercept','C2_malformed':'A_malformed','C3_wholesecond':'A_wholesecond'}
for r in runs:
    s=r.split('__r')[0]
    if s in amap:
        natt+=1; h=vd(r,'decision_v3.json').get('fault_hint')
        if h==amap[s]: hit+=1
        else: mis[(s,h)]+=1
chk('B9','attribution 84/96',(hit,natt)==(84,96),(hit,natt))
chk('B10','misattributions A1→A3 ×3, A8→A3 ×4, C3→intercept ×4',mis[('A1_rogue_master','A3')]==3 and mis[('A8_rogue_bc','A3')]==4 and mis[('C3_wholesecond','A_intercept')]==4,dict(mis))
# B_bc
bc=[r for r in runs if r.startswith('B_bc_replacement')]
sec=all(vd(r,'context.json').get('expected_bc_identity_secondary')=='020000fffe0000b1' for r in bc)
rs=all('Unauthorised clock inserted' in ' '.join(vd(r,'decision_v3.json')['reasons']) and vd(r,'decision_v3.json')['verdict']=='ATTACK' for r in bc)
base=all(vd(r,'decision.json')['verdict']=='ATTACK' for r in bc)
dr=open(C+'/run/decision_rule.py').read(); v3=open(C+'/run/decision_rule_v3.py').read()
chk('C1','B_bc: secondary BC id provisioned in all 12 contexts',sec and len(bc)==12,len(bc))
chk('C2','B_bc: all 12 v3 ATTACK via "Unauthorised clock inserted" (A8); base also ATTACK',rs and base,'')
chk('C3','base rule never reads expected_bc_identity_secondary; v3 does',('secondary' not in dr) and ('expected_bc_identity_secondary' in v3),'')
chk('C4','v3 additive-only: returns base ATTACK unchanged','if v==VERDICT_ATTACK:\n        return v,hint,why,ev' in v3,'')
# C1 implementation and draws
rg=open(C+'/run/run_gap.sh').read()
chk('D1','C1 realised as ip link set v-bc-dn down',re.search(r'ip link set v-bc-dn down',rg) is not None,'')
draws=collections.Counter()
for r in runs:
    if r.startswith('C1_removal'):
        t=open(f'{C}/cap/{r}/inject.log').read() if os.path.exists(f'{C}/cap/{r}/inject.log') else ''
        m=re.search(r'\((\d+)%\)',t); draws[m.group(1) if m else None]+=1
chk('D2','C1 draws 75%x6,70%x3,65%x2,60%x1 (55% never)',draws==collections.Counter({'75':6,'70':3,'65':2,'60':1}),dict(draws))
# free_running
cf=glob.glob(V+'/tb/cfg/*'); fr=[f for f in cf if re.search(r'^free_running\s+1',open(f).read(),re.M)]
chk('E1','free_running 1 in every testbed config',len(fr)==len(cf) and len(cf)>0,f'{len(fr)}/{len(cf)}')
# RU logs
cnt=collections.defaultdict(collections.Counter); s2=0; nlog=0
prov={'0a','0b','01','b1'}
for d in sorted(os.listdir(LOGS)):
    if '__r' not in d: continue
    s=d.split('__r')[0]
    for ru in ('ru1','ru2','ru3'):
        t=open(f'{LOGS}/{d}/{ru}.log',errors='ignore').read(); nlog+=1
        sel=re.findall(r'selected best master clock 020000\.fffe\.0000([0-9a-f]{2})',t)
        fm=re.findall(r'new foreign master 020000\.fffe\.0000([0-9a-f]{2})',t)
        c=cnt[s]; c['n']+=1
        c['rogue_sel']+=any(x not in prov for x in sel); c['rogue_fm']+=any(x not in prov for x in fm)
        c['timeout']+='ANNOUNCE_RECEIPT_TIMEOUT_EXPIRES' in t
        c['lines']+=len(re.findall(r'master offset',t)); s2+=bool(re.search(r'master offset\s+-?\d+ s2',t))
chk('F1','504 RU logs, servo s2 in none',nlog==504 and s2==0,(nlog,s2))
chk('F2','A1 36/36 RU logs selected non-provisioned best master',cnt['A1_rogue_master']['rogue_sel']==36,cnt['A1_rogue_master']['rogue_sel'])
chk('F3','A8 36/36 saw rogue BC as new foreign master',cnt['A8_rogue_bc']['rogue_fm']==36,cnt['A8_rogue_bc']['rogue_fm'])
chk('F4','C1 36/36 Announce timeout; B3 12/36; B_bc 36/36',(cnt['C1_removal']['timeout'],cnt['B3_pdv_congestion']['timeout'],cnt['B_bc_replacement']['timeout'])==(36,12,36),(cnt['C1_removal']['timeout'],cnt['B3_pdv_congestion']['timeout'],cnt['B_bc_replacement']['timeout']))
m=lambda s: round(cnt[s]['lines']/cnt[s]['n'],1)
chk('F5','servo lines per RU log: baseline 22.0, C1 7.8, C3 3.0',(m('baseline'),m('C1_removal'),m('C3_wholesecond'))==(22.0,7.8,3.0),(m('baseline'),m('C1_removal'),m('C3_wholesecond')))
chk('F6','A2/A3/A5/C2/C3: no master change in any RU log',all(cnt[s]['rogue_sel']==0 and cnt[s]['rogue_fm']==0 for s in ['A2_sync_spoof','A3_replay','A5_dos_flood','C2_malformed','C3_wholesecond']),'')
# pmc
pm=glob.glob(LOGS+'/*/pmc.jsonl'); lines=0; resp=0
for f in pm:
    for l in open(f):
        lines+=1; d=json.loads(l)
        if not d['raw'].strip().startswith('sending:') or 'RESPONSE' in d['raw']: resp+=1
chk('G1','pmc: 120 files, 48 runs without, 40,320 lines, 0 responses',(len(pm),168-len(pm),lines,resp)==(120,48,40320,0),(len(pm),lines,resp))
pl=open(V+'/tb/run/pmc_log.sh').read()
chk('G2','pmc_log.sh calls pmc without -d (domain)',' -d ' not in pl and 'pmc -u -b 0' in pl,'')
dom=re.search(r'domainNumber\s+(\d+)',open(V+'/tb/cfg/g87251.base').read()).group(1)
chk('G3','ptp4l domainNumber 24',dom=='24',dom)
# pilot S11 / S15 / S14
EP=PR+'/outputs/empirical_software_network_pilot_v1'
s11=open(EP+'/S11_S12_CURRENT_REPORT.md').read()
chk('H1','S11: action 5/5, no_action 0/5',re.search(r'\| action \| 5/5',s11) is not None and re.search(r'\| no_action \| 0/5',s11) is not None,'')
s15=json.load(open(EP+'/S15_INDEPENDENT_VALIDATION_EVALUATION.json'))
txt=json.dumps(s15)
chk('H2','S15 not established; 14/15 and 8/15 present',('8/15' in txt or '0.5333' in txt) and ('14/15' in txt or '0.9333' in txt),re.findall(r'"(?:status|verdict|result|outcome)[^"]*": "[^"]*"',txt)[:3])
sh=open(EP+'/START_HERE_FINAL.md').read()
chk('H3','S14: 232,403 packets, 25 prospective runs (START_HERE_FINAL)','232,403' in sh and '25 fresh prospective S14 runs' in sh,'')
reg=open(EP+'/REMAINING_WORK_ACCEPTANCE_REGISTER.md').read()
chk('H4','register still says S15 zero trials','zero trials in `s15_runs/`' in reg,'')
# B6
B6=PR+'/outputs/B6_two_machine_2026-10-02'
r1=open(B6+'/DRIFT_REPORT.md').read(); r2=open(B6+'/run2/DRIFT_REPORT_run2.md').read()
chk('I1','B6 run1 NOT ESTABLISHED; run2 ESTABLISHED +21.013 [20.623, 21.403]','NOT ESTABLISHED' in r1 and 'ESTABLISHED' in r2 and '+21.013 ppm  [+20.623, +21.403]' in r2,'')
chk('I2','B6 arm A -4.189 (run1) vs -2.877 (run2)','-4.189 ppm' in r1 and '-2.877 ppm' in r2,'')
# TIMESAFE origin
gc=open(PR+'/dataset/legitimate/timesafe_real_hardware_captures/s-plane_security_repo/.git/config').read()
chk('J1','TIMESAFE data from github.com/genesys-neu/s-plane_security','github.com/genesys-neu/s-plane_security' in gc,'')
# walkthrough withdrawal
wt=glob.glob(PR+'/99_ARCHIVE_OLDER_AND_SUPERSEDED/documents_2026-09-20_superseded_by_09-29/ORAN_Project_Walkthrough_2026-09-17.pdf')[0]
import subprocess; wtxt=subprocess.run(['pdftotext',wt,'-'],capture_output=True,text=True).stdout
chk('J2','17 Sep walkthrough withdraws August figures (duplicates; 12 of 28 features)','no longer used as evidence' in wtxt and '12 of the 28 features' in wtxt,'')
# reorg
man=list(csv.DictReader(open(PR+'/99_ARCHIVE_OLDER_AND_SUPERSEDED/MOVE_MANIFEST_2026-10-03.csv')))
_del=set(r['path'] for r in csv.DictReader(open(PR+'/99_ARCHIVE_OLDER_AND_SUPERSEDED/DELETION_LOG_2026-10-05_PPT.csv')))
_k1miss=[m['new_path'] for m in man if not os.path.lexists(os.path.join(PR,m['new_path'])) and m['new_path'] not in _del]
chk('K1','41 moves: every destination exists or was later deleted per DELETION_LOG; no source left',len(man)==41 and not _k1miss and not any(os.path.lexists(os.path.join(PR,m['original_path'])) for m in man),(len(man),_k1miss,sum(m['new_path'] in _del for m in man)))
# decks
h=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
L=PR+'/00_LATEST_PRESENTED_DECK_AND_DELIVERABLES'
dl=os.path.expanduser('~/mnt/Downloads/ORAN_SPlane_PRISM_Review_v7_FINAL.pptx')
chk('L1','presented copy byte-identical to Downloads v7_FINAL (08:37 save)',h(L+'/ORAN_SPlane_PRISM_Review_v7_FINAL_PRESENTED_2026-09-29.pptx')==h(dl),h(dl)[:12])
chk('L2','v8 sha256 7e1e54ec… (slide 33 fix 5 Oct)',h(L+'/ORAN_SPlane_PRISM_Review_v8.pptx').startswith('7e1e54ec'),'')
decks=[os.path.join(dp,f) for dp,dn,fn in os.walk(PR) if '/.git' not in dp and 'node_modules' not in dp and '/.venv' not in dp for f in fn if f.lower().endswith(('.pptx','.ppt'))]
chk('M1','only v7_FINAL_PRESENTED and v8 decks remain in the project',sorted(os.path.basename(x) for x in decks)==['ORAN_SPlane_PRISM_Review_v7_FINAL_PRESENTED_2026-09-29.pptx','ORAN_SPlane_PRISM_Review_v8.pptx'],len(decks))
dl_or=[f for f in os.listdir(os.path.expanduser('~/mnt/Downloads')) if f.lower().endswith('.pptx') and 'ORAN' in f.upper()]
chk('M2','Downloads keeps only ORAN_SPlane_PRISM_Review_v7_FINAL.pptx among O-RAN decks',dl_or==['ORAN_SPlane_PRISM_Review_v7_FINAL.pptx'],dl_or)
dlog=list(csv.DictReader(open(PR+'/99_ARCHIVE_OLDER_AND_SUPERSEDED/DELETION_LOG_2026-10-05_PPT.csv')))
chk('M3','deletion log: 53 entries (9 Downloads, 44 AI-Native)',(len(dlog),sum(r['location']=='Downloads' for r in dlog))==(53,9),len(dlog))
man2=list(csv.DictReader(open(PR+'/99_ARCHIVE_OLDER_AND_SUPERSEDED/MOVE_MANIFEST_2026-10-04.csv')))
chk('K2','14 moves on 4 Oct, all destinations exist, no source left',len(man2)==14 and all(os.path.lexists(os.path.join(PR,m['new_path'])) for m in man2) and not any(os.path.lexists(os.path.join(PR,m['original_path'])) for m in man2),len(man2))
for r in R: print('\t'.join(map(str,r)))
print('TOTAL',len(R),'FAIL',sum(r[1]=='FAIL' for r in R))
