"""
Script in ra RAW phan hoi tu Ollama cho tung dieu khoan.

Dung de kiem tra xem LLM (qwen2.5:1.5b) co tra loi dung format ma
comparator._parse_changes() mong doi hay khong.

Su dung:
    python scripts/debug_llm_response.py
    python scripts/debug_llm_response.py --doc-id Hop_dong_A --old v1 --new v2
    python scripts/debug_llm_response.py --clause-id dieu_3
    python scripts/debug_llm_response.py --out output/llm_raw_responses.txt
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from legal_rag.generation.comparator import DocumentComparator


SEP_THICK = "=" * 72
SEP_THIN = "-" * 72


def render_report(result: dict, max_chars: int) -> str:
    doc_id = result["doc_id"]
    ver_old = result["version_old"]
    ver_new = result["version_new"]
    clauses = result["clauses"]
    new_clauses = result.get("new_clauses", [])
    removed_clauses = result.get("removed_clauses", [])

    items = list(clauses.items())
    total = len(items)

    lines = [
        SEP_THICK,
        f"  DEBUG: RAW OLLAMA RESPONSES",
        f"  Tai lieu : {doc_id}   |   So sanh: {ver_old} -> {ver_new}",
        f"  Tong dieu khoan: {total}",
        SEP_THICK,
        "",
    ]

    for i, (clause_id, info) in enumerate(items, 1):
        heading = info.get("heading") or clause_id
        raw = info.get("raw_llm_response", "") or ""
        raw_len = len(raw)
        changes = info.get("changes", [])
        types = [c.get("type", "?") for c in changes]
        guardrail_ok = info.get("guardrail_ok", True)
        violations = info.get("guardrail_violations", [])

        if clause_id in new_clauses:
            origin = "MOI THEM (khong goi LLM)"
        elif clause_id in removed_clauses:
            origin = "BI XOA (khong goi LLM)"
        else:
            origin = "CHUNG (co goi LLM)"

        lines += [
            SEP_THICK,
            f"  [{i}/{total}]  {heading}   ({clause_id})",
            f"  Phan loai    : {origin}",
            SEP_THIN,
            f"  Guardrail OK : {guardrail_ok}",
            f"  Violations   : {violations if violations else '[]'}",
            f"  Parsed changes: {len(changes)}   (types: {types})",
            SEP_THIN,
            f"  RAW OLLAMA RESPONSE  ({raw_len} chars)",
            SEP_THIN,
        ]

        if raw_len == 0:
            lines.append("  (khong co — dieu khoan nay khong goi LLM)")
        else:
            display = raw if max_chars <= 0 else raw[:max_chars]
            lines.append(display)
            if max_chars > 0 and raw_len > max_chars:
                lines.append(f"... [cat bot {raw_len - max_chars} ky tu]")

        lines += [SEP_THICK, ""]

    lines += [
        SEP_THICK,
        f"  TOM TAT",
        SEP_THIN,
        f"  Dieu khoan moi them  : {new_clauses if new_clauses else '[]'}",
        f"  Dieu khoan bi xoa    : {removed_clauses if removed_clauses else '[]'}",
        SEP_THICK,
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="In raw Ollama response cho tung dieu khoan de debug"
    )
    parser.add_argument("--doc-id", default="Hop_dong_A", help="ID tai lieu")
    parser.add_argument("--old", default="v1", help="Phien ban cu")
    parser.add_argument("--new", default="v2", help="Phien ban moi")
    parser.add_argument("-k", type=int, default=20, help="So chunk toi da truy xuat")
    parser.add_argument(
        "--clause-id",
        default=None,
        help="Chi chay mot dieu khoan cu the (vd: dieu_3)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ghi output ra file (utf-8). Mac dinh chi in ra stdout.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="Gioi han ky tu moi raw response. 0 = khong cat (mac dinh).",
    )
    args = parser.parse_args()

    clause_ids = [args.clause_id] if args.clause_id else None

    print(f"[*] Doc: {args.doc_id} | {args.old} -> {args.new} | k={args.k}")
    if clause_ids:
        print(f"[*] Chi debug clause: {args.clause_id}")
    print("[*] Dang goi DocumentComparator (co the mat vai phut tren CPU)...")

    comparator = DocumentComparator()
    result = comparator.compare_versions(
        doc_id=args.doc_id,
        version_old=args.old,
        version_new=args.new,
        clause_ids=clause_ids,
        k=args.k,
    )

    report = render_report(result, max_chars=args.max_chars)
    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"\n[+] Da ghi ra {out_path}")


if __name__ == "__main__":
    main()
