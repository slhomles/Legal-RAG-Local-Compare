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
COLOR_CITE  = RGBColor(0x00, 0x56, 0x96)   # Xanh duong — citation


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


def _add_colored_para(doc: Document, label: str, content: str, color: RGBColor):
    p = doc.add_paragraph()
    run_label = p.add_run(f"{label}: ")
    run_label.bold = True
    run_label.font.color.rgb = color
    run_content = p.add_run(content)
    run_content.font.color.rgb = color
    return p


def _add_code_block(doc: Document, text: str):
    p = doc.add_paragraph()
    p.style = "Normal"
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "12")
    left.set(qn("w:space"), "12")
    left.set(qn("w:color"), "4472C4")
    pBdr.append(left)
    pPr.append(pBdr)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "360")
    pPr.append(ind)
    return p


def section_json_output(doc: Document, comparison: Dict, enriched: Dict):
    _add_heading(doc, "III.1. Dinh dang dau ra JSON", level=2)

    doc.add_paragraph(
        "Duoi day la cau truc JSON day du cua ket qua so sanh, "
        "bao gom thong tin tung dieu khoan, loai thay doi va trich dan vi tri."
    )

    compact: Dict[str, Any] = {
        "doc_id": enriched["doc_id"],
        "version_old": enriched["version_old"],
        "version_new": enriched["version_new"],
        "new_clauses": enriched.get("new_clauses", []),
        "removed_clauses": enriched.get("removed_clauses", []),
        "clauses": {},
    }

    for cid, cdata in enriched.get("clauses", {}).items():
        clause_out: Dict[str, Any] = {
            "heading": cdata.get("heading", cid),
            "guardrail_ok": cdata.get("guardrail_ok", True),
            "changes": [],
        }
        for ch in cdata.get("changes", []):
            ch_out: Dict[str, Any] = {
                "type": ch.get("type", ""),
                "old_text": ch.get("old_text", "")[:80] + ("..." if len(ch.get("old_text","")) > 80 else ""),
                "new_text": ch.get("new_text", "")[:80] + ("..." if len(ch.get("new_text","")) > 80 else ""),
                "location": ch.get("location", ""),
            }
            cit = ch.get("citations", {})
            if cit:
                ch_out["citations"] = {
                    k: {
                        "found": v.get("found"),
                        "match_type": v.get("match_type"),
                        "chunk_id": v.get("chunk_id"),
                        "char_start": v.get("char_start"),
                        "char_end": v.get("char_end"),
                    }
                    for k, v in cit.items()
                    if isinstance(v, dict)
                }
            clause_out["changes"].append(ch_out)
        compact["clauses"][cid] = clause_out

    json_text = json.dumps(compact, ensure_ascii=False, indent=2)
    _add_code_block(doc, json_text)


