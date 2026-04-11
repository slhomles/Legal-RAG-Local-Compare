"""
So sanh hai phien ban hop dong va sinh bao cao thay doi.

Su dung:
    python scripts/compare.py
    python scripts/compare.py --doc-id Hop_dong_A --old v1 --new v2 --json
"""
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.report import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="So sanh hai phien ban hop dong")
    parser.add_argument("--doc-id", default="Hop_dong_A", help="ID tai lieu")
    parser.add_argument("--old", default="v1", help="Phien ban cu")
    parser.add_argument("--new", default="v2", help="Phien ban moi")
    parser.add_argument("--json", action="store_true", help="Xuat ket qua JSON")
    parser.add_argument("-k", type=int, default=20, help="So chunk toi da truy xuat")
    args = parser.parse_args()

    print("=" * 60)
    print("SO SANH HOP DONG VA SINH BAO CAO")
    print("=" * 60)
    print(f"[*] Doc: {args.doc_id} | {args.old} -> {args.new}")

    # Buoc 1: So sanh
    print("\n[*] Buoc 1: Truy xuat va phat hien thay doi...")
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(
        doc_id=args.doc_id, version_old=args.old, version_new=args.new, k=args.k,
    )
    n_clauses = len(comparison.get("clauses", {}))
    n_new = len(comparison.get("new_clauses", []))
    n_removed = len(comparison.get("removed_clauses", []))
    print(f"[+] Tim thay {n_clauses} dieu khoan ({n_new} moi, {n_removed} bi xoa)")

    # Buoc 2: Anh xa trich dan
    print("\n[*] Buoc 2: Anh xa trich dan chinh xac...")
    citation_mapper = CitationMapper(retriever=comparator.retriever)
    enriched = citation_mapper.enrich_changes(comparison)
    print("[+] Da bo sung citation cho cac thay doi")

    # Buoc 3: Sinh bao cao
    print("\n[*] Buoc 3: Sinh bao cao tom tat...")
    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)

    # Xuat ket qua
    if args.json:
        print("\n" + json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n" + report_gen.format_plain_text(report))


if __name__ == "__main__":
    main()
