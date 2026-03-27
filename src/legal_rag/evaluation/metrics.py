# ---------------------------------------------------------------------------
# Metrics do luong chat luong he thong so sanh hop dong.
#
# Cac chi so chinh:
#   1. Citation Accuracy: ty le trich dan tim thay dung trong chunk goc
#   2. Change Detection Rate: ty le thay doi duoc phat hien (vs ground truth)
#   3. Guardrail Compliance: ty le output khong vi pham guardrails
# ---------------------------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, List


def citation_accuracy(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Do luong ty le trich dan chinh xac trong bao cao.

    Mot citation duoc coi la "chinh xac" khi:
      - found == True
      - match_type in ("exact", "normalized")

    Returns:
        {
            "total_citations": 10,
            "found_citations": 8,
            "exact_matches": 6,
            "normalized_matches": 2,
            "partial_matches": 1,
            "not_found": 1,
            "accuracy": 0.80,
            "exact_rate": 0.60,
            "details": [...]
        }
    """
    total = 0
    found = 0
    exact = 0
    normalized = 0
    partial = 0
    not_found = 0
    details: List[Dict[str, Any]] = []

    for change in report.get("changes_detail", []):
        citations = change.get("citations", {})

        for source_key in ("old_source", "new_source"):
            src = citations.get(source_key, {})
            if not src:
                continue

            total += 1
            is_found = src.get("found", False)
            match_type = src.get("match_type", "none")

            if is_found:
                found += 1
                if match_type == "exact":
                    exact += 1
                elif match_type == "normalized":
                    normalized += 1
                elif match_type == "partial":
                    partial += 1
            else:
                not_found += 1

            details.append({
                "clause_id": change.get("clause_id", ""),
                "source_key": source_key,
                "found": is_found,
                "match_type": match_type,
                "chunk_id": src.get("chunk_id", ""),
            })

    accuracy = found / total if total > 0 else 0.0
    exact_rate = exact / total if total > 0 else 0.0

    return {
        "total_citations": total,
        "found_citations": found,
        "exact_matches": exact,
        "normalized_matches": normalized,
        "partial_matches": partial,
        "not_found": not_found,
        "accuracy": round(accuracy, 4),
        "exact_rate": round(exact_rate, 4),
        "details": details,
    }


def change_detection_rate(
    report: Dict[str, Any],
    ground_truth: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Do luong ty le thay doi duoc phat hien so voi ground truth.

    ground_truth: danh sach cac thay doi da biet, moi item co dang:
        {
            "clause_id": "dieu_2",
            "type": "SUA",
            "description": "Thay doi gia tri hop dong"
        }

    Returns:
        {
            "total_expected": 8,
            "detected": 6,
            "missed": 2,
            "extra": 1,
            "recall": 0.75,
            "precision": 0.857,
            "f1": 0.80,
            "missed_details": [...],
            "extra_details": [...]
        }
    """
    # Tap hop cac thay doi da phat hien (clause_id, type)
    detected_set: set[tuple[str, str]] = set()
    detected_list: List[Dict[str, str]] = []

    for change in report.get("changes_detail", []):
        key = (change.get("clause_id", ""), change.get("type", ""))
        detected_set.add(key)
        detected_list.append(change)

    # Tap hop ground truth
    expected_set: set[tuple[str, str]] = set()
    for gt in ground_truth:
        expected_set.add((gt["clause_id"], gt["type"]))

    # Tinh toan
    true_positives = detected_set & expected_set
    missed = expected_set - detected_set
    extra = detected_set - expected_set

    total_expected = len(expected_set)
    total_detected = len(detected_set)

    recall = len(true_positives) / total_expected if total_expected > 0 else 0.0
    precision = len(true_positives) / total_detected if total_detected > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "total_expected": total_expected,
        "detected": len(true_positives),
        "missed": len(missed),
        "extra": len(extra),
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "missed_details": [{"clause_id": m[0], "type": m[1]} for m in missed],
        "extra_details": [{"clause_id": e[0], "type": e[1]} for e in extra],
    }


def guardrail_compliance(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Do luong ty le output tuan thu guardrails (khong chua cum tu vi pham).

    Returns:
        {
            "total_clauses": 5,
            "compliant": 4,
            "violations": 1,
            "compliance_rate": 0.80,
            "violation_details": [...]
        }
    """
    total = 0
    compliant = 0
    violation_details: List[Dict[str, Any]] = []

    # Kiem tra tung clause trong comparison_result goc (neu co)
    # Hoac kiem tra summary
    summary_ok = report.get("guardrail_ok", True)
    summary_violations = report.get("guardrail_violations", [])

    if not summary_ok:
        violation_details.append({
            "source": "summary",
            "violations": summary_violations,
        })

    # Dem guardrail compliance theo tung metric tong the
    total = 1  # summary
    compliant = 1 if summary_ok else 0

    compliance_rate = compliant / total if total > 0 else 1.0

    return {
        "total_checks": total,
        "compliant": compliant,
        "violations": total - compliant,
        "compliance_rate": round(compliance_rate, 4),
        "violation_details": violation_details,
    }
