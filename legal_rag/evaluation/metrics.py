# ---------------------------------------------------------------------------
# Metrics do luong chat luong he thong so sanh hop dong.
#
# Cac chi so chinh:
#   1. Citation Accuracy: ty le trich dan tim thay dung trong chunk goc
#   2. Change Detection Rate: ty le thay doi duoc phat hien (vs ground truth)
#   3. Guardrail Compliance: ty le output khong vi pham guardrails
#   4. Processing Time: thoi gian xu ly trung binh moi cap tai lieu
#   5. Hallucination Rate: ty le ket luan khong co bang chung nguon
# ---------------------------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, List

# Chuyen doi type co dau <-> khong dau de so sanh nhat quan
_NORMALIZE_TYPE: Dict[str, str] = {
    "THÊM": "THEM", "THEM": "THEM",
    "XOÁ": "XOA", "XÓA": "XOA", "XOA": "XOA",
    "SỬA": "SUA", "SUA": "SUA",
}


def _norm_type(t: str) -> str:
    """Chuyen 'SỬA'/'SUA'/'THÊM'/'THEM'/... ve dang chuan khong dau."""
    return _NORMALIZE_TYPE.get(t.strip().upper(), t.strip().upper())


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
    # Tap hop cac thay doi da phat hien (clause_id, type_chuan_hoa)
    detected_set: set[tuple[str, str]] = set()
    detected_list: List[Dict[str, str]] = []

    for change in report.get("changes_detail", []):
        key = (change.get("clause_id", ""), _norm_type(change.get("type", "")))
        detected_set.add(key)
        detected_list.append(change)

    # Tap hop ground truth (cung chuan hoa type)
    expected_set: set[tuple[str, str]] = set()
    for gt in ground_truth:
        expected_set.add((gt["clause_id"], _norm_type(gt["type"])))

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


def processing_time_metric(
    start_time: float,
    end_time: float,
    n_clauses: int,
) -> Dict[str, Any]:
    """
    Tinh thoi gian xu ly cho mot cap tai lieu.

    Args:
        start_time: time.perf_counter() truoc khi chay pipeline
        end_time:   time.perf_counter() sau khi chay pipeline
        n_clauses:  so dieu khoan da xu ly

    Returns:
        {
            "total_seconds": 12.4,
            "seconds_per_clause": 2.48,
            "n_clauses": 5
        }
    """
    total = round(end_time - start_time, 3)
    per_clause = round(total / n_clauses, 3) if n_clauses > 0 else 0.0
    return {
        "total_seconds": total,
        "seconds_per_clause": per_clause,
        "n_clauses": n_clauses,
    }


def hallucination_rate(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uoc tinh ty le hallucination dua tren ket qua citation.

    Mot thay doi bị coi la "ungrounded" (hallucination) khi:
      - SUA: ca old_source va new_source deu found == False
      - THEM: new_source found == False
      - XOA: old_source found == False

    Returns:
        {
            "total_changes": 8,
            "ungrounded_changes": 1,
            "hallucination_rate": 0.125,
            "ungrounded_details": [{"clause_id": "dieu_3", "type": "SỬA", "reason": "..."}]
        }
    """
    total = 0
    ungrounded = 0
    ungrounded_details: List[Dict[str, Any]] = []

    for change in report.get("changes_detail", []):
        citations = change.get("citations", {})
        change_type_norm = _norm_type(change.get("type", ""))
        clause_id = change.get("clause_id", "")
        original_type = change.get("type", "")

        old_found = citations.get("old_source", {}).get("found", False)
        new_found = citations.get("new_source", {}).get("found", False)

        total += 1
        if change_type_norm == "THEM":
            if not new_found:
                ungrounded += 1
                ungrounded_details.append({
                    "clause_id": clause_id,
                    "type": original_type,
                    "reason": "new_source not_found",
                })
        elif change_type_norm == "XOA":
            if not old_found:
                ungrounded += 1
                ungrounded_details.append({
                    "clause_id": clause_id,
                    "type": original_type,
                    "reason": "old_source not_found",
                })
        else:  # SUA hoac khac
            if not old_found and not new_found:
                ungrounded += 1
                ungrounded_details.append({
                    "clause_id": clause_id,
                    "type": original_type,
                    "reason": "both sources not_found",
                })

    rate = round(ungrounded / total, 4) if total > 0 else 0.0
    return {
        "total_changes": total,
        "ungrounded_changes": ungrounded,
        "hallucination_rate": rate,
        "ungrounded_details": ungrounded_details,
    }
