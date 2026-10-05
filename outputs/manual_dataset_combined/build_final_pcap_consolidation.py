"""Append reproducible, full-field classic-PCAP exports to the corrected workbook.

This deliberately streams OOXML: loading the 523k-row base workbook in a sheet
library is unnecessary and risks lexical changes.  The base workbook is copied
unchanged; only new worksheets and the workbook manifest are appended.
"""
from __future__ import annotations

import csv, hashlib, json, re, shutil, struct, sys, zipfile
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

B = Path(__file__).resolve().parent
ROOT = B.parents[1]
APP = ROOT / "01_CURRENT_SPlane_SelfHealing" / "oran_splane_selfhealing"
sys.path.insert(0, str(APP))
from ingest.ptp_wire import read_pcap, parse_eth_frame, decode_ptp_payload, MSG_NAME

BASE = B / "ORAN_All_Current_Datasets_CORRECTED.xlsx"
OUT = B / "ORAN_All_Current_Datasets_FINAL_PCAP.xlsx"
AUDIT = B / "source_traceability_audit.json"
PLAN = B / "detailed_plan.json"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELNS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MAX_ROWS = 1_048_576
DECODER = APP / "ingest" / "ptp_wire.py"

PCAP_HEADERS = [
    "Packet ordinal (derived)", "Capture timestamp ns (derived)", "Relative time s (derived)",
    "Frame SHA256 (derived)", "Captured frame length bytes (derived)", "Destination MAC (derived)",
    "Source MAC (derived)", "EtherType (derived)", "PTP parse status (derived)",
    "PTP message type code (derived)", "PTP message type name (derived)",
    "PTP transportSpecific (derived)", "PTP version (derived)", "PTP message length (derived)",
    "PTP domain (derived)", "PTP flags hex (derived)", "PTP correctionField scaled-ns (derived)",
    "PTP correctionField ns (derived)", "PTP sourcePortIdentity (derived)", "PTP source port (derived)",
    "PTP sequenceId (derived)", "PTP controlField (derived)", "PTP logMessageInterval (derived)",
    "PTP originTimestamp ns (derived)", "Announce currentUtcOffset (derived)",
    "Announce grandmasterPriority1 (derived)", "Announce grandmasterClockClass (derived)",
    "Announce grandmasterClockAccuracy (derived)", "Announce offsetScaledLogVariance (derived)",
    "Announce grandmasterPriority2 (derived)", "Announce grandmasterIdentity (derived)",
    "Announce stepsRemoved (derived)", "Announce timeSource (derived)",
    "Observable event/pattern (derived)", "Rule reference (derived)", "Supplied annotation handling (derived)",
    "Conditional action (derived)", "Canonical capture SHA256 (derived)", "Decoder file SHA256 (derived)"
]

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def col(n: int) -> str:
    s=''
    while n: n,k=divmod(n-1,26); s=chr(65+k)+s
    return s

def cell(ref: str, value: object, style='0') -> str:
    value = '' if value is None else str(value)
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value): raise ValueError('XML control char')
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(value)}</t></is></c>'

def row_xml(num: int, values, style='0', height=30) -> str:
    return f'<row r="{num}" ht="{height}" customHeight="1">' + ''.join(cell(f'{col(i)}{num}',v,style) for i,v in enumerate(values,1)) + '</row>'

def mac(b: bytes) -> str: return ':'.join(f'{x:02x}' for x in b)
def ident(b: bytes) -> str: return b.hex() if b else 'NOT_APPLICABLE'
def s8(v: int) -> int: return v-256 if v>127 else v

def unavailable_fields(status, payload=None):
    """Return the 24 decoded-header/message slots after parse status.

    NON_PTP means PTP fields do not apply.  A truncated/invalid PTP-looking
    frame may have some bytes but cannot support a complete decoded message,
    so unknown is deliberately distinct from not-applicable.
    """
    if status == 'NON_PTP_OR_UNSUPPORTED_ETHERNET': return ['NOT_APPLICABLE'] * 24
    if not payload or len(payload) < 34: return ['UNKNOWN_UNAVAILABLE'] * 24
    code=payload[0]&15; scaled=int.from_bytes(payload[8:16],'big',signed=True)
    return [code,MSG_NAME.get(code,'UNKNOWN_UNSUPPORTED'),payload[0]>>4,payload[1]&15,int.from_bytes(payload[2:4],'big'),payload[4],payload[6:8].hex(),scaled,f'{scaled/(1<<16):.9f}',payload[20:28].hex()+payload[28:30].hex(),int.from_bytes(payload[28:30],'big'),int.from_bytes(payload[30:32],'big'),payload[32],s8(payload[33]),'UNKNOWN_UNAVAILABLE']+['UNKNOWN_UNAVAILABLE']*9

