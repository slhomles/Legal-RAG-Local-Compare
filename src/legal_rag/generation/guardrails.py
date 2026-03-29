from typing import Any, Dict


FORBIDDEN_PATTERNS = [
    "hợp pháp",
    "không hợp pháp",
    "trái luật",
    "đúng luật",
    "vi phạm pháp luật",
    "vô hiệu",
    "có hiệu lực",
    "tư vấn pháp lý",
    "nên khởi kiện",
    "rủi ro pháp lý",
]


SAFE_FALLBACK = {
    "document_id": "",
    "clause_id": "",
    "status": "unknown",
    "changes": [],
    "note": "Không đủ bằng chứng hoặc đầu ra không hợp lệ để kết luận."
}


ALLOWED_STATUS = {"added", "removed", "modified", "unchanged", "unknown"}
ALLOWED_CHANGE_TYPES = {"added", "removed", "modified"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def contains_forbidden_legal_judgment(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in FORBIDDEN_PATTERNS)


def validate_change_item(change: Dict[str, Any]) -> bool:
    if not isinstance(change, dict):
        return False

    if change.get("change_type") not in ALLOWED_CHANGE_TYPES:
        return False

    if "summary" not in change:
        return False

    if "evidence_from_original" not in change:
        return False

    if "evidence_from_revised" not in change:
        return False

    if change.get("confidence") not in ALLOWED_CONFIDENCE:
        return False

    change_type = change.get("change_type")
    ev_a = change.get("evidence_from_original")
    ev_b = change.get("evidence_from_revised")

    if change_type == "added" and not ev_b:
        return False

    if change_type == "removed" and not ev_a:
        return False

    if change_type == "modified" and not (ev_a and ev_b):
        return False

    return True


def validate_compare_output(result: Dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False

    required_fields = ["document_id", "clause_id", "status", "changes", "note"]
    for field in required_fields:
        if field not in result:
            return False

    if result["status"] not in ALLOWED_STATUS:
        return False

    if not isinstance(result["changes"], list):
        return False

    for change in result["changes"]:
        if not validate_change_item(change):
            return False

    text_blob = str(result)
    if contains_forbidden_legal_judgment(text_blob):
        return False

    return True


def build_safe_fallback(document_id: str, clause_id: str) -> Dict[str, Any]:
    fallback = SAFE_FALLBACK.copy()
    fallback["document_id"] = document_id
    fallback["clause_id"] = clause_id
    return fallback