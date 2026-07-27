"""Render PDFs into visual review sheets and extract page text.

Usage:
    python tools/render_pdf_review.py literature-survey/papers/priority
"""

from __future__ import annotations

import argparse
import json
import re
from math import ceil
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def render_pdf(pdf: Path, visual_root: Path, thumb_scale: float, sheet_scale: float) -> dict:
    doc = fitz.open(pdf)
    out_dir = visual_root / pdf.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    title_font = load_font(18)
    small_font = load_font(14)
    text_pages: list[str] = []
    page_infos: list[dict] = []
    captions: list[dict] = []
    headings: list[dict] = []
    grouped_thumbs: list[Image.Image] = []
    all_thumbs: list[Image.Image] = []

    for page_no, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        text_pages.append(f"--- PAGE {page_no} ---\n{text}\n")

        for match in re.finditer(
            r"(?i)\b(fig(?:ure)?\.?\s*\d+[^\n]{0,220}|table\s*\d+[^\n]{0,220})",
            text,
        ):
            captions.append(
                {"page": page_no, "caption": re.sub(r"\s+", " ", match.group(1)).strip()[:260]}
            )

        for line in text.splitlines():
            heading = line.strip()
            if 3 <= len(heading) <= 90 and (
                re.match(r"^(\d+\.?\s+|[IVX]+\.?\s+|[A-Z][A-Z\- /]{5,})", heading)
                or re.match(r"^[A-Z][A-Za-z0-9\- /:]{5,}$", heading)
            ):
                if not re.search(r"@|http|doi|ISBN", heading, re.I):
                    headings.append({"page": page_no, "heading": heading})

        page_infos.append(
            {
                "page": page_no,
                "chars": len(text),
                "images": len(page.get_images(full=True)),
                "drawings": len(page.get_drawings()),
                "links": len(page.get_links()),
                "text_start": re.sub(r"\s+", " ", text).strip()[:500],
            }
        )

        for scale, store, header_height, font in [
            (thumb_scale, grouped_thumbs, 32, title_font),
            (sheet_scale, all_thumbs, 24, small_font),
        ]:
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            canvas = Image.new("RGB", (img.width, img.height + header_height), "white")
            canvas.paste(img, (0, header_height))
            draw = ImageDraw.Draw(canvas)
            draw.rectangle([0, 0, img.width, header_height - 1], fill=(20, 20, 20))
            draw.text((8, 5), f"Page {page_no}", fill="white", font=font)
            store.append(canvas)

    save_grouped_sheets(grouped_thumbs, out_dir, per_sheet=6, cols=2)
    save_all_pages_sheet(all_thumbs, out_dir)

    (out_dir / "page_text.txt").write_text("\n".join(text_pages), encoding="utf-8")
    meta = {
        "file": pdf.name,
        "pages": len(doc),
        "page_infos": page_infos,
        "captions": captions[:120],
        "headings": headings[:160],
        "visual_sheets": [p.name for p in sorted(out_dir.glob("sheet_*.png"))],
        "all_pages_contact_sheet": "ALL_PAGES_CONTACT_SHEET.png",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    doc.close()
    return meta


def save_grouped_sheets(images: list[Image.Image], out_dir: Path, per_sheet: int, cols: int) -> None:
    for start in range(0, len(images), per_sheet):
        batch = images[start : start + per_sheet]
        width = max(img.width for img in batch)
        height = max(img.height for img in batch)
        rows = ceil(len(batch) / cols)
        sheet = Image.new("RGB", (cols * width, rows * height), (235, 235, 235))
        for idx, img in enumerate(batch):
            sheet.paste(img, ((idx % cols) * width, (idx // cols) * height))
        sheet.save(out_dir / f"sheet_{start // per_sheet + 1:02d}_pages_{start + 1:03d}-{start + len(batch):03d}.png")


def save_all_pages_sheet(images: list[Image.Image], out_dir: Path) -> None:
    cols = 4 if len(images) > 8 else 2
    width = max(img.width for img in images)
    height = max(img.height for img in images)
    rows = ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * width, rows * height), (230, 230, 230))
    for idx, img in enumerate(images):
        sheet.paste(img, ((idx % cols) * width, (idx // cols) * height))
    sheet.save(out_dir / "ALL_PAGES_CONTACT_SHEET.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_folder", type=Path)
    parser.add_argument("--pattern", default="*.pdf")
    parser.add_argument("--visual-root", type=Path)
    parser.add_argument("--thumb-scale", type=float, default=0.45)
    parser.add_argument("--sheet-scale", type=float, default=0.25)
    args = parser.parse_args()

    pdf_folder = args.pdf_folder.resolve()
    visual_root = args.visual_root or (pdf_folder / "_visual_review")
    visual_root.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_folder.glob(args.pattern))
    all_meta = []
    for index, pdf in enumerate(pdfs, start=1):
        print(f"[{index}/{len(pdfs)}] Rendering {pdf.name}")
        all_meta.append(render_pdf(pdf, visual_root, args.thumb_scale, args.sheet_scale))
    (visual_root / "all_meta.json").write_text(json.dumps(all_meta, indent=2), encoding="utf-8")
    print(f"Rendered {len(all_meta)} PDFs into {visual_root}")


if __name__ == "__main__":
    main()
