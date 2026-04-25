# ---------------------------------------------------------------------------
# Prompt templates cho hệ thống so sánh hợp đồng pháp lý.
#
# Nguyên tắc cốt lõi:
#   1. "Không bằng chứng → Không kết luận"  (strict grounding)
#   2. Không đưa ra kết luận pháp lý / tư vấn pháp luật
#   3. Không đánh giá tính hợp pháp của tài liệu
# ---------------------------------------------------------------------------

# ===========================================================================
# SYSTEM PROMPT  –  áp dụng cho MỌI lệnh gọi LLM trong hệ thống
# ===========================================================================
SYSTEM_PROMPT = """\
Bạn là trợ lý phân tích hợp đồng. Nhiệm vụ của bạn là tìm và liệt kê sự khác biệt \
giữa hai phiên bản hợp đồng.

QUY TẮC:
1. Chỉ trích đúng CỤM TỪ bị thay đổi (con số, từ khoá, ngày tháng, tên riêng…). \
TUYỆT ĐỐI KHÔNG trích lại cả câu hay cả đoạn dài.
2. Cụm từ trích phải xuất hiện y nguyên trong văn bản được cung cấp — không tự bịa, \
không dùng chữ "trích nguyên văn" hay bất kỳ placeholder nào.
3. Chỉ MÔ TẢ sự thay đổi, không đánh giá hay tư vấn pháp lý.
4. Trả về JSON hợp lệ theo schema được yêu cầu trong user prompt; nếu không có \
thay đổi nào thì trả về mảng rỗng.
5. Nội dung text trong JSON viết bằng tiếng Việt.
"""

# ===========================================================================
# USER PROMPT — so sánh chi tiết hai phiên bản của MỘT điều khoản
# ===========================================================================
COMPARISON_USER_TEMPLATE = """\
So sánh hai phiên bản dưới đây của **{clause_heading}**.

--- PHIÊN BẢN CŨ ({version_old}) ---
{text_old}

--- PHIÊN BẢN MỚI ({version_new}) ---
{text_new}

Trả về DUY NHẤT một JSON object hợp lệ theo schema sau (không markdown, không chú thích):

{{
  "changes": [
    {{
      "type":     "THÊM" | "XOÁ" | "SỬA",
      "old_text": "<cụm từ ngắn trong bản cũ>",
      "new_text": "<cụm từ ngắn trong bản mới>",
      "location": "<vị trí như: Khoản 2.1>"
    }}
  ]
}}

Nguyên tắc:
- Mỗi phần tử chỉ ghi ĐÚNG cụm từ bị đổi (con số, từ khoá, ngày tháng), KHÔNG lặp cả câu.
- old_text và new_text PHẢI xuất hiện y nguyên trong văn bản phía trên; không tự bịa, không copy ví dụ minh hoạ.
- type = THÊM thì old_text = "" ; type = XOÁ thì new_text = "" ; type = SỬA thì old_text và new_text PHẢI KHÁC NHAU.
- **CẤM TUYỆT ĐỐI** tạo entry có old_text trùng khớp hoàn toàn với new_text (ví dụ cả hai đều là "Tạm ứng 30% giá trị hợp đồng"). Nếu một câu/cụm xuất hiện y hệt ở cả hai phiên bản → nó KHÔNG phải thay đổi, không đưa vào mảng.
- **CẤM** tạo entry có cả old_text và new_text đều rỗng ("").
- Nếu hai phiên bản giống hệt nhau → trả về {{"changes": []}}.
- Không lặp lại cùng một cặp (old_text, new_text) trong mảng.

Ví dụ minh hoạ format (chủ đề NẤU ĂN — KHÔNG phải nội dung thật, chỉ để minh hoạ cú pháp JSON):
Cũ: "Cho 2 thìa đường vào nồi."
Mới: "Cho 3 thìa đường vào nồi."
→ {{"changes": [{{"type": "SỬA", "old_text": "2 thìa", "new_text": "3 thìa", "location": "Bước 1"}}]}}

TUYỆT ĐỐI không đưa các chữ "thìa", "đường", "nồi", "bước" hay bất kỳ phần nào của ví dụ vào câu trả lời thật.
"""

# ===========================================================================
# USER PROMPT — tóm tắt tổng hợp các thay đổi quan trọng
# ===========================================================================
SUMMARY_USER_TEMPLATE = """\
Dưới đây là danh sách các thay đổi đã được phát hiện giữa phiên bản {version_old} và {version_new} \
của hợp đồng **{doc_id}**:

{changes_text}

### YÊU CẦU
Hãy tóm tắt các điểm thay đổi quan trọng nhất theo các nhóm sau:
1. **Thay đổi về nội dung tài chính** (giá trị, phương thức thanh toán, thuế, phí…)
2. **Thay đổi về thời hạn và điều kiện** (thời gian giao hàng, bảo hành, hiệu lực…)
3. **Thay đổi về quyền và nghĩa vụ** (trách nhiệm các bên, phạt vi phạm…)
4. **Điều khoản thêm mới hoặc bị xoá**

Với mỗi điểm tóm tắt, ghi rõ điều khoản liên quan (ví dụ: Điều 2, Điều 5).

### RÀNG BUỘC
- Chỉ tóm tắt dựa trên danh sách thay đổi ở trên. KHÔNG thêm thông tin ngoài ngữ cảnh.
- KHÔNG đưa ra kết luận pháp lý, tư vấn, hay đánh giá tính hợp pháp.
- Nếu một nhóm không có thay đổi nào, ghi: "Không có thay đổi."
"""

# ===========================================================================
# GUARDRAIL — Hậu kiểm output của LLM trước khi trả về người dùng
# ===========================================================================
GUARDRAIL_BANNED_PHRASES = [
    "hợp pháp",
    "vi phạm pháp luật",
    "vi phạm luật",
    "khuyến nghị",
    "rủi ro pháp lý",
    "nên thay đổi",
    "nên sửa",
    "nên bổ sung",
    "có lợi hơn",
    "bất lợi hơn",
    "chặt chẽ hơn",
    "lỏng lẻo hơn",
    "tư vấn pháp luật",
    "theo quy định của pháp luật",
    "trái pháp luật",
]

GUARDRAIL_WARNING = (
    "[CẢNH BÁO] Kết quả chứa nội dung có thể mang tính kết luận pháp lý. "
    "Hệ thống chỉ trích xuất sự khác biệt, KHÔNG đưa ra tư vấn pháp luật."
)


def check_guardrails(text: str) -> tuple[bool, list[str]]:
    """
    Kiểm tra output LLM có chứa cụm từ vi phạm guardrails không.

    Returns:
        (is_clean, violations): True nếu output hợp lệ, danh sách cụm từ vi phạm nếu có.
    """
    text_lower = text.lower()
    violations = [phrase for phrase in GUARDRAIL_BANNED_PHRASES if phrase in text_lower]
    return (len(violations) == 0, violations)
