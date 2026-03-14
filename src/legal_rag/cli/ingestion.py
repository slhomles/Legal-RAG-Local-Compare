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

        # Extract version from filename (e.g., "Hop_dong_A_v1.docx" -> "v1")
        filename = file_path.name.lower()
        version = "v1"  # default
        if "_v" in filename:
            # Extract "v1", "v2", etc.
            version_part = filename.split("_v")[-1].split(".")[0]
            version = f"v{version_part}"

        chunks = doc_processor.process_file(str(file_path), version=version)
        print(f"  + Da chia thanh {len(chunks)} doan (chunks). Version: {version}")
        
        if chunks:
            first_chunk_meta = chunks[0]["metadata"]
            doc_id = first_chunk_meta.get("document_id", "?")
            version = first_chunk_meta.get("version", "?")
            print(f"  + Document ID: {doc_id}, Version: {version}")

        if not chunks:
            continue

        vector_store.add_documents(chunks)
        total_chunks += len(chunks)

    print(f"\n[+] HOAN THANH. Tong so doan da xu ly va luu: {total_chunks}")
    print("=" * 50)


if __name__ == "__main__":
    main()
