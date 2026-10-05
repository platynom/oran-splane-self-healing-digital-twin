from __future__ import annotations
import hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path
from streaming_discriminator_v1 import StreamState, observe, packet_from_frame
from ingest.ptp_wire import read_pcap

HERE=Path(__file__).resolve().parent; RUNS=HERE/"runs"
PLAN={"baseline_control":["20260913_v2_b1","20260913_v2_b2","20260913_v2_b3"],"netem_delay_jitter_loss":["20260913_v2_n1","20260913_v2_n2","20260913_v2_n3"],"authorized_source_change_no_action_control":["20260913_v2_c1","20260913_v2_c2_retry","20260913_v2_c3"],"authorized_source_change_intervention":["20260913_v2_s1_retry","20260913_v2_s2","20260913_v2_s3"]}
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def verify_frozen_inputs(protocol_path: Path | None = None, engine_path: Path | None = None, stream_protocol_path: Path | None = None):
 protocol_path = protocol_path or HERE/"V2_REPEATED_EVALUATION_PROTOCOL.json"
 engine_path = engine_path or HERE/"streaming_discriminator_v1.py"
 stream_protocol_path = stream_protocol_path or HERE/"STREAMING_PROTOCOL_V2.json"
 frozen=json.loads(protocol_path.read_text())["frozen_inputs"]
 actual={"streaming_discriminator_v1.py_sha256":sha(engine_path),"STREAMING_PROTOCOL_V2.json_sha256":sha(stream_protocol_path)}
 mismatch={key:{"expected":frozen[key],"actual":value} for key,value in actual.items() if frozen[key].lower()!=value.lower()}
 if mismatch: raise RuntimeError(f"frozen input hash mismatch: {json.dumps(mismatch, sort_keys=True)}")
 return actual
def one(name):
 p=RUNS/name/"capture.pcap"; cid=sha(p); state=StreamState(); states=Counter(); events=Counter(); first={}; start=None
 for ns,frame in read_pcap(str(p)):
  ts=ns/1e9; start=ts if start is None else start; out=observe(state,packet_from_frame(cid,ts,frame)); states[out["classification"]]+=1
  if out["classification"] not in first:first[out["classification"]]=ts-start
  for e in out["events"]:
   events[e["type"]]+=1
   if e["type"] not in first:first[e["type"]]=ts-start
 return {"capture_sha256":cid,"packet_records":sum(states.values()),"state_counts":dict(states),"event_counts":dict(events),"first_event_or_state_s":{k:round(v,9) for k,v in first.items()},"any_CONFIGURED_IMPAIRMENT_SUSPECT":states["CONFIGURED_IMPAIRMENT_SUSPECT"]>0,"any_SOURCE_ANNOUNCE_SILENCE_OBSERVED":events["SOURCE_ANNOUNCE_SILENCE_OBSERVED"]>0}
def wilson(k,n,z=1.95996398454):
 if not n:return None
 p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return {"k":k,"n":n,"proportion":p,"wilson95":[max(0,c-r),min(1,c+r)]}
def main():
 frozen_input_verification=verify_frozen_inputs()
 runs={c:{n:one(n) for n in names} for c,names in PLAN.items()}; summary={}
 for c,items in runs.items():
  rows=list(items.values()); summary[c]={"impairment_suspect":wilson(sum(x["any_CONFIGURED_IMPAIRMENT_SUSPECT"] for x in rows),len(rows)),"source_silence":wilson(sum(x["any_SOURCE_ANNOUNCE_SILENCE_OBSERVED"] for x in rows),len(rows))}
 out={"schema_version":"v2-repeated-run-evaluation-v1","protocol":"V2_REPEATED_EVALUATION_PROTOCOL.json","frozen_input_verification":frozen_input_verification,"scope":"predeclared n=3 per condition isolated software feasibility; intervals descriptive","runs":runs,"run_level_summary":summary,"excluded_partial_attempts":["20260913_v2_s1","20260913_v2_c2"],"limits":["run labels are evaluation metadata, never engine features","free_running shared-host software clocks","no physical timing/recovery/attack/health inference"]}
 (HERE/"V2_REPEATED_EVALUATION.json").write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2))
if __name__=="__main__":main()
