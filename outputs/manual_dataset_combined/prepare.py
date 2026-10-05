import csv, json, hashlib, re, math
from pathlib import Path
from collections import OrderedDict, Counter

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
DATA=ROOT/'dataset'
CHUNK=8000
groups=OrderedDict((k,[]) for k in ['TIMESAFE packets','TIMESAFE raw captures','TIMESAFE telemetry','Netem telemetry','Netem decisions','Netem run records','Simulated telemetry','Simulated windows','Model metrics'])
files=sorted(p for p in DATA.rglob('*.csv') if 's-plane_security_repo' not in p.parts)
up=DATA/'timesafe/s-plane_security_repo'
files += [up/'Production_Environment/prod_successful_announce_attack.csv']
files += [up/'DataCollectionPTP'/n for n in ['15min_announce_attack.csv','2024-10-06-announce_attack_UEdata.csv','2024-10-08-announce_attack1.csv','2024-10-08-sync_attack1.csv','2024-10-08-sync_attack_singlestep1.csv']]

def group(p):
    if p.name=='splane_telemetry.csv': return 'Simulated telemetry'
    if p.name=='splane_windows.csv': return 'Simulated windows'
    if 'timesafe' in p.parts:
        if 'DataCollectionPTP' in p.parts or p.name.endswith('_ptp.csv'): return 'TIMESAFE raw captures'
        if 'telemetry' in p.name or 'timesafe_sessions' in p.parts: return 'TIMESAFE telemetry'
        return 'TIMESAFE packets'
    if p.name=='discriminator_metrics.csv': return 'Model metrics'
    if 'decisions' in p.name and 'telemetry' not in p.name: return 'Netem decisions'
    if p.name in ['netem_run_status.csv','netem_partial_capture_summary.csv']: return 'Netem run records'
    return 'Netem telemetry'

rules=[
 ['R00','No row label','Not assigned','A capture/session name alone does not label every packet. No recovery is inferred.'],
 ['R01','Benign or healthy source label','safe_default','No corrective intervention inferred from this label. Benign packets do not prove the entire network is healthy.'],
 ['R02','Announce/spoof attack label','isolate_rogue_master','Candidate only after identifying and confirming an unauthorized master or malicious sender. Verify a trusted remaining source.'],
 ['R03','Sync manipulation or replay attack label','failover_lls_c1','Candidate only if an independent, trusted LLS-C1 configuration exists and avoids the compromised path/source.'],
 ['R04','PDV/congestion/loss fault label','reroute_path','Candidate only if an alternative path has adequate timing performance; verify offset and delay after changing it.'],
 ['R05','Loss of reference/holdover fault label','holdover','Temporary candidate only while oscillator error remains inside the timing budget. Restore a trustworthy source.'],
 ['R06','GNSS attack label','failover_lls_c1','Candidate only if an independently trusted PTP timing source/configuration exists and does not depend on compromised GNSS.'],
 ['R07','Other or insufficiently specified fault/attack','safe_default','Conservative proposal pending diagnosis; the label alone does not select a specific fix.'],
 ['R08','Invalid or unknown telemetry','safe_default','Cannot establish clock health from absent/untrusted observations; inspect telemetry/reference availability.'],
 ['R09','Recorded decision row','Not assigned','Situation is the recorded model output, not ground truth. Existing action is preserved separately in the source action column.'],
 ['R10','Summary/metric row','Not applicable','This row summarizes an experiment or model; it is not a timing observation.'],
]
rulemap={r[0]:r for r in rules}
def classify(r,p,g):
    label=r.get('label',r.get('Label','')).strip()
    scenario=r.get('scenario','')
    family=r.get('attack_family','')
    text=(scenario+' '+family+' '+p.name).lower()
    if g in ['Netem run records','Model metrics']:
        return ['R10','Run status / metric, not a sample label',r.get('status','Model metric'),'Not applicable']
    if g=='Netem decisions':
        return ['R09','Recorded model decision',label or 'Unlabeled','Not assigned']
    if r.get('telemetry_valid','').lower()=='false':
        return ['R08','Manual validity override; original label retained','Unknown — invalid telemetry','safe_default']
    if not label or label.lower() in ['unlabeled','unknown','nan']:
        return ['R00','No usable source row label','Unlabeled','Not assigned']
    timesafe=g.startswith('TIMESAFE')
    benign=label=='0' or label=='healthy' or (timesafe and label=='H0')
    if benign:
        return ['R01','Existing source label','Benign packet' if label=='0' else ('Benign segment' if timesafe else 'Healthy'),'safe_default']
    if label in ['1','H1']:
        if 'gnss' in text: rule='R06'; situation='Attack — '+(scenario or family)
        elif 'announce' in text or 'ptp_spoof' in text: rule='R02'; situation='Attack — Announce/master spoofing'
        elif any(x in text for x in ['sync','replay']): rule='R03'; situation='Attack — '+('replay' if 'replay' in text else 'Sync manipulation')
        else: rule='R07'; situation='Attack — '+(family or scenario or 'unspecified')
    elif label=='H0':
        if any(x in text for x in ['pdv','congestion','traffic_burst','netem_loss']): rule='R04'
        elif any(x in text for x in ['holdover','gnss_loss']): rule='R05'
        else: rule='R07'
        situation='Benign fault — '+(scenario or 'unspecified')
    else: rule='R07'; situation=label
    return [rule,'Existing row label + source scenario/family',situation,rulemap[rule][2]]