def event_for_announce(scope, msg, previous):
    """Compare only like PTP contexts: transport/version/domain/source port."""
    attrs=(msg.grandmaster_priority1,msg.grandmaster_clock_class,msg.grandmaster_clock_accuracy,msg.offset_scaled_log_variance,msg.grandmaster_priority2,msg.steps_removed,msg.time_source)
    current=(ident(msg.grandmaster_identity),attrs)
    before=previous.get(scope); previous[scope]=current
    if before is None or before==current:return 'NONE','NONE'
    if before[0]!=current[0] and before[1]!=current[1]: return 'advertised_GM_identity_and_attribute_change','R-PCAP-01c: GM identity and advertised attributes changed within one PTP context.'
    if before[0]!=current[0]: return 'advertised_GM_identity_change','R-PCAP-01a: advertised grandmasterIdentity changed within one PTP context.'
    return 'advertised_clock_attribute_change','R-PCAP-01b: advertised clock attributes changed with unchanged grandmasterIdentity within one PTP context.'

def pcap_records(path: Path, digest: str):
    first=None; prev={}; count=0; ptp=0; transitions=0
    decoder_sha=sha(DECODER)
    for ordinal,(ts,frame) in enumerate(read_pcap(str(path)),1):
        count += 1; first = ts if first is None else first
        payload=parse_eth_frame(frame)
        base=[ordinal,ts,f'{(ts-first)/1_000_000_000:.9f}',hashlib.sha256(frame).hexdigest(),len(frame),
              mac(frame[:6]) if len(frame)>=6 else 'UNKNOWN_UNAVAILABLE',mac(frame[6:12]) if len(frame)>=12 else 'UNKNOWN_UNAVAILABLE',
              f'0x{int.from_bytes(frame[12:14],"big"):04x}' if len(frame)>=14 else 'UNKNOWN_UNAVAILABLE']
        event='NONE'; rule='NONE'; annotation='NO_LABEL_TRANSFER'; action='No action from this packet alone; validate receiver logs, topology and policy prerequisites first.'
        if digest.startswith('0690ed95'):
            annotation='S026 supplied labels remain only in S026; this full-field export does not transfer them.'
        if payload is None:
            yield base+['NON_PTP_OR_UNSUPPORTED_ETHERNET']+unavailable_fields('NON_PTP_OR_UNSUPPORTED_ETHERNET')+[event,rule,annotation,action,digest,decoder_sha]; continue
        if len(payload)<34:
            yield base+['TRUNCATED_PTP_HEADER']+unavailable_fields('TRUNCATED_PTP_HEADER',payload)+[event,rule,annotation,action,digest,decoder_sha]; continue
        msg=decode_ptp_payload(payload)
        if msg is None:
            yield base+['UNSUPPORTED_OR_INVALID_PTP']+unavailable_fields('UNSUPPORTED_OR_INVALID_PTP',payload)+[event,rule,annotation,action,digest,decoder_sha]; continue
        ptp += 1
        srcid=payload[20:30].hex(); port=int.from_bytes(payload[28:30],'big')
        prefix=['PTP_DECODED',msg.msg_type,MSG_NAME.get(msg.msg_type,'UNKNOWN'),payload[0]>>4,payload[1]&15,
                int.from_bytes(payload[2:4],'big'),payload[4],payload[6:8].hex(),int.from_bytes(payload[8:16],'big',signed=True),
                f'{msg.correction_ns:.9f}',srcid,port,msg.seq_id,payload[32],s8(payload[33]),
                msg.origin_ts_ns if msg.origin_ts_ns is not None else 'UNKNOWN_UNAVAILABLE']
        ann=[msg.current_utc_offset,msg.grandmaster_priority1,msg.grandmaster_clock_class,msg.grandmaster_clock_accuracy,
             msg.offset_scaled_log_variance,msg.grandmaster_priority2,ident(msg.grandmaster_identity),msg.steps_removed,msg.time_source]
        if msg.msg_type != 0xB: ann=['NOT_APPLICABLE']*9
        else:
            scope=(payload[0]>>4,payload[1]&15,payload[4],srcid)
            event,rule=event_for_announce(scope,msg,prev)
            transitions += event != 'NONE'
        yield base+prefix+ann+[event,rule,annotation,action,digest,decoder_sha]
    return count,ptp,transitions

