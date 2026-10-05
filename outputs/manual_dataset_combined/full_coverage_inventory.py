"""Repository-wide software read coverage. Resumable: append-only JSONL, skips completed paths.

Every file is opened and parsed, or recorded as unreadable with the reason.
.pth files are NEVER unpickled - only their ZIP central directory is read.
.py files are NEVER executed - only parsed with ast.
"""
from __future__ import annotations
import ast, csv, hashlib, json, os, struct, sys, time, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "manual_dataset_combined" / "coverage"
OUT.mkdir(exist_ok=True)
JSONL = OUT / "full_coverage_inventory.jsonl"
ROOTS = ["dataset", "02_PREVIOUS_Work",
         "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data", "outputs"]
HASH_ROOTS = {"dataset", "02_PREVIOUS_Work",
              "01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/data"}
BUDGET_S = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def parse_csv(p: Path) -> dict:
    delim = ","
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        head = f.readline()
        if head.count("\t") > head.count(","):
            delim = "\t"
        f.seek(0)
        rd = csv.reader(f, delimiter=delim)
        try:
            hdr = next(rd)
        except StopIteration:
            return {"rows": 0, "columns": 0, "header": [], "delimiter": delim, "ragged_rows": 0}
        n = len(hdr); rows = 0; ragged = 0
        for row in rd:
            rows += 1
            if len(row) != n:
                ragged += 1
    return {"rows": rows, "columns": n, "header": hdr[:40], "delimiter": delim,
            "ragged_rows": ragged, "all_rows_match_header": ragged == 0}


def parse_pcap(p: Path) -> dict:
    with p.open("rb") as f:
        gh = f.read(24)
        if len(gh) < 24:
            return {"parsed": False, "reason": "shorter than a pcap global header"}
        magic = struct.unpack("<I", gh[:4])[0]
        if magic == 0x0A0D0D0A:
            return {"parsed": False, "format": "pcapng", "reason": "UNPARSED_FORMAT: reader handles classic pcap only"}
        if magic not in (0xA1B2C3D4, 0xD4C3B2A1, 0xA1B23C4D, 0x4D3CB2A1):
            return {"parsed": False, "reason": f"unrecognised magic {hex(magic)}"}
        end = "<" if magic in (0xA1B2C3D4, 0xA1B23C4D) else ">"
        nano = magic in (0xA1B23C4D, 0x4D3CB2A1)
        link = struct.unpack(end + "I", gh[20:24])[0]
        total = ptp = 0; srcs = set(); mtypes = {}; first = last = None
        while True:
            h = f.read(16)
            if len(h) < 16:
                break
            ts, sub, incl, _o = struct.unpack(end + "IIII", h)
            d = f.read(incl)
            if len(d) < incl:
                break
            total += 1
            t = ts + sub / (1e9 if nano else 1e6)
            if first is None:
                first = t
            last = t
            if len(d) >= 14 and d[12:14] == b"\x88\xf7":
                ptp += 1
                srcs.add(":".join(f"{b:02x}" for b in d[6:12]))
                mt = d[14] & 0x0F if len(d) > 14 else None
                mtypes[mt] = mtypes.get(mt, 0) + 1
    return {"parsed": True, "endianness": "little" if end == "<" else "big",
            "timestamp_resolution": "nanosecond" if nano else "microsecond",
            "link_type": link, "records": total, "ptp_records": ptp,
            "distinct_source_macs": sorted(srcs)[:20], "distinct_source_mac_count": len(srcs),
            "ptp_message_types": {str(k): v for k, v in sorted(mtypes.items(), key=lambda x: str(x[0]))},
            "first_epoch_s": first, "last_epoch_s": last}


def parse_pth(p: Path) -> dict:
    if not zipfile.is_zipfile(p):
        return {"torch_zip_archive": False, "NOT_DEPICKLED": True,
                "note": "legacy non-zip torch format; header not interpreted, file never unpickled"}
    with zipfile.ZipFile(p) as z:
        infos = z.infolist()
    interesting = [i.filename for i in infos
                   if any(k in i.filename.lower() for k in ("data.pkl", "constants", "version", "config"))]
    return {"torch_zip_archive": True, "NOT_DEPICKLED": True, "entry_count": len(infos),
            "entries_sample": [{"name": i.filename, "size": i.file_size} for i in infos[:15]],
            "notable_entries": interesting[:10],
            "total_uncompressed_bytes": sum(i.file_size for i in infos)}


