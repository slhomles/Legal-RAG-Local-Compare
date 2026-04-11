"""
Semantic search over legal chunks trong ChromaDB.

Su dung:
    python scripts/search.py "Quy dinh ve thanh toan" -k 5
    python scripts/search.py "query" -k 5 --doc-id Hop_dong_A --version v1
    python scripts/search.py "query" -k 5 --clause-id "dieu_3" --pair
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.retrieval import LegalRetriever
from legal_rag.retrieval.context_pairing import ContextPairer


def build_filter(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    conditions: List[Dict[str, Any]] = []

    if args.doc_id:
        conditions.append({"doc_id": args.doc_id})

    if args.clause_id:
        conditions.append({"logical_id": args.clause_id})

    if args.version:
        versions = [v.strip() for v in args.version.split(",") if v.strip()]
        if len(versions) == 1:
            conditions.append({"version": versions[0]})
        elif len(versions) > 1:
            conditions.append({"version": {"$in": versions}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def print_paired_results(paired_results: Dict[str, Dict[str, str]]) -> None:
    separator = "=" * 100
    print(separator)
    print("CONTEXT PAIRING JSON RESULTS")
    print(separator)
    print(json.dumps(paired_results, indent=2, ensure_ascii=False))
    print(separator)


def print_search_results(
    query: str,
    top_k: int,
    filter_dict: Optional[Dict[str, Any]],
    results: List[Dict[str, Any]],
) -> None:
    separator = "=" * 100
    print(separator)
    print("SEMANTIC SEARCH RESULTS")
    print(separator)
    print(f"Query      : {query}")
    print(f"Top-K      : {top_k}")
    print(f"Filters    : {filter_dict or 'None'}")
    print(f"Retrieved  : {len(results)}")
    print(separator)

    if not results:
        print("Khong tim thay chunk phu hop.")
        print(separator)
        return

    for result in results:
        metadata = result["metadata"]
        distance = result.get("distance")
        distance_text = f"{distance:.6f}" if isinstance(distance, (int, float)) else "N/A"

        print(f"[{result['rank']}] {metadata.get('doc_id', 'Unknown')} | version={metadata.get('version', 'N/A')} | distance={distance_text}")
        print(f"ID         : {result['id']}")
        print(f"Heading    : {metadata.get('chunk_heading', 'N/A')}")
        print(f"Hierarchy  : {metadata.get('hierarchy_path', 'N/A')}")
        print(f"Clause ID  : {metadata.get('logical_id', 'N/A')}")
        print(f"Chunk Index: {metadata.get('chunk_index', 'N/A')}")
        print("Content    :")
        print(textwrap.fill(result["content"], width=100, initial_indent="  ", subsequent_indent="  "))
        print("-" * 100)


def main(argv: Optional[List[str]] = None) -> Union[List[Dict[str, Any]], Dict[str, Dict[str, str]]]:
    parser = argparse.ArgumentParser(description="Semantic search over legal chunks")
    parser.add_argument("query", help='Cau truy van, vi du: "Quy dinh ve thanh toan"')
    parser.add_argument("-k", "--top-k", type=int, default=3, help="So ket qua muon lay")
    parser.add_argument("--doc-id", help="Loc theo doc_id")
    parser.add_argument("--version", help="Loc theo version (vd: v1,v2)")
    parser.add_argument("--clause-id", help="Loc theo dieu khoan (logical_id)")
    parser.add_argument("--pair", action="store_true", help="Ghep cap ket qua theo dieu khoan va phien ban")

    args = parser.parse_args(argv)
    filter_dict = build_filter(args)

    retriever = LegalRetriever()
    results = retriever.retrieve(query=args.query, k=args.top_k, filter_dict=filter_dict)

    if args.pair:
        pairer = ContextPairer()
        paired_results = pairer.pair_chunks(results)
        print_paired_results(paired_results)
        return paired_results
    else:
        print_search_results(query=args.query, top_k=args.top_k, filter_dict=filter_dict, results=results)
        return results


if __name__ == "__main__":
    main()
