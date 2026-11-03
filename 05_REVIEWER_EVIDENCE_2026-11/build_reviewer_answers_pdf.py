#!/usr/bin/env python3
"""Render REVIEWER_ANSWERS_2026-11.md as a readable, source-preserving PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "REVIEWER_ANSWERS_2026-11.md"
OUTPUT = ROOT / "REVIEWER_ANSWERS_2026-11.pdf"

NAVY = colors.HexColor("#142A43")
TEAL = colors.HexColor("#0F8B8D")
CYAN = colors.HexColor("#1A6F8D")
SLATE = colors.HexColor("#42566E")
LIGHT = colors.HexColor("#EAF2F5")
RULE = colors.HexColor("#B8C8D2")


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        (Path(r"C:\Windows\Fonts\aptos.ttf"), Path(r"C:\Windows\Fonts\aptosbd.ttf"), Path(r"C:\Windows\Fonts\consola.ttf")),
        (Path(r"C:\Windows\Fonts\calibri.ttf"), Path(r"C:\Windows\Fonts\calibrib.ttf"), Path(r"C:\Windows\Fonts\consola.ttf")),
    ]
    for regular, bold, mono in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("BodyFont", str(regular)))
            pdfmetrics.registerFont(TTFont("BodyFont-Bold", str(bold)))
            if mono.exists():
                pdfmetrics.registerFont(TTFont("MonoFont", str(mono)))
            else:
                return "BodyFont", "BodyFont-Bold", "Courier"
            return "BodyFont", "BodyFont-Bold", "MonoFont"
    return "Helvetica", "Helvetica-Bold", "Courier"


BODY_FONT, BOLD_FONT, MONO_FONT = register_fonts()


def inline_markdown(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(r"`([^`]+)`", rf'<font name="{MONO_FONT}" color="#244A62">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", rf'<font name="{BOLD_FONT}">\1</font>', escaped)
    escaped = escaped.replace("  ", " ")
    return escaped


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName=BOLD_FONT,
            fontSize=25,
            leading=30,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=10 * mm,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.3,
            leading=13,
            textColor=SLATE,
            backColor=LIGHT,
            borderColor=RULE,
            borderWidth=0.6,
            borderPadding=8,
            spaceAfter=3 * mm,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=BOLD_FONT,
            fontSize=15.5,
            leading=19,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.5,
            leading=13.2,
            textColor=colors.HexColor("#263748"),
            spaceAfter=2.8 * mm,
            allowWidows=0,
            allowOrphans=0,
        ),
        "evidence": ParagraphStyle(
            "Evidence",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=8.6,
            leading=12,
            textColor=colors.HexColor("#194D5B"),
            leftIndent=4 * mm,
            borderColor=TEAL,
            borderWidth=0,
            borderLeft=2,
            borderPadding=5,
            backColor=colors.HexColor("#F1FAF8"),
            spaceAfter=2.5 * mm,
        ),
        "limits": ParagraphStyle(
            "Limits",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=8.6,
            leading=12,
            textColor=colors.HexColor("#5A4850"),
            leftIndent=4 * mm,
            borderColor=colors.HexColor("#B57645"),
            borderWidth=0,
            borderLeft=2,
            borderPadding=5,
            backColor=colors.HexColor("#FFF8F2"),
            spaceAfter=3.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.1,
            leading=12.5,
            textColor=colors.HexColor("#263748"),
            leftIndent=6 * mm,
            firstLineIndent=-3 * mm,
            bulletIndent=2 * mm,
            spaceAfter=1.5 * mm,
        ),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 5 * mm, width, 5 * mm, fill=1, stroke=0)
    canvas.setFont(BODY_FONT, 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(18 * mm, 10 * mm, "O-RAN S-plane reviewer evidence · 2026-11-03")
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.4)
    canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
    canvas.restoreState()


def parse_markdown(text: str, styles) -> list:
    story: list = []
    lines = text.splitlines()
    paragraph: list[str] = []
    meta_mode = True

    def flush() -> None:
        nonlocal paragraph, meta_mode
        if not paragraph:
            return
        raw = " ".join(line.strip() for line in paragraph).strip()
        if raw:
            if raw.startswith("**Evidence:**"):
                style = styles["evidence"]
            elif raw.startswith("**Limits:**"):
                style = styles["limits"]
            elif meta_mode:
                style = styles["meta"]
            else:
                style = styles["body"]
            story.append(Paragraph(inline_markdown(raw), style))
        paragraph = []

    for line in lines:
        if line.startswith("# "):
            flush()
            story.append(Spacer(1, 10 * mm))
            story.append(Paragraph(inline_markdown(line[2:]), styles["title"]))
            story.append(HRFlowable(width="100%", thickness=1.2, color=TEAL, spaceAfter=6 * mm))
        elif line.startswith("## "):
            flush()
            meta_mode = False
            story.append(CondPageBreak(65 * mm))
            # A blank Paragraph is retained at a page boundary, unlike Spacer,
            # so headings never collide with the top brand bar after a conditional break.
            story.append(Paragraph("&nbsp;", styles["body"]))
            story.append(Paragraph(inline_markdown(line[3:]), styles["h2"]))
        elif line.startswith("- "):
            flush()
            meta_mode = False
            story.append(Paragraph(inline_markdown(line[2:]), styles["bullet"], bulletText="•"))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.rstrip("  "))
    flush()
    return story


def main() -> None:
    styles = build_styles()
    text = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title="Reviewer answers: O-RAN S-plane timing security",
        author="Project evidence audit",
        subject="Evidence-backed answers to 16 reviewer questions",
    )
    story = parse_markdown(text, styles)
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=CYAN))
    story.append(Paragraph("End of audited answer sheet", styles["meta"]))
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
