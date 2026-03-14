#!/usr/bin/env python
"""
CLI script để thực hiện tìm kiếm vector trên Legal RAG Database.

Ví dụ sử dụng:
    # 1. Tìm kiếm semantic thông thường
    python retrieve.py "Quy định về thanh toán"
    python retrieve.py "Quy định về thanh toán" --k 5
    
    # 2. Tìm kiếm với filter metadata
    python retrieve.py "Quy định về bảo hành" --doc-id "Hop_dong_A" --version "v2"
    python retrieve.py "..." --clause-id "Dieu 3"
    
    # 3. Lấy điều khoản cụ thể bằng metadata filtering (không dùng semantic search)
    python retrieve.py --clause-id "Dieu 3" --metadata-only
    
    # 4. So sánh cùng điều khoản giữa 2 version
    python retrieve.py --clause-id "Dieu 3" --compare-versions
    python retrieve.py --clause-id "Dieu 1" --compare-versions --doc-id "Hop_dong_A"
    python retrieve.py --clause-id "Dieu 5" --compare-versions --versions "v1" "v2"
"""

import sys
import io
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from legal_rag.retrieval.retriever import LegalRetriever


def main():
    parser = argparse.ArgumentParser(
        description="Tìm kiếm đoạn hợp đồng liên quan dựa trên câu truy vấn hoặc điều khoản",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Semantic search (mặc định)
  python retrieve.py "Thanh toán sản phẩm"
  python retrieve.py "Bảo hành" --k 5
  
  # Metadata filtering (lọc theo clause_id)
  python retrieve.py --clause-id "Dieu 3" --metadata-only
  python retrieve.py --clause-id "Dieu 3" --doc-id "Hop_dong_A"
  
  # Dual-version comparison (so sánh 2 version)
  python retrieve.py --clause-id "Dieu 3" --compare-versions
  python retrieve.py --clause-id "Dieu 1" --compare-versions --versions "v1" "v2"
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default=None,
        help="Câu truy vấn semantic (ví dụ: 'Quy định về thanh toán'). Không cần nếu dùng --clause-id"
    )
    
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Số lượng kết quả trả về (mặc định: 3)"
    )
    
    parser.add_argument(
        "--clause-id",
        type=str,
        default=None,
        help="Filter theo clause_id (ví dụ: 'Dieu 3', 'Dieu 1', 'Chuong I'). Dùng cho metadata filtering."
    )
    
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="Filter theo document_id (ví dụ: 'Hop_dong_A')"
    )
    
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Filter theo một version cụ thể (ví dụ: 'v1' hoặc 'v2' hoặc 'A')"
    )
    
    parser.add_argument(
        "--versions",
        type=str,
        nargs="+",
        default=None,
        help="Danh sách versions để so sánh (ví dụ: v1 v2 hoặc A B). Mặc định: v1 v2"
    )
    
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Chỉ dùng metadata filtering, bỏ qua semantic search"
    )
    
    parser.add_argument(
        "--compare-versions",
        action="store_true",
        help="So sánh cùng một điều khoản giữa 2 version (yêu cầu --clause-id)"
    )
    
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=300,
        help="Độ dài preview nội dung (mặc định: 300)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LEGAL RAG - METADATA FILTERING & DUAL-VERSION RETRIEVER")
    print("=" * 80)
    
    # Khởi tạo retriever
    try:
        retriever = LegalRetriever()
    except Exception as e:
        print(f"\n[!] Error initializing retriever: {e}")
        sys.exit(1)
    
    # Xác định chế độ truy xuất
    if args.compare_versions:
        # === Chế độ SO SÁNH 2 VERSION ===
        if not args.clause_id:
            print("\n[!] Error: --clause-id is required for --compare-versions")
            sys.exit(1)
        
        try:
            comparison_result = retriever.search_clause_with_both_versions(
                clause_id=args.clause_id,
                document_id=args.doc_id,
                versions=args.versions
            )
            retriever.print_clause_comparison(comparison_result, preview_chars=args.preview_chars)
        except Exception as e:
            print(f"[!] Error during clause comparison: {e}")
            sys.exit(1)
    
    elif args.clause_id:
        # === Chế độ METADATA FILTERING ===
        try:
            # Xác định versions cần lấy
            target_versions = None
            if args.version:
                # Nếu người dùng chỉ định 1 version
                target_versions = [args.version]
            elif args.versions:
                # Nếu người dùng chỉ định danh sách versions
                target_versions = args.versions
            # Nếu không chỉ định, search_by_clause_id sẽ lấy tất cả versions
            
            results_by_version = retriever.search_by_clause_id(
                clause_id=args.clause_id,
                document_id=args.doc_id,
                versions=target_versions
            )
            retriever.print_results_by_version(results_by_version, preview_chars=args.preview_chars)
        except Exception as e:
            print(f"[!] Error during metadata filtering: {e}")
            sys.exit(1)
    
    else:
        # === Chế độ SEMANTIC SEARCH (mặc định) ===
        if not args.query:
            print("\n[!] Error: query is required for semantic search. Use --clause-id for metadata filtering.")
            sys.exit(1)
        
        try:
            results = retriever.search(
                query=args.query,
                k=args.k,
                document_id=args.doc_id,
                version=args.version,
                clause_id=None  # Không dùng clause-id filter cho semantic search
            )
            retriever.print_results(results, preview_chars=args.preview_chars)
        except Exception as e:
            print(f"[!] Error during semantic search: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()