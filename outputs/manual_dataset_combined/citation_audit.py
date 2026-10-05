import hashlib
import json
import re
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def resolve_anchor(fpath, anchor):
    if not anchor:
        return True
    p = Path(fpath)
    if not p.exists():
        return False
    if fpath.endswith('.json'):
        try:
            cur = json.loads(p.read_text(encoding='utf-8'))
            parts = anchor.split('.')
            for part in parts:
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                    cur = cur[int(part)]
                else:
                    return False
            return True
        except Exception:
            return False
    elif fpath.endswith('.md'):
        try:
            text = p.read_text(encoding='utf-8')
            if anchor in text:
                return True
            headings = re.findall(r'^#+\s+(.+)$', text, re.M)
            slugs = set()
            for h in headings:
                slugs.add(re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-'))
                slugs.add(re.sub(r'[^a-z0-9 -]+', '', h.lower()).replace(' ', '-'))
            norm_anchor = re.sub(r'[^a-z0-9]+', '-', anchor.lower()).strip('-')
            norm_anchor_gfm = re.sub(r'[^a-z0-9 -]+', '', anchor.lower()).replace(' ', '-')
            return (norm_anchor in slugs) or (norm_anchor_gfm in slugs)
        except Exception:
            return False
    return True

def run_citation_audit():
    root = Path(__file__).resolve().parent
    repo_root = root.parents[1]
    reg_path = root / 'ACCEPTANCE_REGISTER.md'

    content = reg_path.read_text(encoding='utf-8')

    table_rows = re.findall(r'\|\s*([0-9a-z]+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*`([^`]+)`', content)

    audit_records = []
    broken_citations = []

    for crit_num, name, status, ref in table_rows:
        name_str = name.strip()
        status_str = status.strip()
        ref_str = ref.strip()

        if '#' in ref_str:
            file_part, anchor_part = ref_str.split('#', 1)
        else:
            file_part, anchor_part = ref_str, None

        # Resolve path relative to repo root if not absolute
        file_path_obj = repo_root / file_part
        file_exists = file_path_obj.exists()
        file_size_bytes = file_path_obj.stat().st_size if file_exists else 0
        file_sha256 = compute_sha256(file_path_obj) if file_exists else None

        anchor_resolves = resolve_anchor(str(file_path_obj), anchor_part) if file_exists else False

        is_broken = (not file_exists) or (not anchor_resolves)

        rec = {
            "criterion_number": crit_num,
            "criterion_name": name_str,
            "recorded_status": status_str,
            "reference": ref_str,
            "path": file_part,
            "anchor": anchor_part,
            "file_exists": file_exists,
            "file_size_bytes": file_size_bytes,
            "file_sha256": file_sha256,
            "anchor_resolves": anchor_resolves,
            "is_broken_citation": is_broken
        }
        audit_records.append(rec)
        if is_broken:
            broken_citations.append(crit_num)

    output = {
        "summary": {
            "total_citations": len(audit_records),
            "broken_citation_count": len(broken_citations),
            "broken_criteria": broken_citations
        },
        "citations": audit_records
    }

    out_json = root / 'citation_audit.json'
    out_json.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(f"Wrote citation audit to {out_json}")

if __name__ == '__main__':
    run_citation_audit()
