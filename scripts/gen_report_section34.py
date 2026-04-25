"""
Sinh bao cao Word cho Phan 3 (Dinh nghia Metrics) va Phan 4 (Ket qua danh gia vong 1).
Output: output/bao_cao_section3_4.docx
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "bao_cao_section3_4.docx"
OUTPUT_PATH.parent.mkdir(exist_ok=True)

BLACK = RGBColor(0, 0, 0)
FONT_NAME = "Times New Roman"
FONT_SIZE = Pt(13)


def set_run_style(run, bold=False, size=None, color=None):
    run.font.name = FONT_NAME
    run.font.size = size or FONT_SIZE
    run.font.bold = bold
    run.font.color.rgb = color or BLACK
    # Set East Asian font
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rPr.insert(0, rFonts)


def add_heading(doc, text, level):
    """H1/H2/H3 bold, Times New Roman 13, black."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    para.paragraph_format.space_after = Pt(4)
    run = para.add_run(text)
    set_run_style(run, bold=True, size=Pt(13 if level >= 2 else 14))
    return para


def add_body(doc, text, indent=False):
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(2)
    if indent:
        para.paragraph_format.left_indent = Cm(0.75)
    run = para.add_run(text)
    set_run_style(run)
    return para


def add_bullet(doc, text, level=1):
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.left_indent = Cm(0.75 * level)
    para.paragraph_format.space_before = Pt(1)
    para.paragraph_format.space_after = Pt(1)
    run = para.add_run(text)
    set_run_style(run)
    return para


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.paragraphs[0].clear()
        run = cell.paragraphs[0].add_run(h)
        set_run_style(run, bold=True, size=Pt(11))
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Data rows
    for ri, row in enumerate(rows):
        tr = table.rows[ri + 1]
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            cell.paragraphs[0].clear()
            run = cell.paragraphs[0].add_run(str(val))
            set_run_style(run, size=Pt(11))
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Column widths
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


# ──────────────────────────────────────────
doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)

# ══════════════════════════════════════════
# PHAN 3: DINH NGHIA METRICS
# ══════════════════════════════════════════
add_heading(doc, "3. Định nghĩa Metrics đánh giá", 1)

# 3.1
add_heading(doc, "3.1. Precision / Recall / F1 cho phát hiện thay đổi", 2)
add_body(doc, (
    "Bộ ba chỉ số Precision, Recall và F1 đo lường khả năng phát hiện "
    "thay đổi điều khoản của hệ thống so với ground truth. "
    "Một thay đổi được tính là phát hiện đúng (True Positive) khi cặp "
    "(clause_id, loại thay đổi) khớp với ground truth."
))
add_bullet(doc, "TP (True Positive): thay đổi phát hiện đúng theo ground truth.")
add_bullet(doc, "FP (False Positive): thay đổi phát hiện thừa, không có trong ground truth.")
add_bullet(doc, "FN (False Negative): thay đổi trong ground truth bị bỏ sót.")

add_body(doc, "Công thức:")
add_body(doc, "Precision  =  TP / (TP + FP)", indent=True)
add_body(doc, "Recall     =  TP / (TP + FN)", indent=True)
add_body(doc, "F1         =  2 × Precision × Recall / (Precision + Recall)", indent=True)
add_body(doc, (
    "Recall ưu tiên phát hiện toàn diện (không bỏ sót), Precision kiểm soát "
    "phát hiện thừa. F1 là chỉ số tổng hợp cân bằng cả hai."
))

# 3.2
add_heading(doc, "3.2. Citation Accuracy (Độ chính xác trích dẫn)", 2)
add_body(doc, (
    "Đo tỷ lệ trích dẫn nguồn trong báo cáo tìm thấy đúng đoạn văn bản gốc "
    "trong ChromaDB. Một trích dẫn được coi là chính xác khi "
    "match_type ∈ {exact, normalized}."
))
add_body(doc, "Công thức:")
add_body(doc, (
    "Citation Accuracy  =  Số trích dẫn found / Tổng số trích dẫn"
), indent=True)
add_body(doc, (
    "Mỗi thay đổi có thể có hai nguồn: old_source (phiên bản cũ) và "
    "new_source (phiên bản mới). Cả hai được kiểm tra độc lập."
))

