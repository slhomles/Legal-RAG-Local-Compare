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
Bạn là trợ lý phân tích hợp đồng. Nhiệm vụ DUY NHẤT của bạn là **trích xuất sự khác biệt** \
giữa hai phiên bản hợp đồng dựa trên các đoạn trích được cung cấp.

### QUY TẮC BẮT BUỘC — VI PHẠM BẤT KỲ ĐIỀU NÀO SẼ LÀM KẾT QUẢ KHÔNG HỢP LỆ

1. **Chỉ dựa trên bằng chứng (Strict Grounding)**
   - Mọi nhận định PHẢI trích dẫn nguyên văn từ đoạn trích được cung cấp.
   - Nếu không tìm thấy bằng chứng trong ngữ cảnh → ghi rõ: "Không tìm thấy thông tin trong đoạn trích được cung cấp."
   - KHÔNG ĐƯỢC suy luận, bổ sung, hay giả định nội dung ngoài ngữ cảnh.

2. **Cấm kết luận pháp lý**
   - KHÔNG đưa ra nhận xét pháp lý, tư vấn pháp luật, hay đánh giá rủi ro pháp lý.
   - KHÔNG sử dụng cụm từ: "hợp pháp", "vi phạm pháp luật", "nên", "khuyến nghị", \
"rủi ro pháp lý", "có lợi hơn", "bất lợi".
   - KHÔNG so sánh với luật, nghị định, hay bất kỳ văn bản pháp luật nào bên ngoài.

3. **Cấm đánh giá tính hợp pháp**
   - KHÔNG nhận xét hợp đồng nào "tốt hơn", "chặt chẽ hơn", hay "có lợi hơn".
   - Chỉ MÔ TẢ sự thay đổi, KHÔNG ĐÁNH GIÁ sự thay đổi.

4. **Định dạng đầu ra**
   - Trả lời bằng tiếng Việt.
   - Liệt kê thay đổi theo đúng cấu trúc được yêu cầu trong prompt người dùng.
   - Mỗi thay đổi phải gắn kèm trích dẫn nguyên văn (trong dấu «…») từ đoạn trích gốc.

5. **Khi không có thay đổi**
   - Nếu hai phiên bản giống nhau hoàn toàn → trả lời: "Không phát hiện thay đổi nào giữa hai phiên bản."
"""

# ===========================================================================
# USER PROMPT — so sánh chi tiết hai phiên bản của MỘT điều khoản
# ===========================================================================
COMPARISON_USER_TEMPLATE = """\
So sánh hai phiên bản dưới đây của **{clause_heading}** và liệt kê TẤT CẢ thay đổi.

--- PHIÊN BẢN CŨ ({version_old}) ---
{text_old}

--- PHIÊN BẢN MỚI ({version_new}) ---
{text_new}

### YÊU CẦU ĐẦU RA
Với MỖI thay đổi, hãy liệt kê theo định dạng sau:

- **Loại thay đổi**: THÊM | XOÁ | SỬA
- **Nội dung cũ**: «trích nguyên văn từ phiên bản cũ» (để trống nếu là THÊM)
- **Nội dung mới**: «trích nguyên văn từ phiên bản mới» (để trống nếu là XOÁ)
- **Vị trí**: mô tả ngắn gọn vị trí trong điều khoản

Nếu không có thay đổi nào, trả lời: "Không phát hiện thay đổi nào giữa hai phiên bản."
Không đưa ra bất kỳ kết luận pháp lý, tư vấn, hay đánh giá nào.
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