def section_changes_table(doc: Document, changes_detail: List[Dict]):
    _add_heading(doc, "III.2. Danh sach thay doi THEM / XOA / SUA", level=2)

    if not changes_detail:
        doc.add_paragraph("Khong phat hien thay doi nao giua hai phien ban.")
        return

    from collections import Counter
    counts = Counter(c.get("type", "?") for c in changes_detail)
    stats = "  |  ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    p = doc.add_paragraph()
    r = p.add_run(f"Tong so thay doi: {len(changes_detail)}   ({stats})")
    r.bold = True

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    headers = ["STT", "Dieu khoan", "Loai", "Mo ta thay doi"]
    hdr_cells = table.rows[0].cells
    bg_colors = ["1F3564", "1F3564", "1F3564", "1F3564"]
    for i, (cell, header, bg) in enumerate(zip(hdr_cells, headers, bg_colors)):
        cell.text = header
        _set_cell_bg(cell, bg)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(9)

    widths = [Inches(0.4), Inches(1.8), Inches(0.7), Inches(3.6)]
    for i, width in enumerate(widths):
        for row in table.rows:
            row.cells[i].width = width

    for idx, change in enumerate(changes_detail, 1):
        row_cells = table.add_row().cells
        ctype = change.get("type", "?")
        heading = change.get("heading", change.get("clause_id", ""))
        old_txt = change.get("old_text", "")
        new_txt = change.get("new_text", "")
        location = change.get("location", "")

        desc_parts = []
        if old_txt:
            desc_parts.append(f"Cu: {old_txt[:100]}{'...' if len(old_txt)>100 else ''}")
        if new_txt:
            desc_parts.append(f"Moi: {new_txt[:100]}{'...' if len(new_txt)>100 else ''}")
        if location:
            desc_parts.append(f"Vi tri: {location}")
        description = "\n".join(desc_parts)

        row_cells[0].text = str(idx)
        row_cells[1].text = heading
        row_cells[2].text = ctype
        row_cells[3].text = description

        color_hex = {
            "THÊM": "C6EFCE", "THEM": "C6EFCE",
            "XOÁ":  "FFC7CE", "XOA":  "FFC7CE",
            "SỬA":  "FFEB9C", "SUA":  "FFEB9C",
        }.get(ctype.upper(), "F2F2F2")
        _set_cell_bg(row_cells[2], color_hex)

        text_color = _change_color(ctype)
        for para in row_cells[2].paragraphs:
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

    _add_heading(doc, "III.2.b. Dinh dang Markdown", level=3)
    md_lines = ["| STT | Dieu khoan | Loai | Noi dung cu | Noi dung moi |",
                "|-----|-----------|------|-------------|--------------|"]
    for idx, ch in enumerate(changes_detail, 1):
        old = ch.get("old_text", "")[:60].replace("|", "｜")
        new = ch.get("new_text", "")[:60].replace("|", "｜")
        heading = ch.get("heading", "").replace("|", "｜")
        md_lines.append(f"| {idx} | {heading} | {ch.get('type','')} | {old} | {new} |")
    _add_code_block(doc, "\n".join(md_lines))


def section_summary(doc: Document, report: Dict):
    _add_heading(doc, "III.3. Tom tat diem thay doi quan trong", level=2)

    summary = report.get("summary", "(Khong co tom tat)")
    guardrail_ok = report.get("guardrail_ok", True)

    if not guardrail_ok:
        p = doc.add_paragraph()
        r = p.add_run("CANH BAO GUARDRAIL: Phat hien noi dung co the mang tinh ket luan phap ly.")
        r.bold = True
        r.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
        violations = report.get("guardrail_violations", [])
        doc.add_paragraph(f"Cum tu vi pham: {', '.join(violations)}")

    for line in summary.split("\n"):
        if line.strip():
            p = doc.add_paragraph(line.strip(), style="List Bullet" if line.startswith(("-", "+", "*")) else "Normal")


