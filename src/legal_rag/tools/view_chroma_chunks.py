import argparse
import io
import shutil
import sqlite3
import sys
import textwrap
from pathlib import Path

from legal_rag.config import CHROMA_DB_DIR

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _terminal_width() -> int:
    return max(88, min(shutil.get_terminal_size((100, 20)).columns, 140))


def _rule(char: str = "-") -> str:
    return char * _terminal_width()


def _print_section(title: str) -> None:
    print("=" * _terminal_width())
    print(title)
    print("=" * _terminal_width())


def _format_filters(
    doc_id: str | None,
    version: str | None,
    logical_id: str | None,
    contains: str | None,
) -> str:
    filters = []
    if doc_id:
        filters.append(f"doc_id={doc_id}")
    if version:
        filters.append(f"version={version}")
    if logical_id:
        filters.append(f"logical_id={logical_id}")
    if contains:
        filters.append(f"contains={contains}")
    return " | ".join(filters) if filters else "(none)"


def _truncate_content(content: str, max_chars: int) -> str:
    preview = content.strip()
    if len(preview) <= max_chars:
        return preview
    return preview[:max_chars].rstrip() + "..."


def _render_preview_block(content: str, max_chars: int) -> str:
    preview = _truncate_content(content, max_chars)
    width = max(40, _terminal_width() - 6)
    rendered_lines = []
    for raw_line in preview.splitlines() or [""]:
        line = raw_line.strip()
        if not line:
            if rendered_lines and rendered_lines[-1] != "":
                rendered_lines.append("")
            continue
        rendered_lines.extend(textwrap.wrap(line, width=width) or [""])

    if not rendered_lines:
        rendered_lines = ["(empty)"]

    return "\n".join(f"  {line}" if line else "" for line in rendered_lines)


def _print_chunk(row_index: int, row: tuple, preview_chars: int) -> None:
    chunk_id, doc_id, version, chunk_index, heading, hierarchy_path, logical_id, content = row
    print(_rule())
    print(f"[{row_index}] {chunk_id}")
    print(f"  doc_id         : {doc_id}")
    print(f"  version        : {version}")
    print(f"  chunk_index    : {chunk_index}")
    print(f"  heading        : {heading}")
    print(f"  hierarchy_path : {hierarchy_path}")
    print(f"  logical_id     : {logical_id}")
    print("  content:")
    print(_render_preview_block(content, preview_chars))


def _build_where_clause(
    doc_id: str | None,
    version: str | None,
    logical_id: str | None,
    contains: str | None,
) -> tuple[list[str], list]:
    where = ["doc.key = 'chroma:document'"]
    params: list = []

    if doc_id:
        where.append("doc_meta.string_value = ?")
        params.append(doc_id)

    if version:
        where.append("version_meta.string_value = ?")
        params.append(version)

    if logical_id:
        where.append("logical_meta.string_value = ?")
        params.append(logical_id)

    if contains:
        where.append("LOWER(doc.string_value) LIKE ?")
        params.append(f"%{contains.lower()}%")

    return where, params


def _build_query(
    doc_id: str | None,
    version: str | None,
    logical_id: str | None,
    contains: str | None,
) -> tuple[str, list]:
    where, params = _build_where_clause(doc_id, version, logical_id, contains)

    query = f"""
        SELECT
            emb.embedding_id AS chunk_id,
            COALESCE(doc_meta.string_value, 'unknown') AS doc_id,
            COALESCE(version_meta.string_value, 'unknown') AS version,
            COALESCE(chunk_index_meta.int_value, -1) AS chunk_index,
            COALESCE(heading_meta.string_value, 'unknown') AS chunk_heading,
            COALESCE(path_meta.string_value, 'unknown') AS hierarchy_path,
            COALESCE(logical_meta.string_value, 'unknown') AS logical_id,
            COALESCE(doc.string_value, '') AS content
        FROM embedding_metadata AS doc
        JOIN embeddings AS emb
            ON emb.id = doc.id
        LEFT JOIN embedding_metadata AS doc_meta
            ON doc_meta.id = doc.id AND doc_meta.key = 'doc_id'
        LEFT JOIN embedding_metadata AS version_meta
            ON version_meta.id = doc.id AND version_meta.key = 'version'
        LEFT JOIN embedding_metadata AS chunk_index_meta
            ON chunk_index_meta.id = doc.id AND chunk_index_meta.key = 'chunk_index'
        LEFT JOIN embedding_metadata AS heading_meta
            ON heading_meta.id = doc.id AND heading_meta.key = 'chunk_heading'
        LEFT JOIN embedding_metadata AS path_meta
            ON path_meta.id = doc.id AND path_meta.key = 'hierarchy_path'
        LEFT JOIN embedding_metadata AS logical_meta
            ON logical_meta.id = doc.id AND logical_meta.key = 'logical_id'
        WHERE {" AND ".join(where)}
        ORDER BY doc_meta.string_value, version_meta.string_value, chunk_index_meta.int_value, emb.embedding_id
    """
    return query, params


