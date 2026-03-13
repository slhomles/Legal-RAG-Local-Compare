import os
from typing import Any, Dict, List

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

from legal_rag.config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR, DEVICE, EMBEDDING_MODEL_NAME


class VectorStoreManager:
    """
    Manage local embeddings and the Chroma collection for legal chunks.
    """

    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        print(f"[*] Dang tai mo hinh nhung {EMBEDDING_MODEL_NAME}...")
        model_kwargs = {"device": DEVICE}
        encode_kwargs = {"normalize_embeddings": True}

        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        print("[+] Khoi tao Embedding Model thanh cong.")

        self._create_vector_db()

    def _create_vector_db(self) -> None:
        print(f"[*] Ket noi den ChromaDB tai: {CHROMA_DB_DIR}")
        self.vector_db = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DB_DIR),
        )
        print("[+] Ket noi Vector DB thanh cong.")

    def reset_collection(self) -> None:
        print(f"[*] Xoa du lieu cu trong collection: {CHROMA_COLLECTION_NAME}")
        try:
            self.vector_db.delete_collection()
            print("[+] Da xoa collection cu.")
        except Exception as exc:
            print(f"[!] Khong the xoa collection cu sach se: {exc}")

        self._create_vector_db()

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

        print(f"[*] Dang nhung va luu {len(texts)} doan van ban...")
        self.vector_db.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )
        self.vector_db.persist()
        print("[+] Da luu du lieu vao ChromaDB thanh cong.")

    def search_similar(self, query: str, k: int = 3, filter_dict: Dict = None) -> List[Any]:
        print(f"[*] Dang tim kiem: '{query}'...")
        return self.vector_db.similarity_search(
            query=query,
            k=k,
            filter=filter_dict,
        )
