import argparse
import textwrap
from typing import Any, Dict, List, Optional

from legal_rag.retrieval import LegalRetriever


def add_search_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("query", help='Cau truy van, vi du: "Quy dinh ve thanh toan"')
    parser.add_argument("-k", "--top-k", type=int, default=3, help="So ket qua muon lay")
    parser.add_argument("--doc-id", help="Loc theo doc_id")
    parser.add_argument("--version", help="Loc theo version")
    parser.add_argument("--logical-id", help="Loc theo logical_id")
    return parser


def add_search_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("search", help="Tim kiem semantic top-K trong ChromaDB")
    return add_search_arguments(parser)


def run_search(args: argparse.Namespace) -> List[Dict[str, Any]]:
    filter_dict = build_filter(args)
    retriever = LegalRetriever()
    results = retriever.retrieve(
        query=args.query,
        k=args.top_k,
        filter_dict=filter_dict,
    )
    print_search_results(
        query=args.query,
        top_k=args.top_k,
        filter_dict=filter_dict,
        results=results,
    )
    return results


def build_filter(args: argparse.Namespace) -> Optional[Dict[str, str]]:
    filter_dict: Dict[str, str] = {}
    if args.doc_id:
        filter_dict["doc_id"] = args.doc_id
    if args.version:
        filter_dict["version"] = args.version
    if args.logical_id:
        filter_dict["logical_id"] = args.logical_id
    return filter_dict or None


def print_search_results(
    query: str,
    top_k: int,
    filter_dict: Optional[Dict[str, str]],
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
        print(f"Logical ID : {metadata.get('logical_id', 'N/A')}")
        print(f"Chunk Index: {metadata.get('chunk_index', 'N/A')}")
        print("Content    :")
        print(textwrap.fill(result["content"], width=100, initial_indent="  ", subsequent_indent="  "))
        print("-" * 100)


def build_direct_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Semantic search over legal chunks")
    return add_search_arguments(parser)


def main(argv: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    parser = build_direct_parser()
    args = parser.parse_args(argv)
    return run_search(args)


if __name__ == "__main__":
    main()
