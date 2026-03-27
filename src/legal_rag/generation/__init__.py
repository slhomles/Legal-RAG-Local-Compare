# Module Tuần 7-8: Sinh báo cáo so sánh và trích dẫn
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.prompts import check_guardrails
from legal_rag.generation.report import ReportGenerator

__all__ = ["DocumentComparator", "CitationMapper", "ReportGenerator", "check_guardrails"]
