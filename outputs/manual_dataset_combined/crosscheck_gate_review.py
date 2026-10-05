"""Review-only reproduction; temporary metadata is not scientific evidence."""
from pathlib import Path
from contextlib import nullcontext
import sys,json,hashlib,tempfile
import pandas as pd
B=Path(__file__).resolve().parent
R=B.parents[1]/'01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing'
sys.path.insert(0,str(R))
import ast
from ingest.schema import coerce_telemetry
from telemetry.features import window_features
# Execute the unchanged loader/gate definitions without importing unrelated ML dependencies.
code=R/'stats/openset_eval.py'
selected={'_source_hashes_match','_has_independent_clock_health_evidence','_load_real_sessions'}
tree=ast.parse(code.read_text(encoding='utf-8'))
ROOT=R
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected],type_ignores=[]),str(code),'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
config=R/'config/default.yaml'; evidence=R/'docs/FAIL_CLOSED_DESIGN.md'
m={'validation_status':'independently_validated','label_semantics':'measured_clock_health','evidence_type':'receiver_measurement','validation_method':'Mechanical test fixture only, not real evidence','reviewer':'Test fixture','review_date':'2026-09-07','source_sha256':{'config/default.yaml':sha(config)},'evidence_artifact':'docs/FAIL_CLOSED_DESIGN.md','evidence_sha256':sha(evidence)}
results={'fixture_notice':'Metadata deliberately describes unrelated documents. No real validation claimed.','unrelated_source_map_passes':_has_independent_clock_health_evidence(m)}
with nullcontext(B/'gate_review_fixture') as td:
 folder=Path(td)
 (folder/'TIMESAFE_SESSION_METADATA.json').write_text(json.dumps(m))
 original=R/'data/external/timesafe_sessions/announce_session_1__announce.csv'
 frame=pd.read_csv(original).head(100).copy()
 frame['label']='healthy'
 # Filename declares attack; explicit source label says healthy.
 frame.to_csv(folder/'announce_session_1__announce.csv',index=False)
 windows=_load_real_sessions(folder,{'dataset':{'window_s':0.4,'step_s':0.2}})
 results.update({'loaded_rows':len(windows),'conflicting_capture_loaded':'announce_session_1' in set(windows.get('capture_id',[])),'input_labels':['healthy'],'output_labels':sorted(set(windows.get('label',[]))),'input_csv_declared_in_manifest':False})
 try:_has_independent_clock_health_evidence([])
 except Exception as ex:results['malformed_metadata_behavior']=type(ex).__name__
 (folder/'TIMESAFE_SESSION_METADATA.json').unlink()
 (folder/'announce_session_1__announce.csv').unlink()
(B/'CROSSCHECK_GATE_REVIEW.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