def typed(v,h):
    if v=='': return None
    # Preserve identifiers and non-finite source tokens exactly; Excel has 15-digit precision.
    if any(x in h.lower() for x in ['identity','source','destination','capture_id']) or h in ['Source','Destination']:
        return v
    if v in ['True','False']: return v=='True'
    if re.fullmatch(r'[+-]?\d+',v):
        return int(v) if len(v.lstrip('+-').lstrip('0'))<=15 and not (len(v)>1 and v.startswith('0')) else v
    if re.fullmatch(r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?',v):
        f=float(v)
        return f if math.isfinite(f) else v
    return "'"+v if v.startswith('=') else v

catalog=[]; hashes={}; descriptors=[]; counts=Counter()
for i,p in enumerate(files,1):
    with p.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); headers=reader.fieldnames; n=sum(1 for _ in reader)
    sha=hashlib.sha256(p.read_bytes()).hexdigest(); sid=f'S{i:03}'
    duplicate=hashes.get(sha,''); hashes.setdefault(sha,sid)
    g=group(p)
    evidence=('Simulated' if g.startswith('Simulated') else 'Model result; training provenance not inferred' if g=='Model metrics' else 'Real capture, author-encoded packet labels' if g=='TIMESAFE packets' else 'Real packet capture export; no row labels' if g=='TIMESAFE raw captures' else 'Real capture-derived; inferred/default fields present' if g=='TIMESAFE telemetry' else 'Software testbed; inferred/default fields present' if g=='Netem telemetry' else 'Recorded software-testbed decisions' if g=='Netem decisions' else 'Software-testbed run summary')
    groups[g].append((sid,p,headers,n))
    catalog.append([sid,str(p.relative_to(ROOT)).replace('\\','/'),g,n,len(headers),evidence,duplicate or 'None',sha])

meta={'sheets':[], 'sources':catalog,'rules':rules}
def emit_sheet(name,headers,rows):
    index=len(meta['sheets']); desc={'name':name,'headers':headers,'parts':[],'rows':0,'columns':len(headers)}
    part=[]
    def flush():
        path=BASE/f'part_{index:02}_{len(desc["parts"]):03}.json'
        path.write_text(json.dumps({'name':name,'headers':headers,'rows':part},ensure_ascii=False,allow_nan=False),encoding='utf-8')
        desc['parts'].append(path.name)
    for row in rows:
        assert len(row)==len(headers),(name,len(row),len(headers))
        part.append(row); desc['rows']+=1
        if len(part)==CHUNK: flush(); part=[]
    if part: flush()
    meta['sheets'].append(desc)
    print(name,desc['rows'],desc['columns'],flush=True)

