#!/usr/bin/env python
"""
CLI script để thực hiện tìm kiếm vector trên Legal RAG Database.

Ví dụ sử dụng:
    python retrieve.py "Quy định về thanh toán"
    python retrieve.py "Quy định về thanh toán" --k 5
    python retrieve.py "Quy định về bảo hành" --doc-id "Hop_dong_A" --version "v2"
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
        description="Tìm kiếm đoạn hợp đồng liên quan dựa trên câu truy vấn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python retrieve.py "Quy định về thanh toán"
  python retrieve.py "Bảo hành" --k 5
  python retrieve.py "giá trị hợp đồng" --doc-id "Hop_dong_A" --version "v2"
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Câu truy vấn (ví dụ: 'Quy định về thanh toán')"
    )
    
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Số lượng kết quả trả về (mặc định: 3)"
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
        help="Filter theo version (ví dụ: 'v1' hoặc 'v2')"
    )
    
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=300,
        help="Độ dài preview nội dung (mặc định: 300)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LEGAL RAG - VECTOR RETRIEVER")
    print("=" * 80)
    
    # Khởi tạo retriever
    try:
        retriever = LegalRetriever()
    except Exception as e:
        print(f"\n[!] Error initializing retriever: {e}")
        sys.exit(1)
    
    # Thực hiện tìm kiếm
    try:
        results = retriever.search(
            query=args.query,
            k=args.k,
            document_id=args.doc_id,
            version=args.version
        )
        
        # In kết quả
        retriever.print_results(results, preview_chars=args.preview_chars)
        
    except Exception as e:
        print(f"\n[!] Error during search: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
