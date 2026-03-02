import argparse

from legal_rag.cli.ingestion import main as run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Legal RAG CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="ingest",
        choices=["ingest"],
        help="Lenh can chay",
    )
    args = parser.parse_args()

    if args.command == "ingest":
        run_ingestion()


if __name__ == "__main__":
    main()
