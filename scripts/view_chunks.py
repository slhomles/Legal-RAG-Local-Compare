"""
Inspect ChromaDB contents: thong ke chunks, xem noi dung.

Su dung:
    python scripts/view_chunks.py --stats
    python scripts/view_chunks.py --doc-id Hop_dong_A --version v1 -n 10
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.tools.view_chroma_chunks import main

if __name__ == "__main__":
    main()
