from __future__ import annotations
import hashlib, json
from collections import Counter
from pathlib import Path
from streaming_discriminator_v1 import StreamState, observe, packet_from_frame
from ingest.ptp_wire import read_pcap

HERE = Path(__file__).resolve().parent; RUNS = HERE / "runs"
DECLARED = {
 "20260912_streamtest_baseline":"baseline_control", "20260912_streamtest_netem":"netem_delay_jitter_loss",
 "20260912_streamtest_control_retry":"authorized_source_change_no_action_control", "20260912_streamtest_source_stop_retry":"authorized_source_change_intervention"}
def digest(path):
 h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def evaluate(name, declared_condition):
 path=RUNS/name/"capture.pcap"; capture_id=digest(path); state=StreamState(); counts=Counter(); event_counts=Counter(); first={}; first_events={}; start=None
 for ts_ns, frame in read_pcap(str(path)):
  ts=ts_ns/1e9; start=ts if start is None else start
  out=observe(state, packet_from_frame(capture_id,ts,frame)); kind=out["classification"]; counts[kind]+=1
  if kind not in first: first[kind]=round(ts-start,9)
  for event in out["events"]:
   kind=event["type"]; event_counts[kind]+=1
   if kind not in first_events: first_events[kind]=round(ts-start,9)
 return {"declared_condition_for_evaluation_only":declared_condition,"capture_sha256":capture_id,"packet_count":sum(counts.values()),"state_counts":dict(counts),"event_counts":dict(event_counts),"first_state_time_s_from_capture_start":first,"first_event_time_s_from_capture_start":first_events,"validity":"STRUCTURAL_VALIDATION_REQUIRED_SEPARATELY"}
def main():
 out={"schema_version":"streaming-protocol-v2-development-evaluation","scope":"four v1 captures are development/regression evidence after a silence-composition defect; not held-out evidence","runs":{n:evaluate(n,c) for n,c in DECLARED.items()},"limits":["one fresh run per condition","no EOF features","arrival-driven silence unless tick is supplied","source silence is observation only","no receiver service, attack, health, physical-clock, or recovery inference"]}
 (HERE/"STREAMING_PROTOCOL_V1_FRESH_EVALUATION.json").write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps(out,indent=2))
if __name__=="__main__": main()
