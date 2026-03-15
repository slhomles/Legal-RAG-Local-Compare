# Logic truy xuất đoạn văn bản liên quan dựa trên metadata và vector [cite: 16]
from typing import Any, Dict, List, Optional

from legal_rag.db.vector_store import VectorStoreManager


class LegalRetriever:
    def __init__(self):
        self.vector_store = VectorStoreManager()

    def semantic_search(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Thực hiện tìm kiếm semantic top-K trên Vector DB.

        Args:
            query: Câu truy vấn tự nhiên, ví dụ "quy định về thanh toán"
            k: Số lượng kết quả trả về
            filter_dict: Bộ lọc metadata nếu cần (chưa bắt buộc ở commit 2)

        Returns:
            Danh sách Document tìm được từ ChromaDB
        """
        return self.vector_store.search_similar(
            query=query,
            k=k,
            filter_dict=filter_dict
        )