notes=[
 ['Scope','All rows and columns from the current CSV files directly under dataset/Netem, dataset/Synthetic S-Plane, dataset/timesafe and their project-generated subfolders; selected upstream raw capture CSVs and the original production labeled CSV are also included.'],
 ['Excluded','Historical upstream archives/training merges, old project generations, binary pcaps, and results outside the dataset folder. No sampling or row truncation of included CSVs.'],
 ['Start','TIMESAFE packets contains the original small packet schema. Filter Source_ID using Sources to select the production capture or one session.'],
 ['Row meaning','Packets, capture exports, processed telemetry, window features, recorded decisions, and run summaries remain separate. They are not joined by row number or timestamp.'],
 ['Final columns','Situation_classification interprets the existing label in its dataset context. Proposed_recovery_action is a conditional manual proposal, not an executed recovery or recorded ground truth. Rule_ID links to Recovery rules.'],
 ['Real versus simulated','TIMESAFE is real experimental capture data. Netem is a software linuxptp/netem testbed, not hardware validation. Simulated sheets contain generated data, including copies stored in the Netem folder.'],
 ['Derived fields','Real-source telemetry is not entirely direct measurement. Ingest may supply defaults for SyncE/oscillator/reference fields and infer GNSS or holdover state from PTP. Preserve values but do not treat these as hardware observations.'],
 ['Labels','TIMESAFE packet Label 0/1 means benign/attack packet. TIMESAFE telemetry H0/H1 means benign/attack segment. Simulated and Netem H0 means benign fault, H1 attack; healthy is separate.'],
 ['Validity','Explicit telemetry_valid=False receives Unknown — invalid telemetry and safe_default in the added analysis columns even if original label says healthy. Original values remain intact.'],
 ['Decisions','Netem decisions preserves model label and action exactly. Proposed recovery is Not assigned so the recorded recommendation is not misrepresented as a new manual diagnosis.'],
 ['Missing values','Empty source cells stay blank; columns absent in a file stay blank in the union schema. Source nan/inf tokens stay text. No missing measurements are fabricated.'],
 ['Precision','Ordinary numeric cells are numeric. Identifiers and integers longer than 15 digits stay text. Decimal values have Excel floating-point precision; source CSVs remain authoritative for lexical precision.'],
 ['Duplicates','All included CSV rows are retained, including repeated captures, combined/per-scenario files and exact copies. Sources marks exact byte duplicates; do not count these as independent experiments.'],
 ['Disabled features','Every source feature column is retained, including experimental cross-source columns. Presence does not mean the current 28-feature model uses it; see Parameter roles.'],
 ['Recovery limits','Labels/scenarios guide conditional proposals. No new classifier was run. No recovery success or physical execution is claimed. Broad binary labels do not prove an attack subtype independently of session context.'],
]
emit_sheet('Read me',['Topic','Explanation'],notes)
emit_sheet('Sources',['Source_ID','Source_file','Data_sheet','Data_rows','Source_columns','Evidence_type','Exact_duplicate_of','SHA256'],catalog)
emit_sheet('Recovery rules',['Rule_ID','Situation','Proposed_recovery_action','Required interpretation / condition'],rules)

for g,entries in groups.items():
    cols=list(dict.fromkeys(h for _,_,hs,_ in entries for h in hs))
    headers=['Source_ID','Source_row']+cols+['Rule_ID','Classification_basis','Situation_classification','Proposed_recovery_action']
    def rows():
        for sid,p,hs,n in entries:
            with p.open(encoding='utf-8-sig',newline='') as f:
                for num,r in enumerate(csv.DictReader(f),2):
                    extra=classify(r,p,g); counts[(g,extra[-2],extra[-1])]+=1
                    yield [sid,num]+[typed(r.get(h,''),h) for h in cols]+extra
    emit_sheet(g,headers,rows())
meta['classification_counts']=[list(k)+[v] for k,v in counts.items()]
(BASE/'manifest.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
print('TOTAL',sum(s['rows'] for s in meta['sheets'][3:]),'FILES',len(files),flush=True)
