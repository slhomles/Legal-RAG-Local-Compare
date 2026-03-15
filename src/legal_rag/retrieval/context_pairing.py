from typing import Any, Dict, List
from collections import defaultdict

class ContextPairer:
    """
    Module hỗ trợ ghép cặp dữ liệu kết quả từ Retriever thành format JSON cấu trúc.
    Dữ liệu được gom nhóm theo logical_id (điều khoản) và sau đó là version.
    """

    def __init__(self):
        pass

    def pair_chunks(self, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """
        Nhận vào list các dictionary chunk, trả về cây:
        {
            "dieu_3": {
                "v1": "Nội dung...",
                "v2": "Nội dung..."
            }
        }
        """
        paired: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            logical_id = meta.get("logical_id", "unknown_clause")
            version = meta.get("version", "unknown_version")
            content = chunk.get("content", "").strip()

            if content:
                paired[logical_id][version].append(content)

        # Nối các chunk thuộc cùng điều khoản và phiên bản (nếu chunking chia nhỏ nội dung quá dài)
        final_paired: Dict[str, Dict[str, str]] = {}
        for logical_id, versions in paired.items():
            final_paired[logical_id] = {}
            for version, contents_list in versions.items():
                final_paired[logical_id][version] = "\n".join(contents_list)

        return final_paired
