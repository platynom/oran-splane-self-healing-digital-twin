"""Verify alignment and replay the supplied labeling rule without altering sources."""
import csv,json,hashlib,math,runpy,os
from pathlib import Path
from decimal import Decimal
from collections import Counter
B=Path(__file__).resolve().parent; R=B.parents[1]; D=R/'dataset/timesafe'
paths={'raw':D/'timesafe_prod_successful_announce_attack_ptp.csv','labels':D/'timesafe_prod_successful_announce_attack_labeled.csv','upstream_labels':D/'s-plane_security_repo/Production_Environment/prod_successful_announce_attack.csv','attack_times':D/'s-plane_security_repo/DataCollectionPTP/announce_attack_only2.csv','labeling_code':D/'s-plane_security_repo/Production_Environment/prodtest_dataset_gen.py'}
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
a,b,e=read(paths['raw']),read(paths['labels']),read(paths['attack_times'])
assert b==read(paths['upstream_labels']), 'Packaged labels differ from upstream local labels'
assert len(a)==len(b)==13565
codes={}
for h in ['Source','Destination']:
 for x in a:
  if x[h] not in codes:codes[x[h]]=str(len(codes))
times={Decimal(x['Time']) for x in e}; expected_sender='b8:ce:f6:5e:6a:fa'
t=0.; maxerr=0.; issues=[]; positives=[]; reproduced=Counter()
with (B/'issue01_production_linked.jsonl').open('w',encoding='utf-8') as out:
 for index,(x,y) in enumerate(zip(a,b),2):
  assert all(codes[x[h]]==y[h] for h in ['Source','Destination'])
  assert all(x[h]==y[h] for h in ['Length','SequenceID','MessageType'])
  t+=float(y['Time Interval']);err=abs(t-float(x['Time']));maxerr=max(maxerr,err)
  assert err<=1e-9
  reconstructed=int(x['Source']==expected_sender and Decimal(x['Time']) in times)
  reproduced[str(reconstructed)]+=1
  if reconstructed!=int(y['Label']):issues.append(index)
  if y['Label']=='1':positives.append(x)
  out.write(json.dumps({'raw_csv_row':index,'label_csv_row':index,'original_packet':x,'original_labeled_record':y,'alignment_verified':True,'label_status':'Supplied label; scientific ground truth not independently verified','supplied_rule_result':reconstructed,'rule_agrees_with_supplied_label':reconstructed==int(y['Label'])})+'\n')
result={'scope':'Issue 1: production capture only; all other sessions remain unaudited at this depth.','source_files':{k:str(p.relative_to(R)) for k,p in paths.items()},'source_sha256':hashes,'rows':len(a),'unique_raw_records':len(set(tuple(x.items()) for x in a)),'address_encoding':codes,'alignment_max_time_error_seconds':maxerr,'existing_label_counts':dict(Counter(x['Label'] for x in b)),'reconstructed_label_counts':dict(reproduced),'rule_mismatch_count':len(issues),'mismatching_csv_rows':issues,'labeled_positive_senders':sorted({x['Source'] for x in positives}),'rule_sender':expected_sender,'labeled_positive_message_types':dict(Counter(x['MessageType'] for x in positives)),'labeled_positive_time_range_seconds':[positives[0]['Time'],positives[-1]['Time']],'conclusion':'Alignment verified. Supplied labels retained for provenance, not promoted to validated ground truth. Current labeling rule and referenced evidence do not reproduce the saved positive labels. No automatic recovery or attack truth inferred.'}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[k] for k,p in paths.items())
import pandas as pd
original_cwd=Path.cwd()
try:
 namespace=runpy.run_path(str(paths['labeling_code']))
 os.chdir(paths['labeling_code'].parent)
 actual=namespace['label_data'](pd.read_csv(paths['raw']).copy())
 result['unmodified_upstream_function_label_counts']={str(k):int(v) for k,v in actual['Label'].value_counts().items()}
 assert actual['Label'].tolist()==[int(x['Source']==expected_sender and Decimal(x['Time']) in times) for x in a]
finally:os.chdir(original_cwd)
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[k] for k,p in paths.items())
(B/'issue01_production_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['rows','alignment_max_time_error_seconds','existing_label_counts','reconstructed_label_counts','rule_mismatch_count','labeled_positive_senders','rule_sender','conclusion']},indent=2))
