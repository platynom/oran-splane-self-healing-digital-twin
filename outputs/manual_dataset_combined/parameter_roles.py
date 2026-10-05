import ast,json
from pathlib import Path
B=Path(__file__).resolve().parent; root=B.parents[1]
m=json.loads((B/'manifest.json').read_text(encoding='utf-8'))
tree=ast.parse((root/'01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/telemetry/features.py').read_text())
env={}
for node in tree.body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id.endswith('FEATURE_COLUMNS'):
        env[node.targets[0].id]=eval(compile(ast.Expression(node.value),'features','eval'),{'__builtins__':{}},env)
active=set(env['FEATURE_COLUMNS']); inactive=set(env['CROSS_SOURCE_FEATURE_COLUMNS'])
rows=[]
for h in dict.fromkeys(h for s in m['sheets'][3:] for h in s['headers'][2:-4]):
    if h in active: role='Active model window feature'
    elif h in inactive: role='Experimental window feature; disabled by default'
    elif h in ['label','Label','attack_family','scenario','attack_flag','fault_flag','is_anomalous']: role='Source label / scenario / annotation'
    elif h in ['telemetry_valid','offset_valid','path_delay_valid','valid_sample_rate','valid_sample_fraction','stale_s']: role='Validity / provenance gate'
    elif h in ['run_id','capture_id','grandmaster_identity','Source','Destination']: role='Identity / grouping; not a direct active model feature'
    elif h in ['action','reason','decision_latency_s','end_to_end_latency_s','within_budget','protective_1of1','protective_2of3']: role='Recorded decision / evaluation output'
    else: role='Source parameter / metadata; not a direct active window feature'
    rows.append([h,role,', '.join(s['name'] for s in m['sheets'][3:] if h in s['headers'])])
name='Parameter roles'; headers=['Parameter','Role in current configuration','Present in sheets']
fn=f'part_{len(m["sheets"]):02}_000.json'
(B/fn).write_text(json.dumps({'name':name,'headers':headers,'rows':rows}),encoding='utf-8')
m['sheets'].append({'name':name,'headers':headers,'parts':[fn],'rows':len(rows),'columns':3})
(B/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print('Active features',len(active),'experimental',len(inactive),'parameters',len(rows))
