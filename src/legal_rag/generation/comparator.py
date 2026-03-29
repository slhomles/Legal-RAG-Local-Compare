# Gọi API Ollama (Qwen 2.5) để so sánh, phát hiện thêm/xóa/sửa và tóm tắt [cite: 17]

import json
from typing import Any, Dict

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
        ollama_url: str = "http://localhost:11434/api/generate",
    ):
        self.model_name = model_name
        self.ollama_url = ollama_url

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
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
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            start = raw_output.find("{")
            end = raw_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_output[start:end + 1]
                return json.loads(candidate)
            raise

    def compare_clause_texts(
        self,
        document_id: str,
        clause_id: str,
        original_text: str,
        revised_text: str
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
            result = self._parse_json_output(raw_output)
        except Exception:
            return build_safe_fallback(document_id, clause_id)

        if not validate_compare_output(result):
            return build_safe_fallback(document_id, clause_id)

        return result