def parse_py(p: Path) -> dict:
    src = p.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"parsed": False, "reason": f"SyntaxError: {e}", "lines": src.count("\n") + 1}
    imports, defs = set(), []
    for n in tree.body:
        if isinstance(n, ast.Import):
            imports.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.append(n.name)
    return {"parsed": True, "lines": src.count("\n") + 1, "NEVER_EXECUTED": True,
            "module_level_imports": sorted(imports), "top_level_defs": defs[:40]}


def parse_json(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return {"parsed": False, "reason": f"{type(e).__name__}: {e}"}
    if isinstance(d, dict):
        return {"parsed": True, "kind": "object", "top_level_keys": list(d)[:40]}
    if isinstance(d, list):
        return {"parsed": True, "kind": "array", "element_count": len(d)}
    return {"parsed": True, "kind": type(d).__name__}


def classify(p: Path, rel: str, do_hash: bool) -> dict:
    ext = p.suffix.lower()
    rec = {"path": rel, "extension": ext or "(none)"}
    try:
        st = p.stat(); rec["size_bytes"] = st.st_size
        rec["sha256"] = sha256(p) if do_hash else "NOT_HASHED_GENERATED_OUTPUT_ROOT"
        if ext in (".csv", ".tsv"):
            rec["type"] = "tabular"; rec["parse"] = parse_csv(p)
        elif ext in (".pcap", ".pcapng"):
            rec["type"] = "capture"; rec["parse"] = parse_pcap(p)
        elif ext == ".json":
            rec["type"] = "json"; rec["parse"] = parse_json(p)
        elif ext == ".pth":
            rec["type"] = "model_checkpoint"; rec["parse"] = parse_pth(p)
        elif ext == ".py":
            rec["type"] = "python_source"; rec["parse"] = parse_py(p)
        else:
            rec["type"] = "OPAQUE"; rec["parse"] = {"parsed": False, "reason": "binary or unhandled type; size and hash only"}
    except Exception as e:
        rec["type"] = "UNREADABLE"; rec["parse"] = {"parsed": False, "reason": f"{type(e).__name__}: {e}"}
    return rec


def main() -> None:
    done = set()
    if JSONL.exists():
        for line in JSONL.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    done.add(json.loads(line)["path"])
                except Exception:
                    pass
    todo = []
    skipped_dirs: list = []
    for r in ROOTS:
        base = ROOT / r
        if not base.exists():
            continue
        walk_errors = []
        for dirpath, dirnames, filenames in os.walk(base, onerror=walk_errors.append):
            dirnames[:] = sorted(d for d in dirnames
                                 if not os.path.islink(os.path.join(dirpath, d)))
            for fn in sorted(filenames):
                fp = Path(dirpath) / fn
                if fp.is_symlink():
                    continue
                rel = str(fp.relative_to(ROOT)).replace("\\", "/")
                if rel not in done:
                    todo.append((fp, rel, r in HASH_ROOTS))
        for we in walk_errors:
            rel = str(getattr(we, "filename", "unknown")).replace("\\", "/")
            if rel not in done:
                skipped_dirs.append({"path": rel, "type": "UNREADABLE_DIRECTORY",
                                     "parse": {"parsed": False,
                                               "reason": f"{type(we).__name__}: {we}"}})
    started = time.monotonic(); n = 0
    with JSONL.open("a", encoding="utf-8") as out:
        for sd in skipped_dirs:
            out.write(json.dumps(sd) + "\n")
        for p, rel, dh in todo:
            out.write(json.dumps(classify(p, rel, dh)) + "\n"); n += 1
            if n % 25 == 0:
                out.flush()
                if time.monotonic() - started > BUDGET_S:
                    break
    print(json.dumps({"processed_this_call": n, "already_done": len(done),
                      "remaining": max(0, len(todo) - n)}))


if __name__ == "__main__":
    main()