# 3.3
add_heading(doc, "3.3. Hallucination Rate (Tỷ lệ kết luận không có bằng chứng)", 2)
add_body(doc, (
    "Ước tính tỷ lệ thay đổi mà LLM đưa ra kết luận không có bằng chứng "
    "nguồn trong vector store. Một thay đổi bị coi là 'ungrounded' khi:"
))
add_bullet(doc, "SỬA: cả old_source và new_source đều found = False.")
add_bullet(doc, "THÊM: new_source found = False.")
add_bullet(doc, "XOÁ: old_source found = False.")
add_body(doc, "Công thức:")
add_body(doc, (
    "Hallucination Rate  =  Số thay đổi ungrounded / Tổng số thay đổi"
), indent=True)

# 3.4
add_heading(doc, "3.4. Thời gian xử lý trung bình", 2)
add_body(doc, (
    "Đo thời gian toàn bộ pipeline (embedding, retrieval, LLM inference, "
    "citation mapping) cho một cặp tài liệu, tính bằng giây. "
    "Thời gian phụ thuộc vào số điều khoản xử lý và tốc độ LLM cục bộ "
    "(Ollama qwen2.5:1.5b trên CPU)."
))
add_body(doc, "Công thức:")
add_body(doc, "T_total  =  T_end − T_start  (đơn vị: giây)", indent=True)
add_body(doc, "T_per_clause  =  T_total / n_clauses", indent=True)

# 3.5
add_heading(doc, "3.5. Tổng hợp công thức", 2)

table_35_headers = ["Metric", "Công thức", "Phạm vi", "Mục tiêu"]
table_35_rows = [
    ["Precision",        "TP / (TP + FP)",                       "[0, 1]", "Cao"],
    ["Recall",           "TP / (TP + FN)",                       "[0, 1]", "Cao"],
    ["F1",               "2×P×R / (P+R)",                        "[0, 1]", "Cao"],
    ["Citation Accuracy","#found / #total_citations",             "[0, 1]", "Cao"],
    ["Hallucination Rate","#ungrounded / #total_changes",         "[0, 1]", "Thấp"],
    ["Processing Time",  "T_end − T_start (s)",                  "[0, ∞)", "Thấp"],
    ["Guardrail Compliance","#compliant / #total_checks",         "[0, 1]", "= 1.0"],
]
add_table(doc, table_35_headers, table_35_rows, col_widths=[3.5, 5.5, 2.2, 1.8])

doc.add_paragraph()

# ══════════════════════════════════════════
# PHAN 4: KET QUA DANH GIA VONG 1
# ══════════════════════════════════════════
add_heading(doc, "4. Kết quả đánh giá vòng 1 (Baseline)", 1)
add_body(doc, (
    "Đánh giá được thực hiện trên 10 cặp hợp đồng (A–J) với k=30 chunks "
    "truy xuất, LLM Ollama qwen2.5:1.5b, embedding BAAI/bge-m3. "
    "Ngày chạy: 13/04/2026."
))

# 4.1
add_heading(doc, "4.1. Bảng tổng hợp kết quả theo từng metric", 2)

table_41_headers = ["Metric", "Trung bình", "Nhận xét"]
table_41_rows = [
    ["Precision",            "50.2%",  "Còn nhiều phát hiện thừa"],
    ["Recall",               "84.0%",  "Phát hiện tương đối đầy đủ"],
    ["F1",                   "62.0%",  "Cân bằng khá, cần cải thiện Precision"],
    ["Citation Accuracy",    "61.5%",  "Hơn 1/3 trích dẫn chưa tìm được nguồn"],
    ["Hallucination Rate",   "29.6%",  "Gần 30% kết luận thiếu bằng chứng nguồn"],
    ["Processing Time",      "235.6 s","Phụ thuộc LLM CPU; ~35 s/điều khoản"],
    ["Guardrail Compliance", "100.0%", "Toàn bộ output tuân thủ guardrails"],
]
add_table(doc, table_41_headers, table_41_rows, col_widths=[4.5, 2.8, 5.7])

doc.add_paragraph()

# 4.2
add_heading(doc, "4.2. Kết quả chi tiết theo từng cặp tài liệu", 2)

