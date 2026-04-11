# ---------------------------------------------------------------------------
# Script kiem thu so bo: do luong ty le ket luan co trich dan dung va lien quan.
#
# Ground truth duoc xay dung tu create_sample_data.py (Hop_dong_A v1 vs v2):
#   - Dieu 1: SUA (them "man hinh")
#   - Dieu 2: SUA (gia tri 500M -> 650M, VAT 10% -> 8%, them L/C)
#   - Dieu 3: SUA (30 -> 45 ngay, them lua chon nha van chuyen)
#   - Dieu 4: SUA (bao hanh 12 -> 24 thang, them hotline 24/7)
#   - Dieu 5: SUA (phat 8% -> 10%)
#   - Dieu 6: THEM (dieu khoan giai quyet tranh chap)
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from legal_rag.evaluation.metrics import (
    change_detection_rate,
    citation_accuracy,
    guardrail_compliance,
)
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.report import ReportGenerator

# ============================================================
# GROUND TRUTH cho Hop_dong_A (v1 -> v2)
# Dua tren create_sample_data.py
# ============================================================
GROUND_TRUTH_HOP_DONG_A: List[Dict[str, str]] = [
    {"clause_id": "dieu_1", "type": "SUA", "description": "Them 'man hinh' vao danh sach hang hoa"},
    {"clause_id": "dieu_2", "type": "SUA", "description": "Gia tri 500M -> 650M, VAT 10% -> 8%, them L/C"},
    {"clause_id": "dieu_3", "type": "SUA", "description": "Thoi gian giao 30 -> 45 ngay, them nha van chuyen"},
    {"clause_id": "dieu_4", "type": "SUA", "description": "Bao hanh 12 -> 24 thang, them hotline 24/7"},
    {"clause_id": "dieu_5", "type": "SUA", "description": "Muc phat 8% -> 10%"},
    {"clause_id": "dieu_6", "type": "THEM", "description": "Dieu khoan moi ve giai quyet tranh chap"},
]


def run_evaluation(
    doc_id: str = "Hop_dong_A",
    version_old: str = "v1",
    version_new: str = "v2",
    ground_truth: Optional[List[Dict[str, str]]] = None,
    k: int = 30,
) -> Dict[str, Any]:
    """
    Chay pipeline day du va do luong cac chi so.

    Returns:
        {
            "citation_metrics": {...},
            "detection_metrics": {...},
            "guardrail_metrics": {...},
            "report": {...}
        }
    """
    if ground_truth is None:
        ground_truth = GROUND_TRUTH_HOP_DONG_A

    print("=" * 60)
    print("EVALUATION: KIEM THU DO LUONG CHAT LUONG HE THONG")
    print("=" * 60)

    # Buoc 1: So sanh
    print(f"\n[1/4] So sanh {doc_id}: {version_old} -> {version_new}...")
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(
        doc_id=doc_id,
        version_old=version_old,
        version_new=version_new,
        k=k,
    )
    n_clauses = len(comparison.get("clauses", {}))
    print(f"      -> Tim thay {n_clauses} dieu khoan")

    # Buoc 2: Citation mapping
    print("[2/4] Anh xa trich dan...")
    mapper = CitationMapper(retriever=comparator.retriever)
    enriched = mapper.enrich_changes(comparison)

    # Buoc 3: Sinh bao cao
    print("[3/4] Sinh bao cao tom tat...")
    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)

    # Buoc 4: Do luong
    print("[4/4] Tinh toan metrics...")
    cit_metrics = citation_accuracy(report)
    det_metrics = change_detection_rate(report, ground_truth)
    guard_metrics = guardrail_compliance(report)

    # In ket qua
    print("\n" + "=" * 60)
    print("KET QUA EVALUATION")
    print("=" * 60)

    print("\n--- CITATION ACCURACY ---")
    print(f"  Tong citations       : {cit_metrics['total_citations']}")
    print(f"  Tim thay             : {cit_metrics['found_citations']}")
    print(f"  Exact match          : {cit_metrics['exact_matches']}")
    print(f"  Normalized match     : {cit_metrics['normalized_matches']}")
    print(f"  Partial match        : {cit_metrics['partial_matches']}")
    print(f"  Khong tim thay       : {cit_metrics['not_found']}")
    print(f"  >> Accuracy          : {cit_metrics['accuracy']:.2%}")
    print(f"  >> Exact rate        : {cit_metrics['exact_rate']:.2%}")

    print("\n--- CHANGE DETECTION ---")
    print(f"  Thay doi ky vong     : {det_metrics['total_expected']}")
    print(f"  Phat hien dung       : {det_metrics['detected']}")
    print(f"  Bo sot               : {det_metrics['missed']}")
    print(f"  Phat hien thua       : {det_metrics['extra']}")
    print(f"  >> Recall            : {det_metrics['recall']:.2%}")
    print(f"  >> Precision         : {det_metrics['precision']:.2%}")
    print(f"  >> F1                : {det_metrics['f1']:.2%}")

    if det_metrics["missed_details"]:
        print(f"  Bo sot chi tiet      : {det_metrics['missed_details']}")
    if det_metrics["extra_details"]:
        print(f"  Thua chi tiet        : {det_metrics['extra_details']}")

    print("\n--- GUARDRAIL COMPLIANCE ---")
    print(f"  Tong kiem tra         : {guard_metrics['total_checks']}")
    print(f"  Tuan thu             : {guard_metrics['compliant']}")
    print(f"  Vi pham              : {guard_metrics['violations']}")
    print(f"  >> Compliance rate   : {guard_metrics['compliance_rate']:.2%}")

    if guard_metrics["violation_details"]:
        print(f"  Chi tiet vi pham     : {guard_metrics['violation_details']}")

    print("\n" + "=" * 60)

    return {
        "citation_metrics": cit_metrics,
        "detection_metrics": det_metrics,
        "guardrail_metrics": guard_metrics,
        "report": report,
    }


def main():
    result = run_evaluation()

    # Xuat JSON neu co flag --json
    if "--json" in sys.argv:
        output = {
            "citation_metrics": result["citation_metrics"],
            "detection_metrics": result["detection_metrics"],
            "guardrail_metrics": result["guardrail_metrics"],
        }
        print("\n" + json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
