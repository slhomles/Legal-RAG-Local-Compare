import argparse
import sqlite3
import io
import sys
from pathlib import Path

from legal_rag.config import CHROMA_DB_DIR

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _build_query(doc_id: str | None, contains: str | None) -> tuple[str, list]:
    where = ["doc.key = 'chroma:document'"]
    params: list = []

    if doc_id:
        where.append("doc_meta.string_value = ?")
        params.append(doc_id)

    if contains:
        where.append("LOWER(doc.string_value) LIKE ?")
        params.append(f"%{contains.lower()}%")

    query = f"""
        SELECT
            doc.id AS chunk_id,
            COALESCE(document_meta.string_value, 'unknown') AS document_id,
            COALESCE(version_meta.string_value, 'unknown') AS version,
            COALESCE(clause_meta.string_value, 'unknown') AS clause_id,
            COALESCE(heading_meta.string_value, 'unknown') AS chunk_heading,
            COALESCE(doc.string_value, '') AS content
        FROM embedding_metadata AS doc
        LEFT JOIN embedding_metadata AS document_meta
            ON document_meta.id = doc.id AND document_meta.key = 'document_id'
        LEFT JOIN embedding_metadata AS version_meta
            ON version_meta.id = doc.id AND version_meta.key = 'version'
        LEFT JOIN embedding_metadata AS clause_meta
            ON clause_meta.id = doc.id AND clause_meta.key = 'clause_id'
        LEFT JOIN embedding_metadata AS heading_meta
            ON heading_meta.id = doc.id AND heading_meta.key = 'chunk_heading'
        WHERE {" AND ".join(where)}
        ORDER BY doc.id
    """
    return query, params


def _print_stats(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT
            COALESCE(document_meta.string_value, 'unknown') AS document_id,
            COALESCE(version_meta.string_value, 'unknown') AS version,
            COUNT(*) AS n
        FROM embedding_metadata AS doc
        LEFT JOIN embedding_metadata AS document_meta
            ON document_meta.id = doc.id AND document_meta.key = 'document_id'
        LEFT JOIN embedding_metadata AS version_meta
            ON version_meta.id = doc.id AND version_meta.key = 'version'
        WHERE doc.key = 'chroma:document'
        GROUP BY document_meta.string_value, version_meta.string_value
        ORDER BY n DESC, document_id
        """
    ).fetchall()

    total = sum(r[2] for r in rows)
    print("=" * 70)
    print("CHUNK STATS (Document ID | Version | Count)")
    print("=" * 70)
    print(f"Total chunks: {total}")
    print()
    print(f"{'Document ID':<35} {'Version':<15} {'Count':<10}")
    print("-" * 70)
    for doc_id, version, count in rows:
        print(f"{doc_id:<35} {version:<15} {count:<10}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View chunks stored in ChromaDB")
    parser.add_argument("--doc-id", help="Filter by doc_id metadata")
    parser.add_argument("--contains", help="Filter chunks whose content contains this text")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to print")
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=320,
        help="Preview length per chunk content",
    )
    parser.add_argument("--stats", action="store_true", help="Print chunk counts by doc")
    args = parser.parse_args()

    db_path = Path(CHROMA_DB_DIR) / "chroma.sqlite3"
    if not db_path.exists():
        raise SystemExit(f"Chroma DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        if args.stats:
            _print_stats(conn)

        query, params = _build_query(args.doc_id, args.contains)
        query += " LIMIT ?"
        params.append(args.limit)
        rows = conn.execute(query, params).fetchall()

        print("=" * 70)
        print("CHUNK PREVIEW")
        print("=" * 70)
        print(f"DB: {db_path}")
        print(f"Rows returned: {len(rows)}")
        print()

        if not rows:
            print("No chunks matched the filter.")
            return

        for idx, (chunk_id, document_id, version, clause_id, heading, content) in enumerate(rows, start=1):
            preview = content[: args.preview_chars]
            if len(content) > args.preview_chars:
                preview += "..."

            print(f"[{idx}] chunk_id={chunk_id}")
            print(f"    document_id={document_id}")
            print(f"    version={version}")
            print(f"    clause_id={clause_id}")
            print(f"    chunk_heading={heading}")
            print(f"    content={preview}")
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
