"""
Output Formatter - Chuyển đổi kết quả truy xuất thành cấu trúc JSON có tổ chức

Chuyển từ danh sách chunks lộn xộn thành Dictionary ghép cặp rõ ràng:
{
    "Điều 1": {
        "Bản_gốc": "nội dung v1...",
        "Bản_sửa_đổi": "nội dung v2..."
    },
    "Điều 2": {...},
    ...
}
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ClauseContent:
    """Đại diện cho nội dung một điều khoản từ một phiên bản"""
    version: str
    document_id: str
    heading: str
    content: str
    chunk_count: int = 1


class RetrievalOutputFormatter:
    """
    Định hình dữ liệu từ LegalRetriever thành cấu trúc JSON có tổ chức
    """
    
    def __init__(self):
        self.clause_data = {}  # {clause_id: {version: content}}
    
    def add_clause_result(
        self,
        clause_id: str,
        version: str,
        document_id: str,
        heading: str,
        content: str,
        chunk_count: int = 1
    ) -> None:
        """
        Thêm kết quả truy xuất cho một điều khoản
        
        Args:
            clause_id: ID của điều khoản (ví dụ: "Dieu 3")
            version: Phiên bản (ví dụ: "v1", "v2")
            document_id: ID tài liệu (ví dụ: "Hop_dong_A_v1.docx")
            heading: Tiêu đề của điều khoản
            content: Nội dung đầy đủ
            chunk_count: Số lượng chunks được gộp lại
        """
        if clause_id not in self.clause_data:
            self.clause_data[clause_id] = {}
        
        self.clause_data[clause_id][version] = {
            "document_id": document_id,
            "heading": heading,
            "content": content,
            "chunk_count": chunk_count,
            "version": version
        }
    
    def add_from_comparison_dict(self, comparison: Dict[str, Any]) -> None:
        """
        Thêm dữ liệu từ kết quả so sánh của LegalRetriever.search_clause_with_both_versions()
        
        Hỗ trợ cả 2 định dạng:
        1. Old format (từ search_by_clause_id):
            {
                "clause_id": "Dieu 3",
                "comparison_ready": True,
                "v1": [chunks],
                "v2": [chunks]
            }
        
        2. New format (từ search_clause_with_both_versions):
            {
                "clause_id": "Dieu 3",
                "comparison_ready": True,
                "versions": {
                    "v1": {
                        "content": "...",
                        "metadata": {...},
                        "chunks_count": 1
                    },
                    "v2": {...}
                }
            }
        """
        clause_id = comparison.get("clause_id")
        if not clause_id:
            return
        
        # Hỗ trợ cả 2 định dạng
        if "versions" in comparison:
            # Format mới: search_clause_with_both_versions()
            for version, version_data in comparison.get("versions", {}).items():
                if version_data:  # Kiểm tra dữ liệu không phải None
                    metadata = version_data.get("metadata", {})
                    self.add_clause_result(
                        clause_id=clause_id,
                        version=version,
                        document_id=metadata.get("document_id", ""),
                        heading=metadata.get("chunk_heading", ""),
                        content=version_data.get("content", ""),
                        chunk_count=version_data.get("chunks_count", 1)
                    )
        else:
            # Format cũ: search_by_clause_id()
            for version in ["v1", "v2"]:
                if version in comparison and comparison[version]:
                    chunks = comparison[version]
                    if isinstance(chunks, list) and chunks:
                        # Gộp các chunks với tiêu đề đầu tiên
                        first_chunk = chunks[0]
                        
                        # Gộp nội dung của các chunks
                        combined_content = "\n\n".join([
                            chunk.get("content", "") for chunk in chunks
                        ])
                        
                        self.add_clause_result(
                            clause_id=clause_id,
                            version=version,
                            document_id=first_chunk.get("document_id", ""),
                            heading=first_chunk.get("chunk_heading", ""),
                            content=combined_content,
                            chunk_count=len(chunks)
                        )
    
    def get_paired_format(self) -> Dict[str, Dict[str, str]]:
        """
        Lấy dữ liệu dưới dạng ghép cặp rõ ràng
        
        Returns:
            {
                "Điều 1": {
                    "Bản_gốc": "nội dung v1...",
                    "Bản_sửa_đổi": "nội dung v2..."
                },
                ...
            }
        """
        paired = {}
        
        for clause_id, versions_data in self.clause_data.items():
            v1_content = versions_data.get("v1", {}).get("content", "")
            v2_content = versions_data.get("v2", {}).get("content", "")
            
            # Chỉ thêm nếu có ít nhất một phiên bản
            if v1_content or v2_content:
                paired[clause_id] = {
                    "Bản_gốc": v1_content if v1_content else "[KHÔNG CÓ DỮ LIỆU]",
                    "Bản_sửa_đổi": v2_content if v2_content else "[KHÔNG CÓ DỮ LIỆU]"
                }
        
        return paired
    
    def get_detailed_format(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy dữ liệu chi tiết với metadata
        
        Returns:
            {
                "Điều 1": {
                    "v1": {
                        "document_id": "...",
                        "heading": "...",
                        "content": "...",
                        "chunk_count": 2
                    },
                    "v2": {...}
                },
                ...
            }
        """
        return self.clause_data
    
    def to_json(self, detailed: bool = False) -> str:
        """
        Chuyển đổi thành JSON string
        
        Args:
            detailed: Nếu True, trả về định dạng chi tiết; nếu False, trả về định dạng ghép cặp
        
        Returns:
            JSON string
        """
        data = self.get_detailed_format() if detailed else self.get_paired_format()
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def to_dict(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Chuyển đổi thành Dictionary
        
        Args:
            detailed: Nếu True, trả về định dạng chi tiết; nếu False, trả về định dạng ghép cặp
        
        Returns:
            Dictionary
        """
        return self.get_detailed_format() if detailed else self.get_paired_format()
    
    def save_json(self, filepath: str, detailed: bool = False) -> None:
        """
        Lưu kết quả thành file JSON
        
        Args:
            filepath: Đường dẫn file JSON cần lưu
            detailed: Nếu True, lưu định dạng chi tiết
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json(detailed=detailed))
        print(f"[+] Đã lưu kết quả vào: {filepath}")
    
    def display(self, detailed: bool = False) -> None:
        """
        In kết quả ra màn hình ở dạng định dạng đẹp
        
        Args:
            detailed: Nếu True, hiển thị định dạng chi tiết
        """
        print("\n" + "="*80)
        print("KẾT QUẢ TRỸ XUẤT - DANH SÁCH ĐIỀU KHOẢN")
        print("="*80)
        
        data = self.to_dict(detailed=detailed)
        
        for clause_id, versions_or_content in sorted(data.items()):
            print(f"\n{clause_id}")
            print("-" * 80)
            
            if detailed:
                # Định dạng chi tiết
                for version, info in sorted(versions_or_content.items()):
                    print(f"\n  📄 {version.upper()} ({info.get('document_id', '?')})")
                    print(f"     Tiêu đề: {info.get('heading', '?')}")
                    print(f"     Chunks: {info.get('chunk_count', 1)}")
                    print(f"     Nội dung:")
                    
                    content = info.get('content', '')
                    lines = content.split('\n')[:5]  # Hiển thị 5 dòng đầu
                    for line in lines:
                        print(f"       {line}")
                    if len(content.split('\n')) > 5:
                        print(f"       ... ({len(content.split(chr(10)))} dòng tổng cộng)")
            else:
                # Định dạng ghép cặp
                print(f"\n  ✏️  Bản gốc (v1):")
                v1 = versions_or_content.get("Bản_gốc", "")
                lines = v1.split('\n')[:4]
                for line in lines:
                    if line.strip():
                        print(f"     {line[:70]}")
                
                print(f"\n  ✏️  Bản sửa đổi (v2):")
                v2 = versions_or_content.get("Bản_sửa_đổi", "")
                lines = v2.split('\n')[:4]
                for line in lines:
                    if line.strip():
                        print(f"     {line[:70]}")
        
        print("\n" + "="*80 + "\n")
    
    def get_comparison_summary(self) -> Dict[str, Any]:
        """
        Lấy tóm tắt so sánh: số lượng điều khoản, phiên bản có sẵn, v.v.
        
        Returns:
            {
                "total_clauses": 6,
                "clauses_with_both_versions": 5,
                "clauses_missing_v1": ["Dieu 6"],
                "clauses_missing_v2": [],
                ...
            }
        """
        total = len(self.clause_data)
        both_versions = sum(1 for v in self.clause_data.values() if "v1" in v and "v2" in v)
        missing_v1 = [cid for cid, v in self.clause_data.items() if "v1" not in v]
        missing_v2 = [cid for cid, v in self.clause_data.items() if "v2" not in v]
        
        return {
            "total_clauses": total,
            "clauses_with_both_versions": both_versions,
            "clauses_missing_v1": missing_v1,
            "clauses_missing_v2": missing_v2,
            "comparison_ready": both_versions == total
        }
