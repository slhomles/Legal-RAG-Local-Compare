import sys
import os
import re
import unicodedata
from typing import Any, Dict, List

# Them thu muc src vao sys.path de import duoc package legal_rag
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from legal_rag.retrieval import LegalRetriever
    from legal_rag.retrieval.context_pairing import ContextPairer
except ImportError as e:
    print(f"[!] Loi import: {e}")
    print("[!] Hay chac chan ban dang chay script tu thu muc goc cua du an.")
    sys.exit(1)

def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

def slugify(value: str) -> str:
    folded = strip_accents(value).lower()
    folded = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return folded

def main():
    print("="*60)
    print("DEMO TRUY XUAT DIEU KHOAN DOI CHIEU")
    print("="*60)
    
    clause_input = input("[?] Nhap dieu khoan muon xem (vi du: Dieu 3, Dieu 5): ").strip()
    if not clause_input:
        print("[!] Vui long nhap ten dieu khoan.")
        return

    logical_id = slugify(clause_input)
    print(f"[*] Dang truy xuat cho ID: {logical_id}...")

    # Khoi tao Retriever va ContextPairer
    retriever = LegalRetriever()
    pairer = ContextPairer()

    # Thuc hien truy xuat voi filter logical_id
    # Chung ta dung query rong vi chung ta chi quan tam den Metadata Filter o day
    filter_dict = {"logical_id": logical_id}
    
    try:
        # Lay top k cao de dam bao lay duoc tat ca cac chunk cua dieu do tren cac ban
        results = retriever.retrieve(query=clause_input, k=10, filter_dict=filter_dict)
        
        if not results:
            print(f"[!] Khong tim thay du lieu cho {clause_input}.")
            return

        paired_data = pairer.pair_chunks(results)

        print("\n" + "="*60)
        print(f"KET QUA DOI CHIEU: {clause_input.upper()}")
        print("="*60)

        # Lay danh sach cac phien ban co san
        clause_versions = paired_data.get(logical_id, {})
        
        if not clause_versions:
            print("[!] Khong co du lieu pairing.")
            return

        # Sap xep phien ban v1, v2 cho dep
        sorted_versions = sorted(clause_versions.keys())

        for version in sorted_versions:
            content = clause_versions[version]
            version_label = "BAN GOC" if version == "v1" else f"BAN SUA DOI ({version})"
            
            print(f"\n>>> {version_label}:")
            print("-" * 30)
            print(content)
            print("-" * 30)

    except Exception as e:
        print(f"[!] Da xay ra loi khi truy xuat: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
