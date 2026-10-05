"""Bounded final checks and concise handover report for the append-only PCAP workbook."""
import hashlib, json, zipfile
from pathlib import Path

B=Path(__file__).resolve().parent; ROOT=B.parents[1]
BASE=B/'ORAN_All_Current_Datasets_CORRECTED.xlsx'; OUT=B/'ORAN_All_Current_Datasets_FINAL_PCAP.xlsx'
R=B/'FINAL_PCAP_RECONCILIATION.json'; PLAN=B/'detailed_plan.json'
def digest(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest()
r=json.loads(R.read_text()); plan=json.loads(PLAN.read_text())
source_hashes=[]
for d in plan:
 p=ROOT/d['file']; got=digest(p); assert got==d['hash'],d['id']; source_hashes.append(d['id'])
with zipfile.ZipFile(BASE) as a,zipfile.ZipFile(OUT) as b:
 assert b.testzip() is None
 parts=[f'xl/worksheets/sheet{i}.xml' for i in range(1,50)]
 assert all(a.read(x)==b.read(x) for x in parts)
r.update({'final_workbook_sha256':digest(OUT),'source_hashes_rechecked':len(source_hashes),
 'base_49_worksheet_parts_byte_identical':True,
 'original_cell_reconciliation':'45 sources / 523176 rows / 9590610 lexical original cells were fully reconciled in detailed_reconciliation.json; the 49 inherited worksheet XML parts are byte-identical in this final append-only workbook.',
 'targeted_history':{'head':'77a47ccb87a8170f1067f7783b12c9ed742ceb6f','capture_commit':'fb0b60d582710baed897395502c049b74e453689','finding':'Commit adds/renames the production PCAP and related dataset files; it does not supply packet-level label-generation, receiver selection, GNSS, or recovery logs.'},
 'preprint_context':{'local_file':'docs/reference_papers/Groen_TIMESAFE_ACM_ToPS_2025__STUDY-ONLY_preprint.pdf','pages':'5-6, 10-11, 20','finding':'Narrative describes BMCA/Announce fields, testbed context and a feature pipeline. It is an author preprint, not the blocked ACM version of record, and does not bind the local capture to a verified physical outcome.'}})
R.write_text(json.dumps(r,indent=2),encoding='utf-8')
md=f'''# Final PCAP consolidation verification\n\n## Deliverable\n\n`ORAN_All_Current_Datasets_FINAL_PCAP.xlsx` SHA-256: `{r['final_workbook_sha256']}`. It is an append-only copy of the corrected 45-source workbook: 49 inherited worksheets are byte-identical, plus 19 PCAP guide/export sheets (68 total).\n\n## Checks\n\n- Rehashed all 45 source files against `detailed_plan.json`: matched.\n- Preserved 523,176 rows and 9,590,610 original lexical cells: the prior full CSV-to-workbook reconciliation remains applicable because all 49 inherited worksheet XML parts are byte-identical.\n- Rehashed and exported 14 canonical classic-PCAP files. Every record is retained; 267,084 is the largest export, below Excel's 1,048,576-row limit. Non-PTP/unsupported frames remain with explicit parse status.\n- ZIP integrity passed; all 68 sheet names are unique; new sheets contain no formulas or Excel error cells.\n- PCAP index records alias paths. The production capture `0690...20599` contains 13,565 records and five R-PCAP-01 advertised-header-transition rows. Those rows are observable header changes only.\n\n## Context checked, not converted to measurements\n\nTargeted full-history check at HEAD `77a47ccb87a8170f1067f7783b12c9ed742ceb6f` found production-PCAP addition/rename in `fb0b60d582710baed897395502c049b74e453689`; it did not establish label generation, receiver source selection, GNSS/SyncE/oscillator health, or recovery execution. The existing author preprint discusses BMCA/testbeds/features on pp. 5-6, 10-11 and 20. The ACM version of record remains unavailable locally (publisher access was 403), so the preprint is narrative context, not an experiment log.\n\n## Remaining evidence limits\n\nSupplied annotations stay separate from packet-derived observations. The workbook does not claim unauthorized takeover, physical timing degradation, GNSS loss, authenticated receiver selection, or successful recovery. Those claims require the missing receiver/topology/configuration, injection/label-generation, timing-reference and recovery-execution records listed in `PCAP evidence gaps`.\n'''
(B/'FINAL_PCAP_CONSOLIDATION_REPORT.md').write_text(md,encoding='utf-8')
print(json.dumps({'sha256':r['final_workbook_sha256'],'sources':len(source_hashes),'sheets':r['sheet_count']}))
