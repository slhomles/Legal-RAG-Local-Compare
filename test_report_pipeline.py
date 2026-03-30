import io
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from legal_rag.generation.comparator import LegalComparator
from legal_rag.retrieval.retriever import LegalRetriever


def main():
    retriever = LegalRetriever()
    comparator = LegalComparator()

    result = comparator.build_compare_report(
        retriever=retriever,
        document_id="Hop_dong_A",
        clause_ids=["Dieu 1", "Dieu 2", "Dieu 3", "Dieu 4"],
        k=4,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()