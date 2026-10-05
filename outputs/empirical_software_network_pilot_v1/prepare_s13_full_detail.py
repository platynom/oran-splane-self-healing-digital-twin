"""Create lossless, row-level CSV sources for the S13 full-detail workbook."""
from __future__ import annotations
import csv, hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent; OUT=HERE/"s13_dataset"; APP=HERE.parents[1]/"01_CURRENT_SPlane_SelfHealing"/"oran_splane_selfhealing"
import sys; sys.path.insert(0,str(APP))
from ingest.ptp_wire import read_pcap,parse_eth_frame,decode_ptp_payload,MSG_NAME

def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def write(name,fields,rows):
 with (OUT/name).open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def main():
 packet=[]; events=[]; decision=[]; receiver=[]; receiver_log=[]
 s11=json.loads((HERE/"S11_CLOSED_LOOP_EVALUATION.json").read_text())
 sealed_lines={r["run"]: (r["input_integrity"].get("decision_log_post_seal_append") or {}).get("sealed_lines")
               for arm in s11["runs"].values() for r in arm.values()}
 for base in ("runs","v3_runs","v4_runs","v5_runs","s11_runs"):
  root=HERE/base
  if not root.is_dir(): continue
  for d in sorted(x for x in root.iterdir() if x.is_dir()):
   for cap in sorted(d.glob("*.pcap")):
    cap_hash=sha(cap)
    for ordinal,(ts,frame) in enumerate(read_pcap(str(cap)),1):
     payload=parse_eth_frame(frame); msg=decode_ptp_payload(payload) if payload else None
     hdr=payload if payload and len(payload)>=34 else None
     packet.append({"run_id":d.name,"batch_directory":base,"capture_file":cap.name,"capture_sha256":cap_hash,"packet_ordinal":ordinal,"capture_timestamp_ns":ts,"frame_length_bytes":len(frame),"frame_hex":frame.hex(),"ptp_decoded":msg is not None,"message_type":MSG_NAME[msg.msg_type] if msg else "UNKNOWN_OR_NOT_PTP","transport_specific":(hdr[0]>>4 if hdr else None),"ptp_version":(hdr[1]&15 if hdr else None),"declared_message_length":(int.from_bytes(hdr[2:4],'big') if hdr else None),"domain_number":(hdr[4] if hdr else None),"flags_hex":(hdr[6:8].hex() if hdr else None),"source_port_identity_hex":(hdr[20:30].hex() if hdr else None),"log_message_interval":(int.from_bytes(hdr[33:34],'big',signed=True) if hdr else None),"sequence_id":msg.seq_id if msg else None,"correction_ns":msg.correction_ns if msg else None,"origin_timestamp_ns":msg.origin_ts_ns if msg else None,"grandmaster_priority1":msg.grandmaster_priority1 if msg else None,"grandmaster_clock_class":msg.grandmaster_clock_class if msg else None,"grandmaster_clock_accuracy":msg.grandmaster_clock_accuracy if msg else None,"offset_scaled_log_variance":msg.offset_scaled_log_variance if msg else None,"grandmaster_priority2":msg.grandmaster_priority2 if msg else None,"grandmaster_identity_hex":msg.grandmaster_identity.hex() if msg and msg.grandmaster_identity else None,"steps_removed":msg.steps_removed if msg else None,"time_source":msg.time_source if msg else None,"decoder_scope":"local PTP-over-Ethernet v2 subset; raw frame_hex is retained for unsupported/TLV bytes"})
   for log in ("events.log","decision_log.jsonl"):
    p=d/log
    if not p.is_file(): continue
    for ordinal,line in enumerate(p.read_text(errors="replace").splitlines(),1):
     row={"run_id":d.name,"batch_directory":base,"source_file":log,"source_sha256":sha(p),"source_line_ordinal":ordinal,"original_line":line}
     if log.endswith("jsonl"):
      if d.name in sealed_lines:
       sealed=sealed_lines[d.name]
       row["s11_seal_scope"]=("SEALED_FULL_LOG_EVALUATION_EVIDENCE" if sealed is None else
                               "SEALED_PREFIX_EVALUATION_EVIDENCE" if ordinal<=sealed else
                               "POST_SEAL_APPENDED_NOT_EVALUATION_EVIDENCE")
      else: row["s11_seal_scope"]="NOT_S11_EVALUATION_INPUT"
      try: row.update({f"json_{k}":v for k,v in json.loads(line).items()})
      except Exception: row["parse_status"]="MALFORMED"
      decision.append(row)
     else: events.append(row)
   p=d/"slave.log"
   if p.is_file():
    for ordinal,line in enumerate(p.read_text(errors="replace").splitlines(),1):
     receiver_log.append({"run_id":d.name,"batch_directory":base,"source_file":"slave.log","source_sha256":sha(p),"source_line_ordinal":ordinal,"original_line":line,"timebase":"ptp4l printed timestamp basis not established; no mapping to detector/capture clocks"})
     m=re.search(r"ptp4l\[([\d.]+)\]: port (\d+): (.+)$",line)
     if m: receiver.append({"run_id":d.name,"batch_directory":base,"source_file":"slave.log","source_sha256":sha(p),"source_line_ordinal":ordinal,"original_line":line,"ptp4l_timestamp_text":m.group(1),"port_number":m.group(2),"transition_or_message":m.group(3),"timebase":"ptp4l printed timestamp basis not established; no numeric join to detector/capture clocks"})
 s12=json.loads((HERE/"S12_MEASURED_OUTCOME.json").read_text())
 outcome=[]
 for arm,rs in s12["runs"].items():
  for run,row in rs.items(): outcome.append({"run_id":run,"arm":arm,"active_capture":row.get("capture"),"active_path_evidence":row.get("active_path_evidence"),"valid_gap_observations_after_trigger":row.get("valid_gap_observations_after_trigger"),"outcome_eligible":row.get("outcome_eligible"),"persistence_after_trigger":row.get("persistence_after_trigger"),"clean_after_trigger":row.get("clean_after_trigger"),"measured_scope":"packet/protocol observation only; no physical recovery"})
 write("s13_packets.csv",list(packet[0]) if packet else [],packet); write("s13_events.csv",["run_id","batch_directory","source_file","source_sha256","source_line_ordinal","original_line"],events); write("s13_decisions.csv",sorted({k for r in decision for k in r}),decision); write("s13_receiver_log.csv",list(receiver_log[0]) if receiver_log else [],receiver_log); write("s13_receiver_transitions.csv",list(receiver[0]) if receiver else [],receiver); write("s13_outcomes.csv",list(outcome[0]) if outcome else [],outcome)
 recon={"packet_rows":len(packet),"event_rows":len(events),"decision_rows":len(decision),"receiver_log_rows":len(receiver_log),"receiver_transition_rows":len(receiver),"outcome_rows":len(outcome),"packet_csv_sha256":sha(OUT/"s13_packets.csv"),"packet_xlsx_representation":"CSV companion required: the prior Artifact Tool in-memory 171988-row packet-sheet build exceeded bounded runtime; raw CSV is lossless and hash-listed, not an all-in-one workbook claim."}
 (OUT/"s13_full_detail_reconciliation.json").write_text(json.dumps(recon,indent=2)+"\n")
if __name__=="__main__": main()
