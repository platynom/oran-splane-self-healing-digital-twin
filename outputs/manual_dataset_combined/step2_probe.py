import csv, json, hashlib, itertools
from pathlib import Path
from collections import Counter

R = Path(__file__).resolve().parents[2]
D = R / 'dataset' / 'timesafe'
U = D / 's-plane_security_repo'

FILES = {
 'raw_A':  U / 'DataCollectionPTP' / '15min_announce_attack.csv',
 'raw_B':  U / 'DataCollectionPTP' / '2024-10-06-announce_attack_UEdata.csv',
 'lab_1':  D / 'timesafe_multi_raw' / 'announce_session_1_labels.csv',
 'lab_2':  D / 'timesafe_multi_raw' / 'announce_session_2_labels.csv',
 'pcap_1': D / 'timesafe_multi_raw' / 'announce_session_1.pcap',
 'pcap_2': D / 'timesafe_multi_raw' / 'announce_session_2.pcap',
 'pcap_A': U / 'DataCollectionPTP' / '15min_announce_attack.pcap',
 'pcap_B': U / 'DataCollectionPTP' / '2024-10-06-announce_attack_UEdata.pcap',
}

out = {'file_facts': {}, 'checks': {}}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

for k, p in FILES.items():
    out['file_facts'][k] = {
        'path': str(p),
        'exists': p.exists(),
        'bytes': p.stat().st_size if p.exists() else None,
        'sha256': sha(p) if p.exists() else None,
    }

def read(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

# CHECK 1 -- are the two raw CSVs the same capture?
if FILES['raw_A'].exists() and FILES['raw_B'].exists():
    A, B = read(FILES['raw_A']), read(FILES['raw_B'])
    out['checks']['raw_rowcounts'] = [len(A), len(B)]
    out['checks']['raw_headers'] = [list(A[0].keys()), list(B[0].keys())]
    pa = [r for r in A if 'ptp' in r.get('Protocol', '').lower()]
    pb = [r for r in B if 'ptp' in r.get('Protocol', '').lower()]
    out['checks']['raw_ptp_rowcounts'] = [len(pa), len(pb)]
    cols = ['Time', 'Source', 'Destination', 'Length', 'SequenceID', 'MessageType']
    diff = Counter()
    for x, y in itertools.islice(zip(pa, pb), 10**9):
        for c in cols:
            if x.get(c) != y.get(c):
                diff[c] += 1
    out['checks']['raw_ptp_field_diff_counts'] = dict(diff)
    out['checks']['raw_A_first3'] = pa[:3]
    out['checks']['raw_B_first3'] = pb[:3]
    out['checks']['raw_A_sources'] = dict(Counter(r['Source'] for r in pa))
    out['checks']['raw_B_sources'] = dict(Counter(r['Source'] for r in pb))
    out['checks']['raw_A_src_msgtype'] = {f"{s}|{m}": n for (s, m), n in
        Counter((r['Source'], r['MessageType']) for r in pa).items()}
    out['checks']['raw_B_src_msgtype'] = {f"{s}|{m}": n for (s, m), n in
        Counter((r['Source'], r['MessageType']) for r in pb).items()}
    out['checks']['raw_A_timespan'] = [pa[0]['Time'], pa[-1]['Time']]
    out['checks']['raw_B_timespan'] = [pb[0]['Time'], pb[-1]['Time']]

# CHECK 2 -- the two label files
L1, L2 = read(FILES['lab_1']), read(FILES['lab_2'])
out['checks']['label_rowcounts'] = [len(L1), len(L2)]
out['checks']['label_counts_1'] = dict(Counter(r['Label'] for r in L1))
out['checks']['label_counts_2'] = dict(Counter(r['Label'] for r in L2))
nonlabel = [c for c in L1[0] if c != 'Label']
out['checks']['nonlabel_identical_rows'] = sum(
    all(x[c] == y[c] for c in nonlabel) for x, y in zip(L1, L2))
out['checks']['conflicting_label_rows'] = sum(
    x['Label'] != y['Label'] for x, y in zip(L1, L2))
out['checks']['conflict_direction'] = dict(Counter(
    f"{x['Label']}->{y['Label']}" for x, y in zip(L1, L2) if x['Label'] != y['Label']))

# CHECK 3 -- can ONE (Source,MessageType) rule reproduce either label set exactly?
def rule_scan(L):
    keys = sorted({(r['Source'], r['MessageType']) for r in L})
    res = {}
    for k in keys:
        pos = sum(1 for r in L if (r['Source'], r['MessageType']) == k)
        agree = sum(1 for r in L
                    if (r['Label'] == '1') == ((r['Source'], r['MessageType']) == k))
        res[f"{k[0]}|{k[1]}"] = {'rule_matches': pos, 'rows_agreeing': agree,
                                 'exact': agree == len(L)}
    return res
out['checks']['rule_scan_labels1'] = rule_scan(L1)
out['checks']['rule_scan_labels2'] = rule_scan(L2)

# CHECK 4 -- positives described by reconstructed time
def pos_profile(L):
    t = 0.0; times = []
    for r in L:
        t += float(r['Time Interval'])
        if r['Label'] == '1':
            times.append(t)
    return {'n_pos': len(times),
            'first': times[0] if times else None,
            'last': times[-1] if times else None,
            'total_span': t,
            'pos_by_src_type': {f"{r['Source']}|{r['MessageType']}": n
                for (r, n) in []} }
out['checks']['pos_time_1'] = pos_profile(L1)
out['checks']['pos_time_2'] = pos_profile(L2)
out['checks']['pos_src_type_1'] = {f"{s}|{m}": n for (s, m), n in
    Counter((r['Source'], r['MessageType']) for r in L1 if r['Label'] == '1').items()}
out['checks']['pos_src_type_2'] = {f"{s}|{m}": n for (s, m), n in
    Counter((r['Source'], r['MessageType']) for r in L2 if r['Label'] == '1').items()}

p = Path(__file__).parent / 'step2_probe.json'
p.write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2)[:4000])
print('WROTE', p)
