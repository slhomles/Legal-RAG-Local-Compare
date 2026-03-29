# Lưu trữ các prompt template ép LLM tuân thủ "không bằng chứng -> không kết luận" [cite: 36]
import json
from typing import Any, Dict


COMPARE_SYSTEM_PROMPT = """
Bạn là trợ lý so sánh văn bản pháp lý chạy cục bộ.

NHIỆM VỤ:
- So sánh 2 đoạn văn bản thuộc cùng một điều khoản giữa 2 phiên bản tài liệu.
- Chỉ xác định sự khác biệt về mặt nội dung văn bản.
- Chỉ được kết luận khi có bằng chứng trực tiếp trong dữ liệu đầu vào.

RÀNG BUỘC BẮT BUỘC:
1. Không được suy đoán.
2. Không được bịa thêm nội dung không xuất hiện trong dữ liệu đầu vào.
3. Nếu không đủ bằng chứng, phải trả về "unknown".
4. Không được đưa ra tư vấn pháp luật.
5. Không được đánh giá tính hợp pháp, hiệu lực, rủi ro pháp lý của tài liệu.
6. Không được sử dụng kiến thức bên ngoài.
7. Chỉ dựa trên văn bản được cung cấp.
8. Phải trả về đúng định dạng JSON được yêu cầu.

PHÂN LOẠI THAY ĐỔI:
- added: nội dung chỉ có ở bản sửa đổi
- removed: nội dung chỉ có ở bản gốc
- modified: cùng điều khoản nhưng nội dung có thay đổi
- unchanged: không có thay đổi đáng kể
- unknown: không đủ bằng chứng để kết luận

NGUYÊN TẮC:
- Không bằng chứng -> không kết luận
- Không trích dẫn được -> không khẳng định
"""


def get_compare_output_schema() -> Dict[str, Any]:
    return {
        "document_id": "string",
        "clause_id": "string",
        "status": "added | removed | modified | unchanged | unknown",
        "changes": [
            {
                "change_type": "added | removed | modified",
                "summary": "string",
                "evidence_from_original": "string | null",
                "evidence_from_revised": "string | null",
                "confidence": "high | medium | low"
            }
        ],
        "note": "string"
    }


def build_compare_user_prompt(
    document_id: str,
    clause_id: str,
    original_text: str,
    revised_text: str
) -> str:
    schema_str = json.dumps(
        get_compare_output_schema(),
        ensure_ascii=False,
        indent=2
    )

    return f"""
Hãy so sánh 2 phiên bản của cùng một điều khoản.

document_id: {document_id}
clause_id: {clause_id}

[BẢN_GỐC]
{original_text}

[BẢN_SỬA_ĐỔI]
{revised_text}

YÊU CẦU:
1. Xác định loại thay đổi: added / removed / modified / unchanged / unknown
2. Liệt kê các thay đổi cụ thể
3. Mỗi thay đổi phải có evidence_from_original và evidence_from_revised
4. Nếu một phía không có evidence thì ghi null
5. Không đưa ra nhận xét pháp lý
6. Không đánh giá tài liệu đúng luật hay sai luật
7. Chỉ mô tả khác biệt văn bản
8. Trả về đúng JSON, không thêm giải thích ngoài JSON

JSON schema mong muốn:
{schema_str}
"""