def section_citation_log(doc: Document, changes_detail: List[Dict]):
    _add_heading(doc, "III.4. Log trich doan va vi tri (Citation Log)", level=2)

    doc.add_paragraph(
        "Bang duoi day the hien tung thay doi kem doan trich dan chinh xac "
        "va vi tri ky tu (char_start / char_end) trong chunk goc."
    )

    found_any = False
    for change in changes_detail:
        citations = change.get("citations", {})
        heading = change.get("heading", change.get("clause_id", ""))
        ctype = change.get("type", "")
        has_citation = any(
            isinstance(v, dict) and v.get("found")
            for v in citations.values()
        )
        if not has_citation:
            continue
        found_any = True

        p = doc.add_paragraph()
        r = p.add_run(f"[{ctype}] {heading}")
        r.bold = True
        r.font.color.rgb = _change_color(ctype)

        for src_key, label in [("old_source", "Phien ban cu"), ("new_source", "Phien ban moi")]:
            src = citations.get(src_key, {})
            if not isinstance(src, dict) or not src.get("found"):
                continue

            chunk_id   = src.get("chunk_id", "")
            match_type = src.get("match_type", "")
            char_start = src.get("char_start", "N/A")
            char_end   = src.get("char_end", "N/A")
            excerpt    = src.get("excerpt", "") or change.get(
                "old_text" if src_key == "old_source" else "new_text", ""
            )
            hierarchy  = src.get("hierarchy_path", "")
            version    = src.get("version", "")

            p2 = doc.add_paragraph()
            p2.paragraph_format.left_indent = Inches(0.3)
            r2 = p2.add_run(f"{label}  ")
            r2.bold = True
            r2.font.color.rgb = COLOR_CITE
            p2.add_run(f"[{match_type.upper()}]  chunk: {chunk_id}")

            p3 = doc.add_paragraph()
            p3.paragraph_format.left_indent = Inches(0.3)
            p3.add_run(f"Vi tri: ky tu {char_start} -> {char_end}   |   {hierarchy}   |   ver={version}")
            for run in p3.runs:
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

            if excerpt:
                p4 = doc.add_paragraph()
                p4.paragraph_format.left_indent = Inches(0.4)
                r4 = p4.add_run(f'"{excerpt[:200]}{"..." if len(excerpt) > 200 else ""}"')
                r4.italic = True
                r4.font.size = Pt(9)
                r4.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
                pPr = p4._p.get_or_add_pPr()
                pBdr = OxmlElement("w:pBdr")
                left = OxmlElement("w:left")
                left.set(qn("w:val"), "single")
                left.set(qn("w:sz"), "18")
                left.set(qn("w:space"), "8")
                left.set(qn("w:color"), "4472C4" if src_key == "new_source" else "70AD47")
                pBdr.append(left)
                pPr.append(pBdr)

        doc.add_paragraph()

    if not found_any:
        doc.add_paragraph("(Khong co trich dan nao duoc tim thay chinh xac.)")

    _add_heading(doc, "III.4.b. Log dang text", level=3)
    log_lines: List[str] = []
    for i, ch in enumerate(changes_detail, 1):
        log_lines.append(f"[{i}] {ch.get('heading','')} — {ch.get('type','')}")
        cit = ch.get("citations", {})
        for src_key in ("old_source", "new_source"):
            src = cit.get(src_key, {})
            if isinstance(src, dict) and src.get("found"):
                log_lines.append(
                    f"    {src_key}: chunk={src.get('chunk_id','')} | "
                    f"match={src.get('match_type','')} | "
                    f"pos={src.get('char_start','?')}..{src.get('char_end','?')}"
                )
            else:
                reason = src.get("reason","") if isinstance(src, dict) else ""
                log_lines.append(f"    {src_key}: not found — {reason}")
        log_lines.append("")
    _add_code_block(doc, "\n".join(log_lines))


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
    output_path: str = "output/bao_cao_section_III.docx",
    from_json: str | None = None,
):
    """Sinh bao cao Word tu pipeline hoac tu file JSON."""
    Path("output").mkdir(exist_ok=True)

    if from_json:
        print(f"[*] Doc du lieu tu {from_json}")
        with open(from_json, encoding="utf-8") as f:
            report = json.load(f)
        enriched = report.get("_enriched", report)
        doc_id = report.get("doc_id", doc_id)
        old = report.get("version_old", old)
        new = report.get("version_new", new)
    else:
        print(f"[*] So sanh {doc_id}: {old} -> {new}")
        print("[*] Buoc 1: Truy xuat va so sanh...")
        report = run_pipeline(doc_id, old, new)
        enriched = report.get("_enriched", report)

    changes_detail = report.get("changes_detail", [])
    print(f"    Phat hien {len(changes_detail)} thay doi")

    print("[*] Tao file Word...")
    doc = Document()

    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    title = doc.add_heading("Bao cao So sanh Hop dong", level=0)
    for run in title.runs:
        run.font.color.rgb = COLOR_HEAD
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph(
        f"Muc III: Ket qua So sanh va Trich dan\n"
        f"Tai lieu: {doc_id}   |   So sanh: {old} -> {new}\n"
        f"Ngay tao: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in subtitle.runs:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    doc.add_paragraph()

    section_json_output(doc, enriched, enriched)
    doc.add_page_break()

    section_changes_table(doc, changes_detail)
    doc.add_page_break()

    section_summary(doc, report)
    doc.add_page_break()

    section_citation_log(doc, changes_detail)

    doc.save(output_path)
    print(f"\n[OK] Da luu bao cao: {output_path}")
    print(f"     So trang uoc tinh: ~{4 + len(changes_detail) // 3}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Sinh bao cao Word - Muc III")
    parser.add_argument("--doc-id", default="Hop_dong_A")
    parser.add_argument("--old", default="v1")
    parser.add_argument("--new", default="v2")
    parser.add_argument("--out", default="output/bao_cao_section_III.docx")
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
