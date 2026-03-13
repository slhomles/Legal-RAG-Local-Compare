from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb

from legal_rag.config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR, DEVICE, EMBEDDING_MODEL_NAME
from legal_rag.db.embedding import BGEEmbeddingModel


class VectorStoreManager:
    """
    Manage local embeddings and the Chroma collection for legal chunks.
    """

    def __init__(self) -> None:
        print(f"[*] Dang tai mo hinh nhung {EMBEDDING_MODEL_NAME}...")
        self.embeddings = BGEEmbeddingModel(
            model_name=EMBEDDING_MODEL_NAME,
            device=DEVICE,
        )
        print(f"[+] Khoi tao Embedding Model thanh cong ({self.embeddings.backend}).")
        self._create_vector_db()

    def _create_vector_db(self) -> None:
        print(f"[*] Ket noi den ChromaDB tai: {CHROMA_DB_DIR}")
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.vector_db = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
        )
        print("[+] Ket noi Vector DB thanh cong.")

    def reset_collection(self) -> None:
        print(f"[*] Xoa du lieu cu trong collection: {CHROMA_COLLECTION_NAME}")
        try:
            self.client.delete_collection(name=CHROMA_COLLECTION_NAME)
            print("[+] Da xoa collection cu.")
        except Exception as exc:
            print(f"[!] Khong the xoa collection cu sach se: {exc}")

        self.vector_db = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
        )

    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            print("[!] Khong co du lieu de them vao co so du lieu.")
            return

        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            if {"id", "content", "metadata"}.issubset(chunk):
                ids.append(chunk["id"])
                texts.append(chunk["content"])
                metadatas.append(chunk["metadata"])

        if not texts:
            print("[!] Khong co chunk hop le de luu.")
            return

        print(f"[*] Dang nhung va luu {len(texts)} doan van ban...")
        embeddings = self.embeddings.embed_documents(texts)
        self.vector_db.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        print("[+] Da luu du lieu vao ChromaDB thanh cong.")

    def search_similar(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[List[Any]]]:
        print(f"[*] Dang tim kiem: '{query}'...")
        query_embedding = self.embeddings.embed_query(query)
        return self.search_by_embedding(
            query_embedding=query_embedding,
            k=k,
            filter_dict=filter_dict,
        )

    def search_by_embedding(
        self,
        query_embedding: List[float],
        k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[List[Any]]]:
        print(f"[*] Dang tim kiem vector top-{k} trong ChromaDB...")
        return self.vector_db.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"],
        )
