#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DEMO: Truy xuat theo dieu khoan va hien thi so sanh v1 vs v2
Nhap: python demo_retrieval.py
Sau do nhap clause_id (vi du: Dieu 5)
"""

import sys
sys.path.insert(0, 'src')

from legal_rag.retrieval.retriever import LegalRetriever
from legal_rag.retrieval.output_formatter import RetrievalOutputFormatter


def print_side_by_side(v1_content, v2_content, clause_id):
    """In hai phien ban canh nhau"""
    print("\n" + "=" * 100)
    print(f"DIEU KHOAN: {clause_id}")
    print("=" * 100)
    
    # Chia text thanh dong
    v1_lines = v1_content.split('\n')
    v2_lines = v2_content.split('\n')
    
    # Tim dong toi da
    max_lines = max(len(v1_lines), len(v2_lines))
    
    # In header
    print(f"{'BAN GOC (v1)' : <48} | {'BAN SUA DOI (v2)' : <48}")
    print("-" * 100)
    
    # In tung dong canh nhau
    for i in range(max_lines):
        v1_line = v1_lines[i] if i < len(v1_lines) else ""
        v2_line = v2_lines[i] if i < len(v2_lines) else ""
        
        # Cat theo chieu rong
        v1_display = (v1_line[:45] + "...") if len(v1_line) > 45 else v1_line
        v2_display = (v2_line[:45] + "...") if len(v2_line) > 45 else v2_line
        
        print(f"{v1_display : <48} | {v2_display : <48}")
    
    print("=" * 100)


def main():
    print("\n" + "=" * 100)
    print("LEGAL RAG - DEMO TRY XUAT DIEU KHOAN")
    print("=" * 100)
    print("\nCac dieu khoan co san: Dieu 1, Dieu 2, Dieu 3, Dieu 4, Dieu 5, Dieu 6, Mo_dau")
    
    # Yeu cau nhap
    try:
        clause_id = input("\nNhap clause_id (vi du 'Dieu 5'): ").strip()
    except EOFError:
        # Neu chay tu pipe, doc tu argv hoac mac dinh
        import sys
        if len(sys.argv) > 1:
            clause_id = sys.argv[1]
        else:
            clause_id = "Dieu 5"
            print(f"(Mac dinh: {clause_id})")
    
    if not clause_id:
        print("[ERROR] Phai nhap clause_id!")
        return
    
    print(f"\n[*] Dang tro xuat {clause_id}...")
    
    try:
        # Khoi tao retriever va formatter
        retriever = LegalRetriever()
        formatter = RetrievalOutputFormatter()
        
        # Truy xuat du lieu
        comparison = retriever.search_clause_with_both_versions(
            clause_id=clause_id,
            versions=["v1", "v2"]
        )
        
        # Them vao formatter
        formatter.add_from_comparison_dict(comparison)
        
        # Kiem tra co du lieu hay khong
        if not comparison.get("comparison_ready"):
            print(f"\n[WARNING] Khong co du lieu day du cho {clause_id}")
            print(f"  - v1: {'YES' if comparison['versions'].get('v1') else 'NO'}")
            print(f"  - v2: {'YES' if comparison['versions'].get('v2') else 'NO'}")
            return
        
        # Lay du lieu dinh dang
        paired = formatter.get_paired_format()
        
        if clause_id not in paired:
            print(f"\n[ERROR] Khong tim thay {clause_id} trong ket qua!")
            return
        
        # Lay noi dung
        v1_content = paired[clause_id].get("Ban_goc", "")
        v2_content = paired[clause_id].get("Ban_sua_doi", "")
        
        # In ket qua canh nhau
        print_side_by_side(v1_content, v2_content, clause_id)
        
        # Hien thi thong tin them
        print("\n[INFO] Chi tiet:")
        detailed = formatter.get_detailed_format()
        if clause_id in detailed:
            print(f"  Ban goc (v1):")
            if "v1" in detailed[clause_id]:
                v1_info = detailed[clause_id]["v1"]
                print(f"    - Document: {v1_info.get('document_id', '?')}")
                print(f"    - Heading: {v1_info.get('heading', '?')}")
                print(f"    - Chunks: {v1_info.get('chunk_count', 1)}")
            
            print(f"  Ban sua doi (v2):")
            if "v2" in detailed[clause_id]:
                v2_info = detailed[clause_id]["v2"]
                print(f"    - Document: {v2_info.get('document_id', '?')}")
                print(f"    - Heading: {v2_info.get('heading', '?')}")
                print(f"    - Chunks: {v2_info.get('chunk_count', 1)}")
        
        print("\n[SUCCESS] Hoan tat!")
        
    except Exception as e:
        print(f"\n[ERROR] Co loi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
