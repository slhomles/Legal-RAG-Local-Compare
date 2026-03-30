# Gọi API Ollama (Qwen 2.5) để so sánh, phát hiện thêm/xóa/sửa và tóm tắt [cite: 17]

import json
import re
import unicodedata
from typing import Any, Dict, List, Tuple

import requests

from legal_rag.generation.prompts import (
    COMPARE_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_compare_user_prompt,
    build_report_user_prompt,
)

from legal_rag.generation.guardrails import (
    build_safe_fallback,
    validate_compare_output,
)


class LegalComparator:
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct",
        ollama_url: str = "http://127.0.0.1:11434/api/generate",
    ):
        self.model_name = model_name
        self.ollama_url = ollama_url

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0
                    }
                },
                timeout=120,
            )

            if response.status_code != 200:
                print("\n[OLLAMA STATUS CODE]")
                print(response.status_code)
                print("\n[OLLAMA ERROR BODY]")
                print(response.text)
                response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(
                f"Không kết nối được tới Ollama API tại {self.ollama_url}. "
                "Hãy kiểm tra Ollama đang chạy nền và cổng 11434 có đúng là của Ollama hay không."
            ) from e

    def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_output[start : end + 1]
                return json.loads(candidate)
            raise


    def _parse_report_output(self, raw_output: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_output[start:end + 1]
                return json.loads(candidate)
            raise


    def _normalize_report_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "overview" not in result or result["overview"] is None:
            result["overview"] = "Không đủ dữ liệu để tóm tắt."
        elif not isinstance(result["overview"], str):
            result["overview"] = str(result["overview"])

        if "key_changes" not in result or result["key_changes"] is None:
            result["key_changes"] = []
        elif not isinstance(result["key_changes"], list):
            result["key_changes"] = [str(result["key_changes"])]

        normalized_key_changes = []
        for item in result["key_changes"]:
            if item is None:
                continue
            normalized_key_changes.append(str(item))
        result["key_changes"] = normalized_key_changes

        result["risk_note"] = "Chỉ mô tả khác biệt văn bản, không đánh giá pháp lý."

        return result

    def _normalize_to_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return [item for item in value if item is not None]
        return [value]

    def _extract_text(self, item: Any) -> str:
        if item is None:
            return ""

        if hasattr(item, "page_content"):
            return str(getattr(item, "page_content", "")).strip()

        if isinstance(item, dict):
            for key in ("page_content", "content", "text", "chunk_text"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return str(item).strip()

    def _extract_metadata(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}

        if hasattr(item, "metadata") and isinstance(item.metadata, dict):
            return dict(item.metadata)

        if isinstance(item, dict):
            metadata = item.get("metadata")
            if isinstance(metadata, dict):
                return dict(metadata)

            return {
                k: v
                for k, v in item.items()
                if k not in {"page_content", "content", "text", "chunk_text"}
            }

        return {}
    

    def _strip_accents(self, text: str) -> str:
        if not text:
            return ""

        normalized = unicodedata.normalize("NFD", text)
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    
    def _normalize_match_text(self, text: str) -> str:
        if not text:
            return ""

        text = self._strip_accents(text)
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    

    def _find_best_citation(self, evidence: str, docs: List[Any]) -> Dict[str, Any]:
        if not evidence or not docs:
            return {}

        evidence = evidence.strip()
        if not evidence:
            return {}

        normalized_evidence = self._normalize_match_text(evidence)
        evidence_tokens = set(normalized_evidence.split())

        best_result = {}
        best_score = -1

        for doc in docs:
            text = self._extract_text(doc)
            metadata = self._extract_metadata(doc)

            if not text:
                continue

            # 1) Match exact
            char_start = text.find(evidence)
            if char_start != -1:
                char_end = char_start + len(evidence)
                matched_text = text[char_start:char_end]
                score = len(matched_text)

                citation = {
                    "source_file": metadata.get("source_file"),
                    "doc_id": metadata.get("doc_id"),
                    "document_id": metadata.get("document_id"),
                    "version": metadata.get("version"),
                    "clause_id": metadata.get("clause_id"),
                    "chunk_heading": metadata.get("chunk_heading"),
                    "matched_text": matched_text,
                    "char_start": char_start,
                    "char_end": char_end,
                    "match_type": "exact",
                }

                if score > best_score:
                    best_score = score
                    best_result = citation

                continue

            # 2) Match không phân biệt hoa thường
            lower_text = text.lower()
            lower_evidence = evidence.lower()
            char_start = lower_text.find(lower_evidence)
            if char_start != -1:
                char_end = char_start + len(evidence)
                matched_text = text[char_start:char_end]
                score = len(matched_text)

                citation = {
                    "source_file": metadata.get("source_file"),
                    "doc_id": metadata.get("doc_id"),
                    "document_id": metadata.get("document_id"),
                    "version": metadata.get("version"),
                    "clause_id": metadata.get("clause_id"),
                    "chunk_heading": metadata.get("chunk_heading"),
                    "matched_text": matched_text,
                    "char_start": char_start,
                    "char_end": char_end,
                    "match_type": "case_insensitive",
                }

                if score > best_score:
                    best_score = score
                    best_result = citation

                continue

            # 3) Match theo text đã normalize (bỏ dấu, bỏ dấu câu, chuẩn hóa khoảng trắng)
            normalized_text = self._normalize_match_text(text)
            if normalized_evidence and normalized_evidence in normalized_text:
                score = len(normalized_evidence)

                citation = {
                    "source_file": metadata.get("source_file"),
                    "doc_id": metadata.get("doc_id"),
                    "document_id": metadata.get("document_id"),
                    "version": metadata.get("version"),
                    "clause_id": metadata.get("clause_id"),
                    "chunk_heading": metadata.get("chunk_heading"),
                    "matched_text": evidence,
                    "char_start": None,
                    "char_end": None,
                    "match_type": "normalized",
                }

                if score > best_score:
                    best_score = score
                    best_result = citation

                continue

            # 4) Fallback: tính độ overlap token để chọn chunk gần nhất
            normalized_text_tokens = set(normalized_text.split())
            overlap = evidence_tokens.intersection(normalized_text_tokens)
            overlap_score = len(overlap)

            if overlap_score > best_score and overlap_score > 0:
                citation = {
                    "source_file": metadata.get("source_file"),
                    "doc_id": metadata.get("doc_id"),
                    "document_id": metadata.get("document_id"),
                    "version": metadata.get("version"),
                    "clause_id": metadata.get("clause_id"),
                    "chunk_heading": metadata.get("chunk_heading"),
                    "matched_text": evidence,
                    "char_start": None,
                    "char_end": None,
                    "match_type": "token_overlap",
                }

                best_score = overlap_score
                best_result = citation

        return best_result


    def _attach_citations_to_result(
        self,
        result: Dict[str, Any],
        original_docs: List[Any],
        revised_docs: List[Any],
    ) -> Dict[str, Any]:
        changes = result.get("changes", [])

        if not isinstance(changes, list):
            return result

        for change in changes:
            evidence_from_original = change.get("evidence_from_original")
            evidence_from_revised = change.get("evidence_from_revised")

            original_citation = self._find_best_citation(
                evidence=evidence_from_original,
                docs=original_docs,
            ) if evidence_from_original else {}

            revised_citation = self._find_best_citation(
                evidence=evidence_from_revised,
                docs=revised_docs,
            ) if evidence_from_revised else {}

            change["citations"] = {
                "original": original_citation if original_citation else None,
                "revised": revised_citation if revised_citation else None,
            }

        return result


    def _merge_unique_texts(self, items: List[Any]) -> str:
        seen = set()
        merged = []

        for item in items:
            text = self._extract_text(item)
            if text and text not in seen:
                seen.add(text)
                merged.append(text)

        return "\n\n".join(merged).strip()

    def _pick_pair_sides(self, pair: Any) -> Tuple[List[Any], List[Any]]:
        if isinstance(pair, tuple) and len(pair) == 2:
            return self._normalize_to_list(pair[0]), self._normalize_to_list(pair[1])

        if isinstance(pair, list) and len(pair) == 2:
            return self._normalize_to_list(pair[0]), self._normalize_to_list(pair[1])

        if not isinstance(pair, dict):
            return [], []

        lowered = {str(k).lower(): v for k, v in pair.items()}

        original_candidates = [
            "original",
            "original_docs",
            "docs_original",
            "version_a",
            "a",
            "ban_goc",
            "bản_gốc",
            "bản gốc",
            "source_a",
            "left",
        ]

        revised_candidates = [
            "revised",
            "revised_docs",
            "docs_revised",
            "version_b",
            "b",
            "ban_sua_doi",
            "bản_sửa_đổi",
            "bản sửa đổi",
            "source_b",
            "right",
        ]

        original_value = None
        revised_value = None

        for key in original_candidates:
            if key in lowered:
                original_value = lowered[key]
                break

        for key in revised_candidates:
            if key in lowered:
                revised_value = lowered[key]
                break

        return self._normalize_to_list(original_value), self._normalize_to_list(
            revised_value
        )

    def _build_presence_only_result(
        self,
        document_id: str,
        clause_id: str,
        status: str,
        original_text: str,
        revised_text: str,
        original_docs: List[Any],
        revised_docs: List[Any],
    ) -> Dict[str, Any]:
        if status == "added":
            summary = f"{clause_id} chỉ xuất hiện ở bản sửa đổi."
        elif status == "removed":
            summary = f"{clause_id} chỉ xuất hiện ở bản gốc."
        else:
            summary = f"Không đủ dữ liệu để kết luận cho {clause_id}."

        result = {
            "document_id": document_id,
            "clause_id": clause_id,
            "status": status,
            "changes": [],
            "note": "Kết quả được xác định trực tiếp từ retrieval.",
            "retrieval_context": {
                "original_count": len(original_docs),
                "revised_count": len(revised_docs),
                "original_metadata": [
                    self._extract_metadata(doc) for doc in original_docs
                ],
                "revised_metadata": [
                    self._extract_metadata(doc) for doc in revised_docs
                ],
            },
        }

        if status in {"added", "removed"}:
            result["changes"].append(
                {
                    "change_type": status,
                    "summary": summary,
                    "evidence_from_original": original_text if original_text else None,
                    "evidence_from_revised": revised_text if revised_text else None,
                    "confidence": "high",
                }
            )

        return result

    def compare_clause_texts(
        self, document_id: str, clause_id: str, original_text: str, revised_text: str
    ) -> Dict[str, Any]:
        system_prompt = COMPARE_SYSTEM_PROMPT
        user_prompt = build_compare_user_prompt(
            document_id=document_id,
            clause_id=clause_id,
            original_text=original_text,
            revised_text=revised_text,
        )
        
        try:
            raw_output = self._call_ollama(system_prompt, user_prompt)
            print("\n[RAW OLLAMA OUTPUT]")
            print(raw_output)

            result = self._parse_json_output(raw_output)
            print("\n[PARSED RESULT]")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        except Exception as e:
            print("\n[COMPARE ERROR]")
            print(repr(e))
            return build_safe_fallback(document_id, clause_id)

        if not validate_compare_output(result):
            print("\n[VALIDATION FAILED]")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return build_safe_fallback(document_id, clause_id)

        return result
        

    def compare_clause_with_retrieval(
        self,
        retriever: Any,
        document_id: str,
        clause_id: str,
        k: int = 4
    ) -> Dict[str, Any]:
        try:
            pair = retriever.retrieve_clause_pair(
                document_id=document_id,
                clause_id=clause_id,
                k=k,
            )
        except Exception:
            return build_safe_fallback(document_id, clause_id)

        original_docs, revised_docs = self._pick_pair_sides(pair)

        original_text = self._merge_unique_texts(original_docs)
        revised_text = self._merge_unique_texts(revised_docs)

        if not original_text and not revised_text:
            return build_safe_fallback(document_id, clause_id)

        if not original_text and revised_text:
            result = self._build_presence_only_result(
                document_id=document_id,
                clause_id=clause_id,
                status="added",
                original_text=original_text,
                revised_text=revised_text,
                original_docs=original_docs,
                revised_docs=revised_docs,
            )
        elif original_text and not revised_text:
            result = self._build_presence_only_result(
                document_id=document_id,
                clause_id=clause_id,
                status="removed",
                original_text=original_text,
                revised_text=revised_text,
                original_docs=original_docs,
                revised_docs=revised_docs,
            )
        else:
            result = self.compare_clause_texts(
                document_id=document_id,
                clause_id=clause_id,
                original_text=original_text,
                revised_text=revised_text,
            )

        result = self._attach_citations_to_result(
            result=result,
            original_docs=original_docs,
            revised_docs=revised_docs,
        )

        result["retrieval_context"] = {
            "original_count": len(original_docs),
            "revised_count": len(revised_docs),
            "original_metadata": [self._extract_metadata(doc) for doc in original_docs],
            "revised_metadata": [self._extract_metadata(doc) for doc in revised_docs],
        }

        return result




    def compare_clause_list(
        self, retriever: Any, document_id: str, clause_ids: List[str], k: int = 4
    ) -> Dict[str, Any]:
        results = []

        for clause_id in clause_ids:
            clause_result = self.compare_clause_with_retrieval(
                retriever=retriever,
                document_id=document_id,
                clause_id=clause_id,
                k=k,
            )
            results.append(clause_result)

        changed_results = [
            item
            for item in results
            if item.get("status") in {"added", "removed", "modified"}
        ]

        return {
            "document_id": document_id,
            "total_clauses": len(clause_ids),
            "changed_clauses": len(changed_results),
            "results": results,
        }

    def generate_summary_report(
        self,
        document_id: str,
        compare_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_prompt = REPORT_SYSTEM_PROMPT
        user_prompt = build_report_user_prompt(
            document_id=document_id,
            compare_results=compare_results,
        )

        try:
            raw_output = self._call_ollama(system_prompt, user_prompt)
            print("\n[RAW REPORT OUTPUT]")
            print(raw_output)

            result = self._parse_report_output(raw_output)
            print("\n[PARSED REPORT RESULT]")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            result = self._normalize_report_output(result)
        except Exception as e:
            print("\n[REPORT ERROR]")
            print(repr(e))
            return {
                "overview": "Không đủ dữ liệu để tóm tắt.",
                "key_changes": [],
                "risk_note": "Chỉ mô tả khác biệt văn bản, không đánh giá pháp lý."
            }

        return result
    
    def build_compare_report(
        self,
        retriever: Any,
        document_id: str,
        clause_ids: List[str],
        k: int = 4
    ) -> Dict[str, Any]:
        compare_results = self.compare_clause_list(
            retriever=retriever,
            document_id=document_id,
            clause_ids=clause_ids,
            k=k,
        )

        summary_report = self.generate_summary_report(
            document_id=document_id,
            compare_results=compare_results,
        )

        compare_results["summary_report"] = summary_report
        return compare_results