table_42_headers = ["Tài liệu", "Loại HĐ", "Độ khó", "Precision", "Recall", "F1", "Citation Acc.", "Hallucination", "Time (s)"]
table_42_rows = [
    ["Hợp đồng A", "Mua bán HH",    "Dễ",    "75.0%", "100%", "85.7%", "54.2%", "41.7%", "245.9"],
    ["Hợp đồng B", "Dịch vụ CNTT",  "Dễ",    "50.0%", "100%", "66.7%", "81.3%", "12.5%", "461.4"],
    ["Hợp đồng C", "Thuê VP",       "Dễ",    "33.3%", "100%", "50.0%", "56.3%", "37.5%", "159.2"],
    ["Hợp đồng D", "Thi công",      "TB",    "42.9%",  "75%", "54.5%", "60.0%", "30.0%", "182.3"],
    ["Hợp đồng E", "Tư vấn PL",     "TB",    "71.4%", "100%", "83.3%", "72.7%", "18.2%", "161.6"],
    ["Hợp đồng F", "Thiết bị CN",   "TB",    "50.0%",  "75%", "60.0%", "57.1%", "28.6%", "196.3"],
    ["Hợp đồng G", "Vận chuyển",    "TB",    "28.6%",  "67%", "40.0%", "50.0%", "37.5%", "140.1"],
    ["Hợp đồng H", "Liên doanh",    "Khó",   "28.6%",  "40%", "33.3%", "35.7%", "57.1%", "134.2"],
    ["Hợp đồng I", "CGCN",          "Khó",   "66.7%", "100%", "80.0%", "78.6%", "14.3%", "430.5"],
    ["Hợp đồng J", "Nghiên cứu",    "Khó",   "55.6%",  "83%", "66.7%", "68.8%", "18.8%", "245.0"],
]
add_table(doc, table_42_headers, table_42_rows,
          col_widths=[2.8, 2.8, 1.6, 2.2, 1.8, 1.8, 2.5, 2.6, 1.9])

doc.add_paragraph()

# 4.3
add_heading(doc, "4.3. Kết quả theo loại thay đổi", 2)
add_body(doc, (
    "Phân tích dựa trên tổng 42 thay đổi trong ground truth: "
    "SỬA (28 trường hợp, 66.7%), THÊM (10 trường hợp, 23.8%), "
    "XOÁ (4 trường hợp, 9.5%)."
))

table_43_headers = ["Loại thay đổi", "Số lượng GT", "Đặc điểm phát hiện", "Nhận xét"]
table_43_rows = [
    ["SỬA",  "28 (66.7%)",
     "Recall ~85%, dễ phát hiện nội dung thay đổi rõ ràng (số liệu, thời hạn).",
     "Khó khi thay đổi từ ngữ gần nghĩa (Hợp đồng I)."],
    ["THÊM", "10 (23.8%)",
     "Recall ~90%, điều khoản mới thường nổi bật về cấu trúc.",
     "Đôi khi phát hiện thừa do nhận nhầm nội dung cũ."],
    ["XOÁ",  "4 (9.5%)",
     "Recall ~75%, khó hơn vì không có nội dung hiện diện trong v2.",
     "Tỷ lệ ungrounded cao nhất — không có new_source để trích dẫn."],
]
add_table(doc, table_43_headers, table_43_rows, col_widths=[2.5, 2.5, 5.5, 4.5])

doc.add_paragraph()

# 4.4
add_heading(doc, "4.4. Kết quả theo độ khó", 2)

table_44_headers = ["Độ khó", "Số tài liệu", "Avg F1", "Avg Citation Acc.", "Avg Hallucination", "Avg Time (s)"]
table_44_rows = [
    ["Dễ",    "3 (A, B, C)", "67.5%", "63.9%", "30.6%", "288.8"],
    ["Trung bình", "4 (D, E, F, G)", "59.5%", "59.9%", "28.6%", "170.1"],
    ["Khó",   "3 (H, I, J)", "60.0%", "61.0%", "30.1%", "269.9"],
]
add_table(doc, table_44_headers, table_44_rows, col_widths=[2.8, 3.5, 2.0, 3.5, 3.5, 2.7])

doc.add_paragraph()
add_body(doc, (
    "Nhận xét: Tài liệu dễ đạt F1 cao nhất nhờ thay đổi số liệu rõ ràng. "
    "Tài liệu trung bình có thời gian xử lý thấp hơn do ít điều khoản phức tạp. "
    "Tài liệu khó (đặc biệt Hợp đồng H, I) cho thấy thách thức lớn với "
    "thay đổi cấu trúc sâu và thuật ngữ chuyên biệt — Hợp đồng H đạt F1 thấp nhất "
    "(33.3%) trong khi Hợp đồng I đạt F1 cao (80.0%) do thay đổi vẫn "
    "có dấu hiệu rõ về số liệu."
))

# Save
doc.save(OUTPUT_PATH)
print(f"Da luu: {OUTPUT_PATH}")
