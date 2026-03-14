"""
Retrieval module - Tìm kiếm vector và truy xuất những đoạn văn bản liên quan.
"""

from typing import List, Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

from legal_rag.config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME


class LegalRetriever:
    """
    Class để kết nối Vector DB và thực hiện tìm kiếm vector tương đồng.
    """
    
    def __init__(self):
        """Khởi tạo retriever với embedding model và vector store."""
        print(f"[*] Đang tải embedding model {EMBEDDING_MODEL_NAME}...")
        
        # Khởi tạo mô hình embedding
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        print("[+] Embedding model loaded.")
        
        # Kết nối đến ChromaDB
        print(f"[*] Connecting to ChromaDB at {CHROMA_DB_DIR}...")
        self.vector_db = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DB_DIR)
        )
        print("[+] Connected to Vector DB.")
    
    def search(
        self, 
        query: str, 
        k: int = 3,
        document_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm k chunks tương đồng nhất với câu truy vấn.
        
        Args:
            query: Câu truy vấn (ví dụ: "Quy định về thanh toán")
            k: Số lượng kết quả trả về (mặc định: 3)
            document_id: Filter theo document_id (optional)
            version: Filter theo version (optional)
        
        Returns:
            Danh sách k chunks với metadata đầy đủ
        """
        print(f"\n[*] Searching: '{query}'")
        print(f"    k={k}, document_id={document_id}, version={version}")
        
        # Xây dựng filter nếu có
        filter_dict = None
        if document_id or version:
            filter_dict = {}
            if document_id:
                filter_dict["document_id"] = document_id
            if version:
                filter_dict["version"] = version
        
        # Thực hiện similarity search
        results = self.vector_db.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        # Format kết quả
        formatted_results = []
        for i, doc in enumerate(results, 1):
            result = {
                "rank": i,
                "document_id": doc.metadata.get("document_id", "?"),
                "version": doc.metadata.get("version", "?"),
                "clause_id": doc.metadata.get("clause_id", "?"),
                "chunk_heading": doc.metadata.get("chunk_heading", "?"),
                "content": doc.page_content
            }
            formatted_results.append(result)
        
        print(f"[+] Found {len(formatted_results)} results.")
        return formatted_results
    
    def print_results(self, results: List[Dict[str, Any]], preview_chars: int = 300):
        """
        In kết quả tìm kiếm dưới dạng đễ đọc.
        
        Args:
            results: Danh sách kết quả từ search()
            preview_chars: Độ dài preview nội dung
        """
        print("\n" + "=" * 80)
        print("RETRIEVAL RESULTS")
        print("=" * 80)
        
        if not results:
            print("No results found.")
            return
        
        for result in results:
            preview = result["content"][:preview_chars]
            if len(result["content"]) > preview_chars:
                preview += "..."
            
            print(f"\n[RANK {result['rank']}]")
            print(f"  Document ID : {result['document_id']}")
            print(f"  Version     : {result['version']}")
            print(f"  Clause ID   : {result['clause_id']}")
            print(f"  Heading     : {result['chunk_heading']}")
            print(f"  Content     : {preview}")
        
        print("\n" + "=" * 80)