def _count_total_chunks(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM embedding_metadata
        WHERE key = 'chroma:document'
        """
    ).fetchone()
    return int(row[0]) if row else 0


def _count_matching_chunks(
    conn: sqlite3.Connection,
    doc_id: str | None,
    version: str | None,
    logical_id: str | None,
    contains: str | None,
) -> int:
    where, params = _build_where_clause(doc_id, version, logical_id, contains)
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM embedding_metadata AS doc
        LEFT JOIN embedding_metadata AS doc_meta
            ON doc_meta.id = doc.id AND doc_meta.key = 'doc_id'
        LEFT JOIN embedding_metadata AS version_meta
            ON version_meta.id = doc.id AND version_meta.key = 'version'
        LEFT JOIN embedding_metadata AS logical_meta
            ON logical_meta.id = doc.id AND logical_meta.key = 'logical_id'
        WHERE {" AND ".join(where)}
        """,
        params,
    ).fetchone()
    return int(row[0]) if row else 0


def _print_stats(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT
            COALESCE(doc_meta.string_value, 'unknown') AS doc_id,
            COALESCE(version_meta.string_value, 'unknown') AS version,
            COUNT(*) AS n
        FROM embedding_metadata AS doc
        LEFT JOIN embedding_metadata AS doc_meta
            ON doc_meta.id = doc.id AND doc_meta.key = 'doc_id'
        LEFT JOIN embedding_metadata AS version_meta
            ON version_meta.id = doc.id AND version_meta.key = 'version'
        WHERE doc.key = 'chroma:document'
        GROUP BY doc_meta.string_value, version_meta.string_value
        ORDER BY doc_id, version
        """
    ).fetchall()

    total = sum(row[2] for row in rows)
    _print_section("CHUNK STATS")
    print(f"Total chunks : {total}")
    print(f"Rows         : {len(rows)} doc/version groups")
    print()

    if not rows:
        print("No chunks stored yet.")
        print()
        return

    doc_width = max(len("doc_id"), min(max(len(row[0]) for row in rows), 60))
    version_width = max(len("version"), max(len(row[1]) for row in rows))
    count_width = max(len("chunks"), max(len(str(row[2])) for row in rows))

    print(
        f"{'doc_id':<{doc_width}}  "
        f"{'version':<{version_width}}  "
        f"{'chunks':>{count_width}}"
    )
    print(_rule())
    for doc_name, version, count in rows:
        print(
            f"{doc_name:<{doc_width}}  "
            f"{version:<{version_width}}  "
            f"{count:>{count_width}}"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="View chunks stored in ChromaDB")
    parser.add_argument("--doc-id", help="Filter by doc_id metadata")
    parser.add_argument("--version", help="Filter by version metadata")
    parser.add_argument("--logical-id", help="Filter by logical_id metadata")
    parser.add_argument("--contains", help="Filter chunks whose content contains this text")
    parser.add_argument(
        "-n",
        "--num-chunks",
        "--limit",
        dest="limit",
        type=int,
        default=20,
        help="Number of chunks to display (default: 20)",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=320,
        help="Preview length per chunk content",
    )
    parser.add_argument("--stats", action="store_true", help="Print chunk counts by doc/version")
    args = parser.parse_args()

    db_path = Path(CHROMA_DB_DIR) / "chroma.sqlite3"
    if not db_path.exists():
        raise SystemExit(f"Chroma DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        if args.stats:
            _print_stats(conn)

        total_chunks_in_db = _count_total_chunks(conn)
        matching_chunks = _count_matching_chunks(
            conn,
            args.doc_id,
            args.version,
            args.logical_id,
            args.contains,
        )
        query, params = _build_query(args.doc_id, args.version, args.logical_id, args.contains)
        query += " LIMIT ?"
        params.append(args.limit)
        rows = conn.execute(query, params).fetchall()

        _print_section("CHUNK PREVIEW")
        print(f"DB            : {db_path}")
        print(f"Total chunks  : {total_chunks_in_db}")
        print(f"Matching      : {matching_chunks}")
        print(f"Showing       : {len(rows)}")
        print(f"Display limit : {args.limit}")
        print(f"Filters       : {_format_filters(args.doc_id, args.version, args.logical_id, args.contains)}")
        print()

        if not rows:
            print("No chunks matched the filter.")
            return

        for idx, row in enumerate(rows, start=1):
            _print_chunk(idx, row, args.preview_chars)
        print(_rule())
    finally:
        conn.close()


if __name__ == "__main__":
    main()
