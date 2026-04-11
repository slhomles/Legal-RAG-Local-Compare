# ---------------------------------------------------------------------------
# Module ánh xạ (mapping) kết quả đầu ra với metadata để lấy chính xác
# trích đoạn và vị trí của đoạn văn bản gốc.
#
# Mỗi thay đổi được gắn kèm:
#   - chunk_id gốc (doc_id:version:logical_id:pXX)
#   - heading của điều khoản
#   - hierarchy_path (breadcrumb vị trí trong cấu trúc hợp đồng)
#   - vị trí ký tự (char_start, char_end) của trích đoạn trong chunk gốc
# ---------------------------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, List, Optional

from legal_rag.retrieval.retriever import LegalRetriever


class CitationMapper:
    """
    Ánh xạ mỗi thay đổi với metadata chính xác từ ChromaDB,
    bao gồm vị trí trích đoạn trong văn bản gốc.
    """

    def __init__(self, retriever: Optional[LegalRetriever] = None) -> None:
        self.retriever = retriever or LegalRetriever()

    def enrich_changes(
        self,
        comparison_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Nhận kết quả từ DocumentComparator.compare_versions() và bổ sung
        thông tin trích dẫn chính xác (citation) cho mỗi thay đổi.

        Trả về comparison_result đã được bổ sung trường 'citations' cho mỗi change.
        """
        doc_id = comparison_result["doc_id"]
        version_old = comparison_result["version_old"]
        version_new = comparison_result["version_new"]

        # Lấy tất cả chunks liên quan để tra cứu
        chunk_lookup = self._build_chunk_lookup(doc_id, version_old, version_new)

        for clause_id, clause_data in comparison_result.get("clauses", {}).items():
            for change in clause_data.get("changes", []):
                citations = self._find_citations(
                    change=change,
                    clause_id=clause_id,
                    version_old=version_old,
                    version_new=version_new,
                    chunk_lookup=chunk_lookup,
                )
                change["citations"] = citations

        return comparison_result

    def _build_chunk_lookup(
        self,
        doc_id: str,
        version_old: str,
        version_new: str,
        k: int = 50,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Xây dựng bảng tra cứu chunk theo (logical_id, version).

        Returns:
            {
                "dieu_1:v1": {
                    "chunk_id": "Hop_dong_A:v1:dieu_1:p01",
                    "content": "...",
                    "metadata": {...}
                },
                ...
            }
        """
        filter_dict = {
            "$and": [
                {"doc_id": doc_id},
                {"version": {"$in": [version_old, version_new]}},
            ]
        }

        results = self.retriever.retrieve(
            query=f"hop dong {doc_id}",
            k=k,
            filter_dict=filter_dict,
        )

        lookup: Dict[str, Dict[str, Any]] = {}
        for chunk in results:
            meta = chunk.get("metadata", {})
            lid = meta.get("logical_id", "")
            ver = meta.get("version", "")
            key = f"{lid}:{ver}"

            if key not in lookup:
                lookup[key] = {
                    "chunk_id": chunk.get("id", ""),
                    "content": chunk.get("content", ""),
                    "metadata": meta,
                }
            else:
                # Nối nội dung nếu cùng clause + version có nhiều chunk
                lookup[key]["content"] += "\n" + chunk.get("content", "")

        return lookup

    def _find_citations(
        self,
        change: Dict[str, str],
        clause_id: str,
        version_old: str,
        version_new: str,
        chunk_lookup: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Tìm vị trí chính xác của trích đoạn thay đổi trong chunk gốc.

        Returns:
            {
                "old_source": {
                    "chunk_id": "...",
                    "heading": "...",
                    "hierarchy_path": "...",
                    "excerpt": "...",
                    "char_start": 100,
                    "char_end": 200,
                    "found": True
                },
                "new_source": { ... }
            }
        """
        citations: Dict[str, Any] = {}

        # Tìm citation cho nội dung cũ
        old_text = change.get("old_text", "").strip()
        if old_text:
            old_key = f"{clause_id}:{version_old}"
            citations["old_source"] = self._locate_excerpt(
                excerpt=old_text,
                lookup_key=old_key,
                chunk_lookup=chunk_lookup,
            )
        else:
            citations["old_source"] = {"found": False, "reason": "Noi dung cu trong"}

        # Tìm citation cho nội dung mới
        new_text = change.get("new_text", "").strip()
        if new_text:
            new_key = f"{clause_id}:{version_new}"
            citations["new_source"] = self._locate_excerpt(
                excerpt=new_text,
                lookup_key=new_key,
                chunk_lookup=chunk_lookup,
            )
        else:
            citations["new_source"] = {"found": False, "reason": "Noi dung moi trong"}

        return citations

    def _locate_excerpt(
        self,
        excerpt: str,
        lookup_key: str,
        chunk_lookup: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Tìm vị trí chính xác của excerpt trong chunk gốc.
        Hỗ trợ exact match và fuzzy match (substring normalization).
        """
        chunk_info = chunk_lookup.get(lookup_key)
        if not chunk_info:
            return {"found": False, "reason": f"Khong tim thay chunk {lookup_key}"}

        content = chunk_info["content"]
        meta = chunk_info["metadata"]

        # Exact match
        pos = content.find(excerpt)
        if pos != -1:
            return {
                "found": True,
                "match_type": "exact",
                "chunk_id": chunk_info["chunk_id"],
                "heading": meta.get("chunk_heading", ""),
                "hierarchy_path": meta.get("hierarchy_path", ""),
                "doc_id": meta.get("doc_id", ""),
                "version": meta.get("version", ""),
                "excerpt": excerpt,
                "char_start": pos,
                "char_end": pos + len(excerpt),
            }

        # Normalized match: bỏ khoảng trắng thừa
        normalized_content = _normalize_whitespace(content)
        normalized_excerpt = _normalize_whitespace(excerpt)
        pos = normalized_content.find(normalized_excerpt)
        if pos != -1:
            # Tìm vị trí tương ứng trong content gốc
            original_pos = _map_normalized_pos(content, pos)
            return {
                "found": True,
                "match_type": "normalized",
                "chunk_id": chunk_info["chunk_id"],
                "heading": meta.get("chunk_heading", ""),
                "hierarchy_path": meta.get("hierarchy_path", ""),
                "doc_id": meta.get("doc_id", ""),
                "version": meta.get("version", ""),
                "excerpt": excerpt,
                "char_start": original_pos,
                "char_end": original_pos + len(excerpt),
            }

        # Substring match: thử tìm phần đầu excerpt
        partial = excerpt[:min(40, len(excerpt))]
        pos = content.find(partial)
        if pos != -1:
            return {
                "found": True,
                "match_type": "partial",
                "chunk_id": chunk_info["chunk_id"],
                "heading": meta.get("chunk_heading", ""),
                "hierarchy_path": meta.get("hierarchy_path", ""),
                "doc_id": meta.get("doc_id", ""),
                "version": meta.get("version", ""),
                "excerpt": excerpt,
                "char_start": pos,
                "char_end": None,
            }

        return {
            "found": False,
            "match_type": "none",
            "chunk_id": chunk_info["chunk_id"],
            "heading": meta.get("chunk_heading", ""),
            "hierarchy_path": meta.get("hierarchy_path", ""),
            "reason": "Khong tim thay trich doan trong chunk goc",
        }


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def _normalize_whitespace(text: str) -> str:
    """Thu gọn mọi khoảng trắng liên tiếp thành 1 dấu cách."""
    return " ".join(text.split())


def _map_normalized_pos(original: str, normalized_pos: int) -> int:
    """
    Ánh xạ vị trí trong chuỗi đã normalize về vị trí trong chuỗi gốc.
    """
    norm_idx = 0
    in_space = False
    for orig_idx, ch in enumerate(original):
        if ch in (" ", "\t", "\n", "\r"):
            if not in_space:
                if norm_idx == normalized_pos:
                    return orig_idx
                norm_idx += 1
                in_space = True
        else:
            if norm_idx == normalized_pos:
                return orig_idx
            norm_idx += 1
            in_space = False
    return len(original)