def simple_sheet(title, headers, rows):
    widths=''.join(f'<col min="{i}" max="{i}" width="{min(max(len(h)+4,24),70)}" customWidth="1"/>' for i,h in enumerate(headers,1))
    body=row_xml(1,headers,'5',42)+''.join(row_xml(i,r,'6',90) for i,r in enumerate(rows,2))
    end=f'{col(len(headers))}{len(rows)+1}'
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><dimension ref="A1:{end}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{widths}</cols><sheetData>{body}</sheetData><autoFilter ref="A1:{end}"/></worksheet>'

def pcap_sheet(path, digest):
    rows=[]; n=0
    # Sheet XML is written in streaming form by caller. This generator marker is unused.
    return rows,n

def original_definition(h):
    x=h.lower()
    if h in ('Source','Destination'): return ('Raw versus encoded identifier','S026/S027 raw capture exports store displayed MAC-address text; transformed sources may use an encoded/integer representation. Preserve the exact source-tab lexical value rather than treating representations as interchangeable.','Example: `b8:ce:f6:5e:6b:4a` is a displayed captured sender address.','A change can indicate a different observed flow or encoding, not an authorised role or physical identity.','S026/S027 raw-capture tabs; transformed-source tabs retain their own encoding')
    if h=='MessageType': return ('Raw versus encoded protocol field','Raw capture exports use their supplied message-type representation; derived/session sources may encode the same protocol concept numerically. Preserve the source representation and consult the source tab.','Example: `Announce` is a PTP message name; numeric forms are encoded representations.','A change can describe packet role/order, not receiver selection or maliciousness.','S026/S027 raw-capture tabs and source-specific derived tabs')
    if h in ('Time','t_s','wall_time','window_start_s','window_end_s','Time Interval'): return ('Time','Capture/export time or elapsed/window time; units follow the header (`s` means seconds).','Example: an interval orders records within one source.','Changes order observations; unrelated experiments must not be joined by elapsed time.','Source header; capture-local only')
    if 'offset' in x or 'delay' in x or 'pdv' in x or 'residual' in x: return ('Timing metric','Measured or derived timing value; `_ns` is nanoseconds and `_ppb` is parts per billion.','Example: `offset_ns` is the reported PTP offset.','A change is a recorded metric change, not by itself a physical fault cause.','Source telemetry / derived representation')
    if 'priority' in x or 'clock_class' in x or 'grandmaster' in x or h in ('steps_removed','time_source'): return ('PTP advertised field','PTP Announce or derived PTP property; integer/code unless an identity.','Example: `grandmaster_identity` names an advertised clock.','A change can describe advertised data; it does not prove receiver selection or reference health.','PTP capture/telemetry provenance')
    if 'gnss' in x or 'synce' in x or 'oscillator' in x or h in ('holdover','satellites_tracked'): return ('Reference/health field','Supplied telemetry or simulation/software field; units follow suffix.','Example: `gnss_available` is a supplied state flag.','A change supports only that representation unless external instrument logs corroborate it.','Source-specific telemetry provenance')
    if h.lower() in ('label','attack_flag','fault_flag','is_anomalous','scenario','attack_family'): return ('Supplied annotation/scenario','Source-provided class, flag or scenario text/code.','Example: `Label=0` is an annotation, not confirmed benign state.','Do not convert it to validated packet maliciousness or physical health without label-generation evidence.','Source annotation provenance')
    if h in ('accuracy','precision_macro','recall_macro','f1_macro','roc_auc_h1','confusion_matrix','model'): return ('Model result','Reported model name, metric, or confusion matrix; dimensionless except supplied formatting.','Example: F1 summarizes a labeled evaluation.','It is a reported evaluation, not a freshly validated deployment result.','Model-output source')
    if 'rate' in x or 'fraction' in x or 'score' in x or 'count' in x or h in ('samples','windows'): return ('Derived count/rate','Count, fraction, rate, or software-derived score; units follow suffix/name.','Example: `msg_rate_hz` is messages per second.','A change is descriptive and may be confounded by capture/filtering choices.','Source-specific derived field')
    return ('Source-specific field','Original field retained exactly as supplied; consult its source tab and existing parameter guide.','Example is source-dependent.','Meaning and causal interpretation are not established by the field name alone.','Source header / PARAMETER_BY_PARAMETER_GUIDE.md')

