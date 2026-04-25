"""
Sinh bao cao Word - Muc III: Ket qua So sanh va Trich dan.

Su dung:
    python scripts/generate_word_report.py
    python scripts/generate_word_report.py --doc-id Hop_dong_A --old v1 --new v2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor
from docx.enum.style import WD_STYLE_TYPE

from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.report import ReportGenerator


# Mau sac
COLOR_THEM  = RGBColor(0x27, 0x96, 0x27)   # Xanh la — THEM
COLOR_XOA   = RGBColor(0xCC, 0x00, 0x00)   # Do      — XOA
COLOR_SUA   = RGBColor(0xE6, 0x80, 0x00)   # Cam     — SUA
COLOR_RAW   = RGBColor(0x55, 0x55, 0x55)   # Xam     — RAW
COLOR_HEAD  = RGBColor(0x1F, 0x35, 0x64)   # Xanh dam — tieu de


def _change_color(change_type: str) -> RGBColor:
    return {
        "THÊM": COLOR_THEM, "THEM": COLOR_THEM,
        "XOÁ":  COLOR_XOA,  "XOA":  COLOR_XOA,
        "SỬA":  COLOR_SUA,  "SUA":  COLOR_SUA,
    }.get(change_type.upper(), COLOR_RAW)


def _set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = COLOR_HEAD
    return p


def section_changes_table(doc: Document, changes_detail: List[Dict]):
    _add_heading(doc, "Danh sach thay doi Hop dong", level=2)

    if not changes_detail:
        doc.add_paragraph("Khong phat hien thay doi nao giua hai phien ban.")
        return

    from collections import Counter
    counts = Counter(c.get("type", "?") for c in changes_detail)
    stats = "  |  ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    p = doc.add_paragraph()
    r = p.add_run(f"Tong so thay doi: {len(changes_detail)}   ({stats})")
    r.bold = True

    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"

    headers = ["STT", "Loại sửa đổi", "Điều khoản thay đổi", "Nội dung cũ", "Nội dung mới"]
    hdr_cells = table.rows[0].cells
    bg_colors = ["1F3564", "1F3564", "1F3564", "1F3564", "1F3564"]
    for i, (cell, header, bg) in enumerate(zip(hdr_cells, headers, bg_colors)):
        cell.text = header
        _set_cell_bg(cell, bg)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(9)

    widths = [Inches(0.4), Inches(0.9), Inches(1.5), Inches(2.3), Inches(2.3)]
    for i, width in enumerate(widths):
        for row in table.rows:
            row.cells[i].width = width

    for idx, change in enumerate(changes_detail, 1):
        row_cells = table.add_row().cells
        ctype = change.get("type", "?").upper()
        heading = change.get("heading", change.get("clause_id", ""))
        old_txt = change.get("old_text", "")
        new_txt = change.get("new_text", "")

        row_cells[0].text = str(idx)
        row_cells[1].text = ctype
        row_cells[2].text = heading
        row_cells[3].text = old_txt
        row_cells[4].text = new_txt

        color_hex = {
            "THÊM": "C6EFCE", "THEM": "C6EFCE",
            "XOÁ":  "FFC7CE", "XOA":  "FFC7CE",
            "XÓA":  "FFC7CE",
            "SỬA":  "FFEB9C", "SUA":  "FFEB9C",
        }.get(ctype, "F2F2F2")
        _set_cell_bg(row_cells[1], color_hex)

        text_color = _change_color(ctype)
        for para in row_cells[1].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = text_color
                run.font.size = Pt(9)

        for cell in row_cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(9)

    doc.add_paragraph()


def run_pipeline(doc_id: str, old: str, new: str) -> Dict:
    """Chay toan bo pipeline va tra ve report dict."""
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(doc_id, old, new, k=20)
    citation_mapper = CitationMapper(retriever=comparator.retriever)
    enriched = citation_mapper.enrich_changes(comparison)
    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)
    report["_enriched"] = enriched
    return report


def generate_word_report(
    doc_id: str = "Hop_dong_A",
    old: str = "v1",
    new: str = "v2",
    output_path: str = "output/bao_cao_So_Sanh_Giao_Dien_Moi.docx",
    from_json: str | None = None,
):
    """Sinh bao cao Word tu pipeline hoac tu file JSON."""
    Path("output").mkdir(exist_ok=True)

    if from_json:
        print(f"[*] Doc du lieu tu {from_json}")
        with open(from_json, encoding="utf-8") as f:
            report = json.load(f)
        doc_id = report.get("doc_id", doc_id)
        old = report.get("version_old", old)
        new = report.get("version_new", new)
    else:
        print(f"[*] So sanh {doc_id}: {old} -> {new}")
        print("[*] Buoc 1: Truy xuat va so sanh...")
        report = run_pipeline(doc_id, old, new)

    changes_detail = report.get("changes_detail", [])
    print(f"    Phat hien {len(changes_detail)} thay doi")

    print("[*] Tao file Word...")
    doc = Document()

    for section in doc.sections:
        # Mo rong thuoc tinh trang de chua vua 5 cot (Standard US Letter 8.5inch width)
        # 8.5 - 0.5*2 = 7.5 inch width total
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(0.5)
        section.right_margin  = Inches(0.5)

    title = doc.add_heading("Báo cáo So sánh Hợp đồng", level=0)
    for run in title.runs:
        run.font.color.rgb = COLOR_HEAD
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph(
        f"Tai lieu: {doc_id}   |   So sanh: {old} -> {new}\n"
        f"Ngay tao: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in subtitle.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    doc.add_paragraph()

    section_changes_table(doc, changes_detail)

    doc.save(output_path)
    print(f"\n[OK] Da luu bao cao: {output_path}")
    print(f"     So trang uoc tinh: ~{1 + len(changes_detail) // 5}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Sinh bao cao Word")
    parser.add_argument("--doc-id", default="Hop_dong_A")
    parser.add_argument("--old", default="v1")
    parser.add_argument("--new", default="v2")
    parser.add_argument("--out", default="output/bao_cao_So_Sanh_Giao_Dien_Moi.docx")
    parser.add_argument("--from-json", default=None, help="Doc report tu file JSON")
    args = parser.parse_args()

    generate_word_report(
        doc_id=args.doc_id,
        old=args.old,
        new=args.new,
        output_path=args.out,
        from_json=args.from_json,
    )


if __name__ == "__main__":
    main()
