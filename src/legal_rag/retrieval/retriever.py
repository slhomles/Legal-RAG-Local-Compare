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
        return self.vector_store.search_similar(
            query=query,
            k=k,
            filter_dict=filter_dict
        )

    def _normalize_clause_id(self, clause_id: str) -> str:
        return " ".join(clause_id.strip().split()).title()

    def get_clause_by_version(
        self,
        document_id: str,
        clause_id: str,
        version: str,
        k: int = 5
    ) -> List[Any]:
        clause_id = self._normalize_clause_id(clause_id)

        return self.vector_store.search_similar(
            query=clause_id,
            k=k,
            filter_dict={
                "$and": [
                    {"document_id": document_id},
                    {"version": version},
                    {"clause_id": clause_id}
                ]
            }
        )

    def retrieve_clause_pair(
        self,
        document_id: str,
        clause_id: str,
        k: int = 5
    ) -> Dict[str, List[Any]]:
        clause_id = self._normalize_clause_id(clause_id)

        original_docs = self.get_clause_by_version(document_id, clause_id, "A", k=k)
        revised_docs = self.get_clause_by_version(document_id, clause_id, "B", k=k)

        return {
            "clause_id": clause_id,
            "A": original_docs,
            "B": revised_docs
        }
    def _merge_docs(self, docs: List[Any]) -> str:
        if not docs:
            return ""

        merged_parts = []
        seen = set()

        for doc in docs:
            content = doc.page_content.strip()
            if content and content not in seen:
                merged_parts.append(content)
                seen.add(content)

        return "\n\n".join(merged_parts)

    def build_paired_context(
        self,
        document_id: str,
        clause_id: str,
        k: int = 5
    ) -> Dict[str, Dict[str, str]]:
        clause_id = self._normalize_clause_id(clause_id)

        pair_result = self.retrieve_clause_pair(document_id, clause_id, k=k)

        original_text = self._merge_docs(pair_result["A"])
        revised_text = self._merge_docs(pair_result["B"])

        return {
            clause_id: {
                "Bản_gốc": original_text,
                "Bản_sửa_đổi": revised_text
            }
        }