def original_field_rows():
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    groups=defaultdict(list)
    for d in plan:
        for h in d['headers'][:-13]: groups[h].append(d['id'])
    rows=[]
    for h,ids in sorted(groups.items()):
        rep,what,example,change,ref=original_definition(h)
        rows.append([h,rep,', '.join(ids),what,example,change,ref])
    return rows

def pcap_definition(h):
    x=h.lower()
    if h == 'PTP originTimestamp ns (derived)': return ('Decoded PTP message-body timestamp in ns','Timestamp carried in a decodable PTP message body, distinct from the classic-PCAP capture-record timestamp.','Represents protocol content such as a message origin time; it is not the observer capture time.','Compare only with the PTP message type and capture context; it does not prove path delay or clock health.')
    if h == 'Packet ordinal (derived)': return ('Derived 1-based packet count','Sequential record number in this one raw PCAP file; unit: packets.','Packet 1 is the first capture record, irrespective of PTP decode status.','Supports reproducible location in this capture only; not a global packet identifier.')
    if h == 'Captured frame length bytes (derived)': return ('Derived captured length in bytes','Length of the captured frame byte string; unit: bytes.','A larger value means more captured bytes, not necessarily malicious payload.','May be affected by capture truncation and link-layer representation.')
    if h == 'EtherType (derived)': return ('Decoded 16-bit Ethernet EtherType','Hexadecimal field at Ethernet bytes 12-13; `0x88f7` denotes PTP over Ethernet.','Identifies the Ethernet protocol discriminator.','Does not decode VLAN encapsulation or establish message authenticity.')
    if h == 'PTP flags hex (derived)': return ('Decoded 16-bit PTP flagField','Two raw PTP header bytes represented as lowercase hexadecimal; unit: bit field.','Each bit is protocol-defined, not a generic health score.','No individual flag is converted here into a diagnosis without a field-specific rule.')
    if h == 'PTP source port (derived)': return ('Decoded unsigned 16-bit portNumber','The port-number portion of the PTP sourcePortIdentity; unit: integer.','Together with clock identity it scopes a PTP source port.','It is not a UDP/TCP port and does not identify a physical receiver.')
    if 'timestamp' in x or 'relative time' in x: return ('Derived integer ns / decimal seconds','Raw classic-PCAP record time; relative time starts at packet 1 of this capture.','Orders packets in this capture only.','Capture timestamp provenance, not a wall-clock synchronization proof.')
    if 'sha256' in x: return ('Derived hexadecimal SHA-256','Cryptographic digest of a raw frame, capture, or decoder file.','Detects byte changes; it does not authenticate experiment origin.')
    if 'mac' in x or 'sourceportidentity' in x or 'identity' in x: return ('Decoded identifier','Ethernet or PTP header identity represented as lowercase hex.','Identifies an advertised sender/clock context; does not prove device ownership or role.')
    if 'message type' in x or 'sequence' in x or 'domain' in x or 'transport' in x or 'version' in x or 'control' in x or 'logmessage' in x: return ('Decoded PTP header field','Integer/code from the PTP header; log interval is signed base-2 exponent.','Describes packet protocol content, not receiver state.')
    if 'priority' in x or 'clockclass' in x or 'clockaccuracy' in x or 'variance' in x or 'stepsremoved' in x or 'timesource' in x or 'currentutc' in x: return ('Decoded Announce field','Integer/code present only in a decodable Announce message.','A change is an advertised clock-quality/selection input, not verified selection or physical reference health.')
    if 'correction' in x or 'origintimestamp' in x: return ('Decoded timing field','Header timestamp/correction; scaled-ns is raw signed fixed-point, ns is derived conversion.','A value is packet content and cannot alone establish path delay or clock health.')
    if 'parse status' in x: return ('Derived parser state','`PTP_DECODED`, `NON_PTP_OR_UNSUPPORTED_ETHERNET`, `TRUNCATED_PTP_HEADER`, or `UNSUPPORTED_OR_INVALID_PTP`.','NOT_APPLICABLE means no PTP field applies; UNKNOWN_UNAVAILABLE means bytes were insufficient/unsupported.')
    if 'observable' in x or 'rule reference' in x: return ('Derived rule output','R-PCAP-01 compares Announce records only within matching transport/version/domain/sourcePortIdentity context.','It reports advertisement changes only; no diagnosis or action is established.')
    if 'annotation' in x: return ('Provenance guard','States that supplied labels remain in their original source representation.','Prevents silent label transfer to re-exported packets.')
    return ('Derived conditional note','A documented decoder/provenance/action field.','No action or physical outcome is inferred from a packet alone.')

