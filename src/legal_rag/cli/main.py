import argparse

def main() -> None:
    from legal_rag.cli.search import add_search_parser

    parser = argparse.ArgumentParser(description="Legal RAG CLI")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("ingest", help="Chay pipeline ingestion")
    add_search_parser(subparsers)

    args = parser.parse_args()

    if args.command in (None, "ingest"):
        from legal_rag.cli.ingestion import main as run_ingestion

        run_ingestion()
        return

    if args.command == "search":
        from legal_rag.cli.search import run_search

        run_search(args)


if __name__ == "__main__":
    main()
