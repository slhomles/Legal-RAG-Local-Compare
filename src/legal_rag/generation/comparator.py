# Gọi API Ollama (Qwen 2.5) để so sánh, phát hiện thêm/xóa/sửa và tóm tắt [cite: 17]

import json
from typing import Any, Dict, List, Tuple

import requests

from legal_rag.generation.prompts import (
    COMPARE_SYSTEM_PROMPT,
    build_compare_user_prompt,
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
        self, retriever: Any, document_id: str, clause_id: str, k: int = 4
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
            return self._build_presence_only_result(
                document_id=document_id,
                clause_id=clause_id,
                status="added",
                original_text=original_text,
                revised_text=revised_text,
                original_docs=original_docs,
                revised_docs=revised_docs,
            )

        if original_text and not revised_text:
            return self._build_presence_only_result(
                document_id=document_id,
                clause_id=clause_id,
                status="removed",
                original_text=original_text,
                revised_text=revised_text,
                original_docs=original_docs,
                revised_docs=revised_docs,
            )

        result = self.compare_clause_texts(
            document_id=document_id,
            clause_id=clause_id,
            original_text=original_text,
            revised_text=revised_text,
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