def append_sheets():
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    byhash=defaultdict(list)
    for x in audit['external_inventory']:
        if x.get('suffix')=='.pcap': byhash[x['sha256']].append(x['path'])
    captures=[]
    for digest,paths in sorted(byhash.items()):
        p=ROOT/paths[0]
        if p.exists() and sha(p)==digest: captures.append((digest,p,paths))
    if len(captures)!=14: raise RuntimeError(f'expected 14 available canonical PCAPs, got {len(captures)}')
    base_sha=sha(BASE); dec_sha=sha(DECODER)
    # Read base workbook layout.
    with zipfile.ZipFile(BASE) as zin:
        wb=ET.fromstring(zin.read('xl/workbook.xml')); rel=ET.fromstring(zin.read('xl/_rels/workbook.xml.rels'))
        sheets=wb.find('{%s}sheets'%NS); old=list(sheets); maxid=max(int(x.get('sheetId')) for x in old)
        # The established template uses opaque relationship IDs rather than rIdN.
        # New IDs only need to be unique NCNames and match workbook.xml exactly.
        nextrel=1; oldsheetnums=[int(m.group(1)) for x in rel for m in [re.search(r'worksheets/sheet(\d+)\.xml',x.get('Target',''))] if m]; nextsheet=max(oldsheetnums)+1
        # collect user-facing guide rows first.
        index_rows=[]
        for digest,p,paths in captures:
            path_text=' '.join(paths).lower()
            if digest.startswith('d2c91b3e'):
                origin='External TIMESAFE capture alias set; conflicting derived annotations; QUARANTINED from independent label truth.'
            elif 'netem' in path_text:
                origin='Project software-collected Netem/emulation capture; SOFTWARE_TESTBED, not physical experiment proof.'
            elif 's-plane_security_repo' in path_text or 'timesafe' in path_text:
                origin='Associated external TIMESAFE capture/project copy; exact collection/launch linkage is unavailable locally.'
            else:
                origin='Origin not established from audited local provenance.'
            index_rows.append([f'PCAP {digest[:12]}',digest,p.relative_to(ROOT).as_posix(),len(paths),'; '.join(paths[1:]) or 'None',
                               origin])
        start_rows=[
            ['Purpose','Versioned consolidation: preserves the 45-source corrected workbook and adds canonical full-field raw-PCAP exports.'],
            ['Start here','PCAP index lists canonical captures. PCAP <hash> tabs hold every raw packet record and decoded fields.'],
            ['Original source data','S001–S045 detail tabs are preserved from the corrected workbook; raw lexical cells are unchanged.'],
            ['Labels','Supplied annotations remain in their source tabs. PCAP exports do not propagate labels to packet records.'],
            ['Observable event','R-PCAP-01a/b/c report advertised identity and/or attribute changes only within matching transport/version/domain/sourcePortIdentity context. They are not receiver selection, GNSS health, unauthorized takeover, or recovery proof.'],
            ['Excel limit','No canonical PCAP exceeded Excel’s 1,048,576-row worksheet limit. All tabs use filters and frozen headers.'],
            ['Decoder','ingest/ptp_wire.py SHA256 '+dec_sha+'; unsupported/non-PTP frames are retained with explicit parse status.'],
        ]
        dict_rows=original_field_rows()+[[h,'Derived full-PCAP field','PCAP tabs',*pcap_definition(h)] for h in PCAP_HEADERS]
        rule_rows=[
            ['R-PCAP-01a','Observable advertised_GM_identity_change','Announce headers in one canonical PCAP','grandmasterIdentity changes from the previous Announce in the same transportSpecific/version/domain/sourcePortIdentity context.','Header observation only. It does not establish receiver selection, authorization, GNSS state, timing degradation, or recovery.','Conditional: check authenticated receiver logs, configured profile/topology and policy before action. Not executed/measured in these rows.'],
            ['R-PCAP-01b','Observable advertised_clock_attribute_change','Announce headers in one canonical PCAP','Priority, class, accuracy, variance, priority2, stepsRemoved or timeSource changes while grandmasterIdentity stays the same in the same PTP context.','Header observation only. It does not establish receiver selection, authorization, GNSS state, timing degradation, or recovery.','Conditional: check authenticated receiver logs, configured profile/topology and policy before action. Not executed/measured in these rows.'],
            ['R-PCAP-01c','Observable advertised_GM_identity_and_attribute_change','Announce headers in one canonical PCAP','Both identity and advertised attributes change within the same PTP context.','Header observation only. It does not establish receiver selection, authorization, GNSS state, timing degradation, or recovery.','Conditional: check authenticated receiver logs, configured profile/topology and policy before action. Not executed/measured in these rows.'],
            ['R-PCAP-02','Supplied annotation preservation','S026 / other source tabs','No PCAP-derived label is created. Existing supplied labels remain exactly in their original source representation.','Label-generation evidence remains incomplete where the audit says so.','No automatic action. Review provenance before analytical use.'],
        ]
        gaps=[
            ['Available','Raw packet bytes, capture timestamps, header fields and supplied source annotations are retained with hashes.'],
            ['Decoder coverage','Classic libpcap Ethernet frames are retained. Decoder exports Ethernet and common PTPv2 header fields plus Announce fields. Management, Signaling, peer-delay bodies, TLVs, VLAN headers, packet payload bytes and non-Ethernet link-layer semantics are not expanded into separate columns; raw frame SHA256 and original PCAP remain the evidence.'],
            ['Missing or external','Authenticated receiver selection logs, topology/profile configuration, GNSS/SyncE/oscillator measurements, attack injection/label-generation logs, and measured recovery execution/outcomes for the production capture.'],
            ['Historical linkage','Full upstream history was checked only for targeted evidence; narrative/paper linkage is not converted into a measured packet outcome.'],
        ]
        new=[('PCAP start',['Topic','Detail'],start_rows),('PCAP dictionary',['Field','Representation','Applies to','What / units','Example / meaning','What a change can support','Limits / source'],dict_rows),('PCAP index',['Sheet','Canonical SHA256','Representative path','Alias copies','Additional aliases','Origin and disposition'],index_rows),('PCAP rules',['Rule','Output','Scope','Reproducible condition','Interpretation limit','Conditional action'],rule_rows),('PCAP evidence gaps',['Evidence state','Detail'],gaps)]
        # Copy base then write every old item except modified manifests; materialize new sheets afterward.
        with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as zout:
            for info in zin.infolist():
                if info.filename in ('xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml'): continue
                zout.writestr(info,zin.read(info.filename))
            # fixed guide sheets
            pending=[]
            for name,headers,rows in new:
                pending.append((name,'simple',headers,rows,None,None))
            for digest,p,paths in captures:
                pending.append((f'PCAP {digest[:12]}','pcap',None,None,p,digest,paths))
            # Existing sheet names need remain unique.
            existing={x.get('name') for x in old}
            report=[]
            for entry in pending:
                name,kind,headers,rows,p,digest = entry[:6]
                aliases = entry[6] if len(entry) > 6 else []
                if name in existing: raise RuntimeError('sheet collision '+name)
                sheetid=maxid+1; maxid+=1; rid='rIdPCAP'+str(nextrel); nextrel+=1; sheetno=nextsheet; nextsheet+=1
                ET.SubElement(sheets,'{%s}sheet'%NS,{'name':name,'sheetId':str(sheetid),'{%s}id'%OFFNS:rid})
                ET.SubElement(rel,'{%s}Relationship'%RELNS,{'Id':rid,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet','Target':f'worksheets/sheet{sheetno}.xml'})
                if kind=='simple': zout.writestr(f'xl/worksheets/sheet{sheetno}.xml',simple_sheet(name,headers,rows)); report.append({'sheet':name,'kind':'guide','rows':len(rows)})
                else:
                    # streaming XML to avoid workbook-scale memory use
                    endcol=col(len(PCAP_HEADERS)); count=0; ptp=0; transition=0; first=None; prev={}
                    with zout.open(f'xl/worksheets/sheet{sheetno}.xml','w') as dest:
                        widths=''.join(f'<col min="{i}" max="{i}" width="{70 if i in (4,34,35,36,37,38,39) else 42}" customWidth="1"/>' for i in range(1,len(PCAP_HEADERS)+1))
                        dest.write(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{widths}</cols><sheetData>{row_xml(1,PCAP_HEADERS,"5",42)}'.encode())
                        for values in pcap_records(p,digest):
                            count+=1; ptp += values[8]=='PTP_DECODED'; transition += values[33]=='advertised_GM_transition'
                            dest.write(row_xml(count+1,values).encode())
                        end=f'{endcol}{count+1}'
                        dest.write(f'</sheetData><autoFilter ref="A1:{end}"/></worksheet>'.encode())
                    report.append({'sheet':name,'sheet_part':f'xl/worksheets/sheet{sheetno}.xml','kind':'pcap','canonical_sha256':digest,'representative_path':p.relative_to(ROOT).as_posix(),'alias_paths':aliases,'packets':count,'ptp_decoded':ptp,'advertised_transition_rows':transition})
            # serialise manifests after all sheet changes
            ET.register_namespace('',NS); ET.register_namespace('r',OFFNS)
            zout.writestr('xl/workbook.xml',ET.tostring(wb,encoding='utf-8',xml_declaration=True))
            ET.register_namespace('',RELNS); zout.writestr('xl/_rels/workbook.xml.rels',ET.tostring(rel,encoding='utf-8',xml_declaration=True))
            ctype=ET.fromstring(zin.read('[Content_Types].xml')); cns='http://schemas.openxmlformats.org/package/2006/content-types'
            for n in range(max(oldsheetnums)+1,nextsheet): ET.SubElement(ctype,'{%s}Override'%cns,{'PartName':f'/xl/worksheets/sheet{n}.xml','ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'})
            ET.register_namespace('',cns); zout.writestr('[Content_Types].xml',ET.tostring(ctype,encoding='utf-8',xml_declaration=True))
    return {'base_workbook_sha256':base_sha,'decoder_sha256':dec_sha,'canonical_pcaps':len(captures),'appended_sheets':len(pending),'pcap_exports':report,'final_workbook_sha256':sha(OUT)}

def verify(report):
    # ZIP integrity, sheet bounds/headers, source hashes, all original source lexical cells inherited from the already reconciled base.
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        wb=ET.fromstring(z.read('xl/workbook.xml')); names=[x.get('name') for x in wb.find('{%s}sheets'%NS)]
        assert len(names)==49+report['appended_sheets'] and len(names)==len(set(names))
        full_width_checks=[]
        for item in report['pcap_exports']:
            if item['kind']!='pcap': continue
            assert item['packets'] <= MAX_ROWS-1
            assert item['packets']>0
            rows=0
            for event,node in ET.iterparse(z.open(item['sheet_part']),events=('end',)):
                if node.tag!='{'+NS+'}row': continue
                vals=[]
                for c in node:
                    assert c.find('{'+NS+'}f') is None
                    assert c.get('t')!='e'
                    vals.append(''.join(c.itertext()) if c.get('t')=='inlineStr' else c.findtext('{'+NS+'}v',''))
                if rows==0: assert vals==PCAP_HEADERS
                else:
                    assert len(vals)==len(PCAP_HEADERS),(item['sheet'],rows+1,len(vals))
                    assert vals[37]==item['canonical_sha256'],(item['sheet'],rows+1,'canonical provenance position')
                    assert vals[38]==report['decoder_sha256'],(item['sheet'],rows+1,'decoder provenance position')
                rows+=1; node.clear()
            assert rows-1==item['packets']
            full_width_checks.append({'sheet':item['sheet'],'every_row_width':len(PCAP_HEADERS),'header_exact':True,'canonical_sha256_column':38,'decoder_sha256_column':39,'rows_checked':rows-1})
    report['zip_integrity']=True; report['sheet_count']=49+report['appended_sheets']; report['formula_errors_in_new_sheets']=0; report['full_pcap_row_width_and_provenance_checks']=full_width_checks
    report['base_detail_reconciliation_reused']='detailed_reconciliation.json: 45 sources, 523176 rows, 9590610 original lexical cells verified before this append-only operation.'
    (B/'FINAL_PCAP_RECONCILIATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    r=verify(append_sheets()); print(json.dumps({'workbook':str(OUT),'sha256':r['final_workbook_sha256'],'sheets':r['sheet_count'],'pcaps':r['canonical_pcaps']},indent=2))
