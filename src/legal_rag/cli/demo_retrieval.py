import io
import sys

from legal_rag.retrieval.retriever import LegalRetriever


if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main():
    print("=" * 80)
    print("DEMO TRUY SUAT DIEU KHOAN")
    print("=" * 80)

    document_id = input("Nhap document_id (vi du: Hop_dong_A): ").strip()
    clause_id = input("Nhap dieu khoan (vi du: Dieu 5): ").strip()

    retriever = LegalRetriever()
    result = retriever.build_paired_context(document_id=document_id, clause_id=clause_id)

    normalized_clause = next(iter(result.keys()))
    original_text = result[normalized_clause]["Bản_gốc"]
    revised_text = result[normalized_clause]["Bản_sửa_đổi"]

    print("\n" + "=" * 80)
    print(f"{normalized_clause} - BAN GOC")
    print("=" * 80)
    print(original_text if original_text else "[Khong tim thay noi dung]")

    print("\n" + "=" * 80)
    print(f"{normalized_clause} - BAN SUA DOI")
    print("=" * 80)
    print(revised_text if revised_text else "[Khong tim thay noi dung]")


if __name__ == "__main__":
    main()