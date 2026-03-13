from __future__ import annotations

from typing import Any, Dict, List, Optional

from legal_rag.db.vector_store import VectorStoreManager


class LegalRetriever:
    """
    Core semantic retriever for legal chunks stored in ChromaDB.
    """

    def __init__(self, vector_store_manager: Optional[VectorStoreManager] = None) -> None:
        self.vector_store = vector_store_manager or VectorStoreManager()

    def retrieve(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Embed the user query with BGE-M3 and run a KNN search on ChromaDB.
        """
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query must not be empty.")
        if k <= 0:
            raise ValueError("k must be greater than 0.")

        query_embedding = self.vector_store.embeddings.embed_query(normalized_query)
        raw_results = self.vector_store.search_by_embedding(
            query_embedding=query_embedding,
            k=k,
            filter_dict=filter_dict,
        )
        return self._format_results(raw_results)

    @staticmethod
    def _format_results(raw_results: Dict[str, List[List[Any]]]) -> List[Dict[str, Any]]:
        ids = raw_results.get("ids", [[]])
        documents = raw_results.get("documents", [[]])
        metadatas = raw_results.get("metadatas", [[]])
        distances = raw_results.get("distances", [[]])

        result_ids = ids[0] if ids else []
        result_documents = documents[0] if documents else []
        result_metadatas = metadatas[0] if metadatas else []
        result_distances = distances[0] if distances else []

        formatted_results: List[Dict[str, Any]] = []
        for index, chunk_id in enumerate(result_ids):
            formatted_results.append(
                {
                    "rank": index + 1,
                    "id": chunk_id,
                    "content": result_documents[index],
                    "metadata": result_metadatas[index] or {},
                    "distance": result_distances[index] if index < len(result_distances) else None,
                }
            )

        return formatted_results
