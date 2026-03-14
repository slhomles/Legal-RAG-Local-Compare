"""
CLI script để trích xuất và định hình kết quả retrieval thành JSON
Sử dụng: python retrieve_and_format.py [--clause-id CLAUSE_ID] [--output-file FILE.json] [--detailed]
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from legal_rag.retrieval.retriever import LegalRetriever
from legal_rag.retrieval.output_formatter import RetrievalOutputFormatter


def retrieve_all_clauses() -> RetrievalOutputFormatter:
    """
    Trích xuất TẤT CẢ các điều khoản và ghép cặp phiên bản
    
    Returns:
        RetrievalOutputFormatter đã được điền dữ liệu
    """
    print("\n" + "="*80)
    print("TRÍCH XUẤT TOÀN BỘ ĐIỀU KHOẢN")
    print("="*80)
    
    retriever = LegalRetriever()
    formatter = RetrievalOutputFormatter()
    
    # Danh sách các điều khoản cần trích xuất
    # Có thể truy vấn từ database để động hóa
    clause_ids = [
        "Dieu 1", "Dieu 2", "Dieu 3", "Dieu 4", "Dieu 5", "Dieu 6", "Mo_dau"
    ]
    
    print(f"\n[*] Trích xuất {len(clause_ids)} điều khoản...\n")
    
    for clause_id in clause_ids:
        print(f"  ⏳ Đang xử lý {clause_id}...")
        
        try:
            # Lấy kết quả so sánh hai phiên bản
            comparison = retriever.search_clause_with_both_versions(
                clause_id=clause_id,
                versions=["v1", "v2"]
            )
            
            # Thêm vào formatter
            formatter.add_from_comparison_dict(comparison)
            
            # Log trạng thái
            status = "✅" if comparison.get("comparison_ready") else "⚠️"
            print(f"     {status} {clause_id}: comparison_ready={comparison.get('comparison_ready')}")
        
        except Exception as e:
            print(f"     ❌ {clause_id}: {str(e)[:50]}")
    
    return formatter


def retrieve_specific_clause(clause_id: str) -> RetrievalOutputFormatter:
    """
    Trích xuất một điều khoản cụ thể
    
    Args:
        clause_id: ID của điều khoản (ví dụ: "Dieu 3")
    
    Returns:
        RetrievalOutputFormatter đã được điền dữ liệu
    """
    print("\n" + "="*80)
    print(f"TRÍCH XUẤT ĐIỀU KHOẢN: {clause_id}")
    print("="*80)
    
    retriever = LegalRetriever()
    formatter = RetrievalOutputFormatter()
    
    print(f"\n[*] Trích xuất {clause_id}...")
    
    comparison = retriever.search_clause_with_both_versions(
        clause_id=clause_id,
        versions=["v1", "v2"]
    )
    
    formatter.add_from_comparison_dict(comparison)
    
    print(f"✅ Hoàn thành\n")
    
    return formatter


def main():
    parser = argparse.ArgumentParser(
        description="Trích xuất và định hình kết quả retrieval thành JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Trích xuất tất cả điều khoản
  python retrieve_and_format.py
  
  # Trích xuất một điều khoản cụ thể
  python retrieve_and_format.py --clause-id "Dieu 3"
  
  # Lưu với định dạng chi tiết
  python retrieve_and_format.py --detailed --output-file comparison.json
  
  # Trích xuất và in định dạng ghép cặp
  python retrieve_and_format.py --paired
        """
    )
    
    parser.add_argument(
        "--clause-id",
        type=str,
        default=None,
        help='Trích xuất một điều khoản cụ thể (ví dụ: "Dieu 3")'
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        default="comparison_output.json",
        help="Đường dẫn file JSON để lưu kết quả (mặc định: comparison_output.json)"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Lưu với metadata đầy đủ (document_id, heading, chunk_count, v.v.)"
    )
    
    parser.add_argument(
        "--paired",
        action="store_true",
        help="In định dạng ghép cặp (Bản_gốc/Bản_sửa_đổi) thay vì chi tiết"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Không lưu file JSON, chỉ in ra màn hình"
    )
    
    args = parser.parse_args()
    
    # Trích xuất dữ liệu
    if args.clause_id:
        formatter = retrieve_specific_clause(args.clause_id)
    else:
        formatter = retrieve_all_clauses()
    
    # In kết quả
    detailed = args.detailed and not args.paired
    formatter.display(detailed=detailed)
    
    # Hiển thị thống kê
    summary = formatter.get_comparison_summary()
    print("\n" + "="*80)
    print("THỐNG KÊ KẾT QUẢ")
    print("="*80)
    print(f"  📊 Tổng số điều khoản: {summary['total_clauses']}")
    print(f"  ✅ Có cả hai phiên bản: {summary['clauses_with_both_versions']}")
    if summary['clauses_missing_v1']:
        print(f"  ⚠️  Thiếu v1: {', '.join(summary['clauses_missing_v1'])}")
    if summary['clauses_missing_v2']:
        print(f"  ⚠️  Thiếu v2: {', '.join(summary['clauses_missing_v2'])}")
    print(f"  🔄 Sẵn sàng so sánh: {'✅ CÓ' if summary['comparison_ready'] else '❌ KHÔNG'}")
    print("="*80 + "\n")
    
    # Lưu file JSON
    if not args.no_save:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        formatter.save_json(str(output_path), detailed=args.detailed)
        
        # Hiển thị thông tin file
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"💾 File đã lưu: {output_path}")
            print(f"   Kích thước: {file_size:,} bytes")
            print(f"   Định dạng: {'Chi tiết' if args.detailed else 'Ghép cặp'}\n")


if __name__ == "__main__":
    main()
