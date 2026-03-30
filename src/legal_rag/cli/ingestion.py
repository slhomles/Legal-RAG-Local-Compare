import io
import sys
from pathlib import Path

from legal_rag.config import RAW_DATA_DIR
from legal_rag.db.vector_store import VectorStoreManager
from legal_rag.ingest.document_processor import DocumentProcessor


if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def parse_document_info(file_name: str) -> tuple[str, str]:
    """
    Ví dụ:
    Hop_dong_A_v1.docx -> ("Hop_dong_A", "A")
    Hop_dong_A_v2.docx -> ("Hop_dong_A", "B")
    """
    stem = Path(file_name).stem

    if stem.endswith("_v1"):
        return stem[:-3], "A"
    if stem.endswith("_v2"):
        return stem[:-3], "B"

    return stem, "A"


def main() -> None:
    print("=" * 50)
    print("BAT DAU CHAY PIPELINE NHAP DU LIEU (INGESTION)")
    print("=" * 50)

    raw_dir = Path(RAW_DATA_DIR)
    docx_files = sorted(raw_dir.glob("*.docx"))

    if not docx_files:
        print(f"[!] Khong tim thay file .docx nao trong thu muc {RAW_DATA_DIR}")
        print("[!] Vui long chep tai lieu mau vao thu muc nay va chay lai.")
        return

    print(f"[*] Tim thay {len(docx_files)} tai lieu de xu ly.")

    doc_processor = DocumentProcessor()
    vector_store = VectorStoreManager()

    total_chunks = 0
    for file_path in docx_files:
        print(f"\n>> Dang xu ly file: {file_path.name}")
        document_id, version = parse_document_info(file_path.name)
        chunks = doc_processor.process_file(
            str(file_path),
            document_id=document_id,
            version=version
        )
        print(f"  + Da chia thanh {len(chunks)} doan (chunks).")

        if not chunks:
            continue

        vector_store.add_documents(chunks)
        total_chunks += len(chunks)

    print(f"\n[+] HOAN THANH. Tong so doan da xu ly va luu: {total_chunks}")
    print("=" * 50)


if __name__ == "__main__":
    main()
