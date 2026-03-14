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
        print(f"[*] Loading embedding model {EMBEDDING_MODEL_NAME}...")
        
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
        version: Optional[str] = None,
        clause_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm k chunks tương đồng nhất với câu truy vấn.
        
        Args:
            query: Câu truy vấn (ví dụ: "Quy định về thanh toán")
            k: Số lượng kết quả trả về (mặc định: 3)
            document_id: Filter theo document_id (optional)
            version: Filter theo version (optional)
            clause_id: Filter theo clause_id (ví dụ: "Dieu 3") (optional)
        
        Returns:
            Danh sách k chunks với metadata đầy đủ
        """
        print(f"\n[*] Searching: '{query}'")
        print(f"    k={k}, document_id={document_id}, version={version}, clause_id={clause_id}")
        
        # Xây dựng filter nếu có
        filter_dict = None
        if document_id or version or clause_id:
            filters = []
            if document_id:
                filters.append({"document_id": document_id})
            if version:
                filters.append({"version": version})
            if clause_id:
                filters.append({"clause_id": clause_id})
            
            if len(filters) == 1:
                filter_dict = filters[0]
            elif len(filters) > 1:
                filter_dict = {"$and": filters}
        
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
    
    def search_by_clause_id(
        self,
        clause_id: str,
        document_id: Optional[str] = None,
        versions: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tìm kiếm chunks chính xác theo clause_id (Metadata Filtering).
        
        Phương thức này ưu tiên metadata filtering thay vì semantic search,
        đảm bảo lấy đúng điều khoản được chỉ định.
        
        Args:
            clause_id: ID điều khoản cần tìm (ví dụ: "Dieu 1", "Dieu 3", "Chuong I")
            document_id: Filter theo document_id (optional)
            versions: Danh sách các version cần lấy (ví dụ: ["v1", "v2"] hoặc ["A", "B"])
                      Nếu None, lấy tất cả các version có sẵn
        
        Returns:
            Dictionary với key là version, value là danh sách chunks:
            {
                "v1": [chunk1, chunk2, ...],
                "v2": [chunk1, chunk2, ...],
                ...
            }
        """
        print(f"\n[*] Search by clause_id: '{clause_id}'")
        print(f"    document_id={document_id}, versions={versions}")
        
        results_by_version = {}
        
        # Nếu không chỉ định versions, lấy tất cả versions để khám phá
        target_versions = versions if versions else [None]
        
        for version in target_versions:
            # Xây dựng filter
            filters = [{"clause_id": clause_id}]
            if document_id:
                filters.append({"document_id": document_id})
            if version:
                filters.append({"version": version})
            
            if len(filters) == 1:
                filter_dict = filters[0]
            else:
                filter_dict = {"$and": filters}
            
            # Lấy tất cả chunks khớp với filter (không dùng semantic search)
            # Sử dụng similarity_search với k lớn để lấy tất cả khớp
            results = self.vector_db.similarity_search(
                query="",  # Empty query để tìm chỉ dựa vào metadata filter
                k=100,  # Số lượng lớn để lấy tất cả
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
            
            version_key = version if version else "all"
            if formatted_results:
                results_by_version[version_key] = formatted_results
                print(f"[+] Found {len(formatted_results)} results for version '{version_key}'.")
            else:
                print(f"[-] No results found for version '{version_key}'.")
        
        return results_by_version
    
    def search_clause_with_both_versions(
        self,
        clause_id: str,
        document_id: Optional[str] = None,
        versions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Lấy cùng một điều khoản từ 2 phiên bản để so sánh (Dual-Version Retrieval).
        
        Tối ưu hóa cho bài toán đối chiếu tài liệu: lấy "Dieu 3" từ cả version v1 và v2.
        
        Args:
            clause_id: ID điều khoản cần so sánh (ví dụ: "Dieu 3", "Dieu 1")
            document_id: Document cần so sánh (optional)
            versions: 2 phiên bản để so sánh (hoặc tương đương: "A"/"B", "v1"/"v2")
                     Mặc định: ["v1", "v2"]
        
        Returns:
            Dictionary sau:
            {
                "clause_id": "Dieu 3",
                "versions": {
                    "v1": {
                        "content": "...",
                        "metadata": {...}
                    },
                    "v2": {
                        "content": "...",
                        "metadata": {...}
                    }
                },
                "comparison_ready": True/False
            }
        """
        if versions is None:
            versions = ["v1", "v2"]
        
        if len(versions) != 2:
            print("[!] Warning: Expected 2 versions for comparison. Got:", versions)
        
        print(f"\n[*] Compare clause_id: '{clause_id}'")
        print(f"    Versions: {versions}")
        
        comparison_data = {
            "clause_id": clause_id,
            "versions": {}
        }
        
        for version in versions:
            filters = [{"clause_id": clause_id}, {"version": version}]
            if document_id:
                filters.append({"document_id": document_id})
            filter_dict = {"$and": filters}
            
            results = self.vector_db.similarity_search(
                query="",
                k=100,
                filter=filter_dict
            )
            
            if results:
                # Lấy chunk đầu tiên (chunk chính của điều khoản)
                doc = results[0]
                comparison_data["versions"][version] = {
                    "content": doc.page_content,
                    "metadata": {
                        "document_id": doc.metadata.get("document_id", "?"),
                        "version": doc.metadata.get("version", "?"),
                        "clause_id": doc.metadata.get("clause_id", "?"),
                        "chunk_heading": doc.metadata.get("chunk_heading", "?"),
                    },
                    "chunks_count": len(results)
                }
                print(f"[+] Found '{version}': {len(results)} chunk(s)")
            else:
                comparison_data["versions"][version] = None
                print(f"[-] No data found for version '{version}'")
        
        # Kiểm tra xem có dữ liệu từ cả 2 version hay không
        comparison_data["comparison_ready"] = all(
            comparison_data["versions"].get(v) is not None 
            for v in versions
        )
        
        if not comparison_data["comparison_ready"]:
            print("[!] Warning: Not all versions have data available for comparison.")
        
        return comparison_data
    
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
    
    def print_results_by_version(
        self,
        results_by_version: Dict[str, List[Dict[str, Any]]],
        preview_chars: int = 300
    ):
        """
        In kết quả từ search_by_clause_id() theo từng version.
        
        Args:
            results_by_version: Dictionary từ search_by_clause_id()
            preview_chars: Độ dài preview nội dung
        """
        print("\n" + "=" * 80)
        print("RETRIEVAL RESULTS BY VERSION")
        print("=" * 80)
        
        if not results_by_version:
            print("No results found.")
            return
        
        for version, results in results_by_version.items():
            print(f"\n{'█' * 80}")
            print(f"VERSION: {version}")
            print(f"{'█' * 80}")
            
            for result in results:
                preview = result["content"][:preview_chars]
                if len(result["content"]) > preview_chars:
                    preview += "..."
                
                print(f"\n[CHUNK {result['rank']}]")
                print(f"  Document ID : {result['document_id']}")
                print(f"  Clause ID   : {result['clause_id']}")
                print(f"  Heading     : {result['chunk_heading']}")
                print(f"  Content     : {preview}")
        
        print("\n" + "=" * 80)
    
    def print_clause_comparison(
        self,
        comparison_data: Dict[str, Any],
        preview_chars: int = 300
    ):
        """
        In kết quả so sánh 2 version của cùng 1 điều khoản.
        
        Args:
            comparison_data: Dictionary từ search_clause_with_both_versions()
            preview_chars: Độ dài preview nội dung
        """
        print("\n" + "=" * 80)
        print(f"CLAUSE COMPARISON: {comparison_data['clause_id']}")
        print("=" * 80)
        
        if not comparison_data.get("versions"):
            print("No versions found.")
            return
        
        versions_list = list(comparison_data["versions"].keys())
        
        for i, version in enumerate(versions_list, 1):
            version_data = comparison_data["versions"][version]
            
            if version_data is None:
                print(f"\n[VERSION {version}] - ⚠️ NO DATA AVAILABLE")
                continue
            
            print(f"\n{'▼' * 80}")
            print(f"[VERSION {version}]")
            print(f"{'▼' * 80}")
            
            metadata = version_data.get("metadata", {})
            print(f"  Document ID : {metadata.get('document_id', '?')}")
            print(f"  Clause ID   : {metadata.get('clause_id', '?')}")
            print(f"  Heading     : {metadata.get('chunk_heading', '?')}")
            print(f"  Chunks      : {version_data.get('chunks_count', 1)}")
            print()
            
            content = version_data.get("content", "")
            preview = content[:preview_chars]
            if len(content) > preview_chars:
                preview += "\n    ..."
            
            print(f"  Content:\n    {preview}")
        
        print("\n" + "=" * 80)
        
        if comparison_data.get("comparison_ready"):
            print("✅ READY FOR COMPARISON")
        else:
            print("❌ INCOMPLETE DATA - Some versions are missing")
        
        print("=" * 80 + "\n")
