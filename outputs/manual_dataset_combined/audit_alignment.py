import csv,json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2]; D=R/'dataset/timesafe'; U=D/'s-plane_security_repo'
pairs=[
 ('production',D/'timesafe_prod_successful_announce_attack_ptp.csv',D/'timesafe_prod_successful_announce_attack_labeled.csv'),
 ('announce_1',U/'DataCollectionPTP/15min_announce_attack.csv',D/'timesafe_multi_raw/announce_session_1_labels.csv'),
 ('announce_2',U/'DataCollectionPTP/2024-10-06-announce_attack_UEdata.csv',D/'timesafe_multi_raw/announce_session_2_labels.csv'),
 ('announce_3',U/'DataCollectionPTP/2024-10-08-announce_attack1.csv',D/'timesafe_multi_raw/announce_session_3_labels.csv'),
 ('sync_followup',U/'DataCollectionPTP/2024-10-08-sync_attack1.csv',D/'timesafe_multi_raw/sync_followup_session_labels.csv'),
 ('sync_singlestep',U/'DataCollectionPTP/2024-10-08-sync_attack_singlestep1.csv',D/'timesafe_multi_raw/sync_singlestep_session_labels.csv')]
mapping={'Sync':'0','Delay_Req':'1','PDelay_Req':'2','PDelay_Resp':'3','Follow_Up':'8','Delay_Resp':'9','PDelay_Resp_Follow_Up':'10','Announce':'11','Signaling':'12','Management':'13'}
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
results=[]
for name,rp,lp in pairs:
 raw=read(rp);a=[x for x in raw if 'ptp' in x.get('Protocol','').lower()];b=read(lp);t=0.;mx=0.;errors=Counter();ids={}
 for h in ['Source','Destination']:
  for row in a:
   if row[h] not in ids:ids[row[h]]=str(len(ids))
 for x,y in zip(a,b):
  for h in ['Length','SequenceID']:
   if x[h]!=y[h]:errors[h]+=1
  if mapping.get(x['MessageType'],x['MessageType'])!=y['MessageType']:errors['MessageType']+=1
  for h in ['Source','Destination']:
   if ids[x[h]]!=y[h]:errors[h]+=1
  t+=float(y['Time Interval']);mx=max(mx,abs(t-(float(x['Time'])-float(a[0]['Time']))))
 results.append({'pair':name,'raw_rows':len(raw),'ptp_rows':len(a),'labeled_rows':len(b),'field_mismatches':dict(errors),'max_relative_time_error_seconds':mx,'label_counts':dict(Counter(x['Label'] for x in b))})
 print(results[-1],flush=True)
a=read(pairs[1][2]);b=read(pairs[2][2])
duplicates={'pair':['announce_1','announce_2'],'rows':len(a),'identical_nonlabel_rows':sum(all(x[k]==y[k] for k in x if k!='Label') for x,y in zip(a,b)),'conflicting_labels':sum(x['Label']!=y['Label'] for x,y in zip(a,b))}
out={'purpose':'Read-only alignment audit. No new labels assigned; field agreement is not validation of label meaning.','pairs':results,'duplicate_label_conflict':duplicates}
(Path(__file__).parent/'alignment_audit.json').write_text(json.dumps(out,indent=2))
