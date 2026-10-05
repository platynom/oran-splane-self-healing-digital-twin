"""Build an inventory CSV/XLSX for all literature PDFs.

Usage:
    python tools/build_literature_inventory.py
"""

from __future__ import annotations

import csv
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "literature-survey" / "papers"


def inspect_pdf(path: Path) -> dict:
    try:
        doc = fitz.open(path)
        pages = len(doc)
        title = doc.metadata.get("title") or ""
        author = doc.metadata.get("author") or ""
        doc.close()
    except Exception as exc:
        pages = None
        title = ""
        author = ""
        error = str(exc)
    else:
        error = ""

    rel = path.relative_to(ROOT)
    return {
        "folder": path.parent.name,
        "file": path.name,
        "relative_path": str(rel),
        "priority": path.name.startswith("P_") or path.parent.name.lower() == "priority",
        "pages": pages,
        "metadata_title": title,
        "metadata_author": author,
        "error": error,
    }


def main() -> None:
    rows = [inspect_pdf(path) for path in sorted(PAPERS.rglob("*.pdf"))]
    out_csv = ROOT / "literature-survey" / "literature_inventory.csv"
    fieldnames = [
        "folder",
        "file",
        "relative_path",
        "priority",
        "pages",
        "metadata_title",
        "metadata_author",
        "error",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
