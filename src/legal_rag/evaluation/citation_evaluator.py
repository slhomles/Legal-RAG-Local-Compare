from typing import Any, Dict, List


class CitationEvaluator:
    def __init__(self):
        pass

    def _is_valid_single_citation(
        self,
        citation: Dict[str, Any],
        expected_version: str,
        expected_clause_id: str,
    ) -> bool:
        if not isinstance(citation, dict):
            return False

        required_fields = [
            "source_file",
            "doc_id",
            "document_id",
            "version",
            "clause_id",
            "chunk_heading",
            "matched_text",
            "match_type",
        ]

        for field in required_fields:
            if field not in citation:
                return False

        if citation.get("version") != expected_version:
            return False

        if citation.get("clause_id") != expected_clause_id:
            return False

        matched_text = citation.get("matched_text")
        if not isinstance(matched_text, str) or not matched_text.strip():
            return False

        return True

    def _evaluate_change(self, item: Dict[str, Any]) -> Dict[str, Any]:
        clause_id = item.get("clause_id")
        changes = item.get("changes", [])

        total_changes = 0
        changes_with_any_citation = 0
        changes_with_both_citations = 0
        valid_original_citations = 0
        valid_revised_citations = 0

        detailed_results = []

        for change in changes:
            total_changes += 1

            citations = change.get("citations", {})
            original_citation = citations.get("original") if isinstance(citations, dict) else None
            revised_citation = citations.get("revised") if isinstance(citations, dict) else None

            has_any = original_citation is not None or revised_citation is not None
            has_both = original_citation is not None and revised_citation is not None

            if has_any:
                changes_with_any_citation += 1
            if has_both:
                changes_with_both_citations += 1

            original_valid = False
            revised_valid = False

            if original_citation is not None:
                original_valid = self._is_valid_single_citation(
                    citation=original_citation,
                    expected_version="A",
                    expected_clause_id=clause_id,
                )
                if original_valid:
                    valid_original_citations += 1

            if revised_citation is not None:
                revised_valid = self._is_valid_single_citation(
                    citation=revised_citation,
                    expected_version="B",
                    expected_clause_id=clause_id,
                )
                if revised_valid:
                    valid_revised_citations += 1

            detailed_results.append({
                "change_type": change.get("change_type"),
                "summary": change.get("summary"),
                "has_any_citation": has_any,
                "has_both_citations": has_both,
                "original_citation_valid": original_valid,
                "revised_citation_valid": revised_valid,
            })

        return {
            "clause_id": clause_id,
            "total_changes": total_changes,
            "changes_with_any_citation": changes_with_any_citation,
            "changes_with_both_citations": changes_with_both_citations,
            "valid_original_citations": valid_original_citations,
            "valid_revised_citations": valid_revised_citations,
            "details": detailed_results,
        }

    def evaluate_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        results = report_data.get("results", [])

        clause_reports: List[Dict[str, Any]] = []

        total_clauses = 0
        total_changes = 0
        total_changes_with_any_citation = 0
        total_changes_with_both_citations = 0
        total_valid_original_citations = 0
        total_valid_revised_citations = 0

        for item in results:
            clause_report = self._evaluate_change(item)
            clause_reports.append(clause_report)

            total_clauses += 1
            total_changes += clause_report["total_changes"]
            total_changes_with_any_citation += clause_report["changes_with_any_citation"]
            total_changes_with_both_citations += clause_report["changes_with_both_citations"]
            total_valid_original_citations += clause_report["valid_original_citations"]
            total_valid_revised_citations += clause_report["valid_revised_citations"]

        any_citation_rate = (
            total_changes_with_any_citation / total_changes if total_changes > 0 else 0.0
        )
        both_citation_rate = (
            total_changes_with_both_citations / total_changes if total_changes > 0 else 0.0
        )
        original_valid_rate = (
            total_valid_original_citations / total_changes if total_changes > 0 else 0.0
        )
        revised_valid_rate = (
            total_valid_revised_citations / total_changes if total_changes > 0 else 0.0
        )

        return {
            "document_id": report_data.get("document_id"),
            "total_clauses": total_clauses,
            "total_changes": total_changes,
            "changes_with_any_citation": total_changes_with_any_citation,
            "changes_with_both_citations": total_changes_with_both_citations,
            "valid_original_citations": total_valid_original_citations,
            "valid_revised_citations": total_valid_revised_citations,
            "any_citation_rate": round(any_citation_rate, 4),
            "both_citation_rate": round(both_citation_rate, 4),
            "original_valid_rate": round(original_valid_rate, 4),
            "revised_valid_rate": round(revised_valid_rate, 4),
            "clause_reports": clause_reports,
        }