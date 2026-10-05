"""Prepare exact raw/annotation linkage for the bounded production review."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
RAW=ROOT/'dataset/timesafe/timesafe_prod_successful_announce_attack_ptp.csv'
LAB=ROOT/'dataset/timesafe/timesafe_prod_successful_announce_attack_labeled.csv'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
with RAW.open(encoding='utf-8-sig',newline='') as f: raw=list(csv.reader(f))
with LAB.open(encoding='utf-8-sig',newline='') as f: labeled=list(csv.reader(f))
assert len(raw)==len(labeled)==13566
headers, raw_rows=raw[0],raw[1:]
label_headers,label_rows=labeled[0],labeled[1:]
assert label_headers==['Source','Destination','Length','SequenceID','MessageType','Time Interval','Label']
# The supplied annotation representation is a decoder-derived projection, not a
# lexical copy of S027: endpoint IDs are encounter-order IDs, MessageType is the
# PTP numeric code, and Time Interval is the per-row elapsed time.  Verify that
# documented projection exactly without altering either source representation.
codes={'Sync':'0','Delay_Req':'1','PDelay_Req':'2','PDelay_Resp':'3','Follow_Up':'8','Delay_Resp':'9','PDelay_Resp_Follow_Up':'10','Announce':'11','Signaling':'12','Management':'13'}
endpoint={}
for field in (1,2):
    for row in raw_rows:
        if row[field] not in endpoint: endpoint[row[field]]=str(len(endpoint))
elapsed=0.0
for prior, (raw, labeled) in enumerate(zip(raw_rows,label_rows)):
    assert labeled[0]==endpoint[raw[1]] and labeled[1]==endpoint[raw[2]]
    assert labeled[2]==raw[4] and labeled[3]==raw[5]
    assert labeled[4]==codes.get(raw[6],raw[6])
    if prior:
        expected=float(raw[0])-float(raw_rows[prior-1][0])
    else:
        expected=0.0
    assert abs(float(labeled[5])-expected)<1e-12
labels=[r[-1] for r in label_rows]
positives=[i+1 for i,v in enumerate(labels) if v=='1']
assert len(positives)==200 and set(labels)<= {'0','1'}
plan={'raw':str(RAW.relative_to(ROOT)).replace('\\','/'),'labels':str(LAB.relative_to(ROOT)).replace('\\','/'),'raw_sha256':sha(RAW),'label_sha256':sha(LAB),'rows':len(raw_rows),'raw_headers':headers,'label_headers':label_headers,'label_header':'Label','positive_count':len(positives),'zero_count':labels.count('0'),'first_positive_record':positives[0],'last_positive_record':positives[-1],'first_positive_time':raw_rows[positives[0]-1][headers.index('Time')],'last_positive_time':raw_rows[positives[-1]-1][headers.index('Time')],'linkage':'Exact decoder-projection correspondence verified for all rows: encounter-order endpoint IDs, Length, SequenceID, numeric MessageType, per-row elapsed time, and supplied Label.'}
(BASE/'manual_reviews'/'01_production_announce_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
print(json.dumps(plan,indent=2))
