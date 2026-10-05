"""Build a capture-specific lineage sidecar against the ACTUAL ingestion output.

No interval labels and no cross-capture time joins. A message-type/sequence key
is admitted only after verifying uniqueness in this exact hashed PCAP.
"""
import csv, hashlib, json, sys
from pathlib import Path

B=Path(__file__).resolve().parent
APP=B.parents[1]/'01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing'
sys.path.insert(0,str(APP))
from ingest.pcap_ingest import pcap_to_telemetry
from ingest import ptp_wire as wire

def main():
    p=APP/'data/external/timesafe_prod_successful_announce_attack_ptp.pcap'
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    packets={}; t0=None
    for index,(ts,frame) in enumerate(wire.read_pcap(str(p)),1):
        payload=wire.parse_eth_frame(frame)
        if payload is None:continue
        msg=wire.decode_ptp_payload(payload)
        if msg is None:continue
        if t0 is None:t0=ts
        key=(wire.MSG_NAME[msg.msg_type],msg.seq_id)
        assert key not in packets, 'Cannot use nonunique message/sequence identity'
        packets[key]=(index,ts)
    telemetry=pcap_to_telemetry(p)
    seen=set(); rows=[]
    for ordinal,row in enumerate(telemetry.itertuples(index=False),1):
        key=(row.ptp_msg_type,int(row.ptp_seq_id)); index,ts=packets[key]
        assert index not in seen,'Unexpected multiple emissions from one packet'
        assert row.t_s==(ts-t0)/1e9,'Capture time mismatch'
        seen.add(index)
        rows.append([ordinal,digest,index,key[0],key[1],row.t_s])
    missing=sorted(index for index,ts in packets.values() if index not in seen)
    assert len(packets)==13565 and len(rows)==13562 and missing==[1,2,3]
    sidecar=B/'production_telemetry_lineage.csv'
    with sidecar.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['derived_record','pcap_sha256','source_packet_index','message_type','sequence_id','capture_relative_s']);writer.writerows(rows)
    report={'method':'Actual pcap_to_telemetry output matched by capture-hash and verified-unique message-type/sequence key; exact capture-relative time cross-check; no timestamp-only join',
      'pcap_sha256':digest,'decoded_packets':len(packets),'verified_output_records':len(rows),'unemitted_packet_indices':missing,
      'ingester_sha256':hashlib.sha256((APP/'ingest/pcap_ingest.py').read_bytes()).hexdigest(),
      'schema_sha256':hashlib.sha256((APP/'ingest/schema.py').read_bytes()).hexdigest(),
      'derived_csv_sha256':hashlib.sha256(telemetry.to_csv(index=False).encode()).hexdigest(),
      'sidecar_sha256':hashlib.sha256(sidecar.read_bytes()).hexdigest(),
      'scope':'Only this exact PCAP and this regenerated actual output. Does not claim linkage to every historical telemetry export or validate physical timing/labels.'}
    (B/'production_lineage_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
