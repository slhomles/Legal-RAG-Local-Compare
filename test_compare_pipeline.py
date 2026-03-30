import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from legal_rag.generation.comparator import LegalComparator
from legal_rag.retrieval.retriever import LegalRetriever


def main():
    retriever = LegalRetriever()
    comparator = LegalComparator()

    document_id = "Hop_dong_A"
    clause_id = "Dieu 3"

    result = comparator.compare_clause_with_retrieval(
        retriever=retriever,
        document_id=document_id,
        clause_id=clause_id,
        k=4,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()