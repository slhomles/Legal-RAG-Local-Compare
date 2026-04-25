"""
Chay danh gia toan bo tap du lieu va luu ket qua vao output/.

Su dung:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --k 20
    python scripts/run_evaluation.py --doc-ids Hop_dong_A Hop_dong_B
    python scripts/run_evaluation.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Them goc du an vao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from legal_rag.config import GROUND_TRUTH_DIR
from legal_rag.evaluation.evaluator import load_ground_truth, run_evaluation

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_doc_ids() -> List[str]:
    """Tra ve tat ca doc_id co file ground truth JSON."""
    return sorted(
        p.stem.replace("_ground_truth", "")
        for p in Path(GROUND_TRUTH_DIR).glob("*_ground_truth.json")
    )


# ---------------------------------------------------------------------------
# Error accumulation
# ---------------------------------------------------------------------------

def _accumulate_errors(
    doc_id: str,
    result: Dict[str, Any],
    error_log: Dict[str, Any],
) -> None:
    """Gop log loi tu ket qua mot cap vao error_log tong hop."""
    det = result.get("detection_metrics", {})

    # Missed changes (bo sot)
    for item in det.get("missed_details", []):
        t = item.get("type", "UNKNOWN")
        error_log["missed_by_type"].setdefault(t, []).append(
            f"{doc_id}:{item.get('clause_id', '?')}"
        )

    # Extra changes (phat hien thua)
    for item in det.get("extra_details", []):
        t = item.get("type", "UNKNOWN")
        error_log["extra_by_type"].setdefault(t, []).append(
            f"{doc_id}:{item.get('clause_id', '?')}"
        )

    # Wrong citations (trich dan sai)
    for cit in result.get("citation_metrics", {}).get("details", []):
        if not cit.get("found", True):
            error_log["wrong_citations"].append({
                "doc_id": doc_id,
                "clause_id": cit.get("clause_id", ""),
                "source_key": cit.get("source_key", ""),
                "chunk_id": cit.get("chunk_id", ""),
            })


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def _safe_avg(values: List[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _compute_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tinh trung binh tat ca metrics, phan nhom theo do kho."""
    ok_results = [r for r in results if r.get("error") is None]

    def _collect(key: str, sub: str) -> List[float]:
        return [r[key][sub] for r in ok_results if key in r and sub in r[key]]

    summary: Dict[str, Any] = {
        "total_docs": len(results),
        "evaluated_ok": len(ok_results),
        "avg_precision":           _safe_avg(_collect("detection_metrics",   "precision")),
        "avg_recall":              _safe_avg(_collect("detection_metrics",   "recall")),
        "avg_f1":                  _safe_avg(_collect("detection_metrics",   "f1")),
        "avg_citation_accuracy":   _safe_avg(_collect("citation_metrics",    "accuracy")),
        "avg_hallucination_rate":  _safe_avg(_collect("hallucination_metrics", "hallucination_rate")),
        "avg_processing_seconds":  _safe_avg(_collect("time_metrics",        "total_seconds")),
        "avg_compliance_rate":     _safe_avg(_collect("guardrail_metrics",   "compliance_rate")),
    }

    # Phan nhom theo do kho
    by_difficulty: Dict[str, List] = {"easy": [], "medium": [], "hard": []}
    for r in ok_results:
        diff = r.get("difficulty", "unknown")
        if diff in by_difficulty:
            by_difficulty[diff].append(r)

    breakdown: Dict[str, Any] = {}
    for diff, group in by_difficulty.items():
        if not group:
            continue
        def _gavg(key: str, sub: str) -> float:
            return _safe_avg([g[key][sub] for g in group if key in g and sub in g[key]])
        breakdown[diff] = {
            "count": len(group),
            "avg_f1": _gavg("detection_metrics", "f1"),
            "avg_citation_accuracy": _gavg("citation_metrics", "accuracy"),
            "avg_hallucination_rate": _gavg("hallucination_metrics", "hallucination_rate"),
            "avg_processing_seconds": _gavg("time_metrics", "total_seconds"),
        }

    summary["breakdown_by_difficulty"] = breakdown
    return summary


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _print_summary(summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("TOM TAT KET QUA DANH GIA")
    print("=" * 60)
    print(f"  Tong so cap        : {summary['total_docs']}")
    print(f"  Danh gia thanh cong: {summary['evaluated_ok']}")
    print(f"\n  --- Metrics trung binh ---")
    print(f"  Precision          : {summary['avg_precision']:.2%}")
    print(f"  Recall             : {summary['avg_recall']:.2%}")
    print(f"  F1                 : {summary['avg_f1']:.2%}")
    print(f"  Citation accuracy  : {summary['avg_citation_accuracy']:.2%}")
    print(f"  Hallucination rate : {summary['avg_hallucination_rate']:.2%}")
    print(f"  Compliance rate    : {summary['avg_compliance_rate']:.2%}")
    print(f"  Thoi gian xu ly    : {summary['avg_processing_seconds']:.1f}s/cap")

    breakdown = summary.get("breakdown_by_difficulty", {})
    if breakdown:
        print(f"\n  --- Phan nhom theo do kho ---")
        for diff in ("easy", "medium", "hard"):
            b = breakdown.get(diff)
            if not b:
                continue
            print(f"  [{diff.upper():6s}] n={b['count']}  "
                  f"F1={b['avg_f1']:.2%}  "
                  f"Citation={b['avg_citation_accuracy']:.2%}  "
                  f"Halluc={b['avg_hallucination_rate']:.2%}  "
                  f"Time={b['avg_processing_seconds']:.1f}s")

    print("=" * 60)


def _print_error_summary(error_log: Dict[str, Any]) -> None:
    missed = error_log.get("missed_by_type", {})
    extra  = error_log.get("extra_by_type", {})
    wrong  = error_log.get("wrong_citations", [])

    if not missed and not extra and not wrong:
        print("\n  (Khong phat hien loi nao dang ghi nhan)")
        return

    print("\n--- LOG LOI PHO BIEN ---")
    if missed:
        print("  Bo sot theo loai:")
        for t, items in missed.items():
            print(f"    {t}: {len(items)} truong hop -> {items[:5]}")
    if extra:
        print("  Phat hien thua theo loai:")
        for t, items in extra.items():
            print(f"    {t}: {len(items)} truong hop -> {items[:5]}")
    if wrong:
        print(f"  Trich dan sai: {len(wrong)} truong hop")
        for w in wrong[:5]:
            print(f"    {w['doc_id']}:{w['clause_id']} [{w['source_key']}]")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all(doc_ids: List[str], k: int) -> Dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results: List[Dict[str, Any]] = []
    error_log: Dict[str, Any] = {
        "missed_by_type": {},
        "extra_by_type": {},
        "wrong_citations": [],
    }

    for doc_id in doc_ids:
        gt_data = load_ground_truth(doc_id)
        if gt_data is None:
            print(f"\n[WARN] Khong co ground truth cho {doc_id}, bo qua.")
            continue

        print(f"\n{'=' * 60}")
        print(f"Danh gia: {doc_id}  [{gt_data.get('difficulty', '?')}]")
        print(f"Mo ta   : {gt_data.get('description', '')}")

        try:
            result = run_evaluation(
                doc_id=doc_id,
                version_old=gt_data.get("version_old", "v1"),
                version_new=gt_data.get("version_new", "v2"),
                k=k,
            )
            result["doc_id"] = doc_id
            result["difficulty"] = gt_data.get("difficulty", "unknown")
            result["error"] = None
        except Exception as exc:
            print(f"[ERROR] {doc_id}: {exc}")
            result = {
                "doc_id": doc_id,
                "difficulty": gt_data.get("difficulty", "unknown"),
                "error": str(exc),
            }

        all_results.append(result)
        _accumulate_errors(doc_id, result, error_log)

    summary = _compute_summary(all_results)

    output = {
        "timestamp": timestamp,
        "k": k,
        "total_docs": len(doc_ids),
        "evaluated": len([r for r in all_results if r.get("error") is None]),
        "summary": summary,
        "per_doc_results": all_results,
        "error_log": error_log,
    }

    out_path = OUTPUT_DIR / f"evaluation_round1_{timestamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        # Loai bo truong 'report' lon khi luu de giu file gon
        slim = {
            **output,
            "per_doc_results": [
                {k2: v for k2, v in r.items() if k2 != "report"}
                for r in all_results
            ],
        }
        json.dump(slim, f, ensure_ascii=False, indent=2)

    print(f"\nKet qua luu tai: {out_path}")
    _print_summary(summary)
    _print_error_summary(error_log)

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chay danh gia toan bo tap du lieu legal RAG."
    )
    parser.add_argument(
        "--k", type=int, default=30,
        help="So luong chunks truy xuat moi phien (mac dinh: 30)",
    )
    parser.add_argument(
        "--doc-ids", nargs="*", default=None,
        help="Danh sach doc_id can danh gia (mac dinh: tat ca)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="In ket qua JSON ra stdout sau khi hoan tat",
    )
    args = parser.parse_args()

    doc_ids = args.doc_ids or discover_doc_ids()
    if not doc_ids:
        print("[ERROR] Khong tim thay file ground truth nao.")
        print("        Chay 'python scripts/create_sample_data.py' truoc.")
        sys.exit(1)

    print(f"Se danh gia {len(doc_ids)} cap: {doc_ids}")

    output = run_all(doc_ids, k=args.k)

    if args.json:
        printable = {
            "timestamp": output["timestamp"],
            "summary": output["summary"],
            "error_log": output["error_log"],
        }
        print("\n" + json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
