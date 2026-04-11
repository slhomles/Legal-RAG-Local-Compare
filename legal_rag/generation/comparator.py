# ---------------------------------------------------------------------------
# Module so sánh hai phiên bản hợp đồng thông qua RAG + LLM (Ollama/Qwen 2.5).
#
# Luồng xử lý:
#   1. Truy xuất chunks hai phiên bản từ ChromaDB (metadata filter)
#   2. Ghép cặp theo logical_id qua ContextPairer
#   3. Gọi LLM phân tích thêm/xoá/sửa cho từng cặp điều khoản
#   4. Trả về danh sách thay đổi có cấu trúc
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import requests

from legal_rag.config import (
    LLM_MAX_TOKENS,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_BASE_URL,
)
from legal_rag.generation.prompts import (
    COMPARISON_USER_TEMPLATE,
    SYSTEM_PROMPT,
    check_guardrails,
)
from legal_rag.retrieval.context_pairing import ContextPairer
from legal_rag.retrieval.retriever import LegalRetriever


class DocumentComparator:
    """
    So sánh hai phiên bản của một hợp đồng, trả về danh sách thay đổi có cấu trúc.
    """

    def __init__(
        self,
        retriever: Optional[LegalRetriever] = None,
        context_pairer: Optional[ContextPairer] = None,
    ) -> None:
        self.retriever = retriever or LegalRetriever()
        self.context_pairer = context_pairer or ContextPairer()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def compare_versions(
        self,
        doc_id: str,
        version_old: str = "v1",
        version_new: str = "v2",
        clause_ids: Optional[List[str]] = None,
        k: int = 20,
    ) -> Dict[str, Any]:
        """
        So sánh hai phiên bản hợp đồng, trả về dict:
        {
            "doc_id": "Hop_dong_A",
            "version_old": "v1",
            "version_new": "v2",
            "clauses": {
                "dieu_1": {
                    "heading": "Điều 1. ...",
                    "changes": [...],
                    "guardrail_ok": True
                },
                ...
            },
            "new_clauses": ["dieu_6"],
            "removed_clauses": []
        }
        """
        # Bước 1: Truy xuất và ghép cặp chunks
        paired_data, metadata_lookup = self._retrieve_and_pair(
            doc_id, version_old, version_new, k
        )

        # Bước 2: Lọc clause_ids nếu được chỉ định
        if clause_ids:
            paired_data = {
                cid: versions
                for cid, versions in paired_data.items()
                if cid in clause_ids
            }

        # Bước 3: Phân loại điều khoản
        all_clause_ids = set(paired_data.keys())
        new_clauses = [
            cid for cid in all_clause_ids
            if version_old not in paired_data[cid] and version_new in paired_data[cid]
        ]
        removed_clauses = [
            cid for cid in all_clause_ids
            if version_old in paired_data[cid] and version_new not in paired_data[cid]
        ]
        common_clauses = [
            cid for cid in all_clause_ids
            if version_old in paired_data[cid] and version_new in paired_data[cid]
        ]

        # Bước 4: Phân tích thay đổi cho từng cặp điều khoản
        clauses_result: Dict[str, Any] = {}

        for clause_id in common_clauses:
            text_old = paired_data[clause_id][version_old]
            text_new = paired_data[clause_id][version_new]
            heading = self._get_heading(metadata_lookup, clause_id)

            changes, raw_response = self._detect_changes(
                clause_heading=heading or clause_id,
                text_old=text_old,
                text_new=text_new,
                version_old=version_old,
                version_new=version_new,
            )

            is_clean, violations = check_guardrails(raw_response)
            clauses_result[clause_id] = {
                "heading": heading,
                "changes": changes,
                "raw_llm_response": raw_response,
                "guardrail_ok": is_clean,
                "guardrail_violations": violations,
            }

        # Bước 5: Ghi nhận điều khoản mới
        for clause_id in new_clauses:
            heading = self._get_heading(metadata_lookup, clause_id)
            text_new = paired_data[clause_id].get(version_new, "")
            clauses_result[clause_id] = {
                "heading": heading,
                "changes": [{
                    "type": "THÊM",
                    "old_text": "",
                    "new_text": text_new,
                    "location": f"Điều khoản mới trong {version_new}",
                }],
                "raw_llm_response": "",
                "guardrail_ok": True,
                "guardrail_violations": [],
            }

        # Bước 6: Ghi nhận điều khoản bị xoá
        for clause_id in removed_clauses:
            heading = self._get_heading(metadata_lookup, clause_id)
            text_old = paired_data[clause_id].get(version_old, "")
            clauses_result[clause_id] = {
                "heading": heading,
                "changes": [{
                    "type": "XOÁ",
                    "old_text": text_old,
                    "new_text": "",
                    "location": f"Điều khoản bị xoá trong {version_new}",
                }],
                "raw_llm_response": "",
                "guardrail_ok": True,
                "guardrail_violations": [],
            }

        return {
            "doc_id": doc_id,
            "version_old": version_old,
            "version_new": version_new,
            "clauses": clauses_result,
            "new_clauses": new_clauses,
            "removed_clauses": removed_clauses,
        }

    # ------------------------------------------------------------------
    # RETRIEVAL + PAIRING
    # ------------------------------------------------------------------
    def _retrieve_and_pair(
        self,
        doc_id: str,
        version_old: str,
        version_new: str,
        k: int,
    ) -> tuple[Dict[str, Dict[str, str]], Dict[str, Dict]]:
        """
        Truy xuất chunks cho cả hai phiên bản và ghép cặp theo logical_id.

        Returns:
            paired_data: {logical_id: {version: joined_text}}
            metadata_lookup: {logical_id: {first metadata dict encountered}}
        """
        filter_dict = {
            "$and": [
                {"doc_id": doc_id},
                {"version": {"$in": [version_old, version_new]}},
            ]
        }

        # Dùng query tổng quát để lấy tất cả chunks — nội dung query không quan trọng
        # vì metadata filter mới là yếu tố quyết định
        results = self.retriever.retrieve(
            query=f"hợp đồng {doc_id}",
            k=k,
            filter_dict=filter_dict,
        )

        # Ghép cặp theo logical_id → version
        paired_data = self.context_pairer.pair_chunks(results)

        # Xây dựng metadata lookup
        metadata_lookup: Dict[str, Dict] = {}
        for chunk in results:
            lid = chunk.get("metadata", {}).get("logical_id", "")
            if lid and lid not in metadata_lookup:
                metadata_lookup[lid] = chunk["metadata"]

        return paired_data, metadata_lookup

    # ------------------------------------------------------------------
    # LLM — PHÁT HIỆN THAY ĐỔI
    # ------------------------------------------------------------------
    def _detect_changes(
        self,
        clause_heading: str,
        text_old: str,
        text_new: str,
        version_old: str,
        version_new: str,
    ) -> tuple[List[Dict[str, str]], str]:
        """
        Gọi LLM để phân tích thay đổi giữa hai phiên bản của một điều khoản.

        Returns:
            (parsed_changes, raw_response)
        """
        user_prompt = COMPARISON_USER_TEMPLATE.format(
            clause_heading=clause_heading,
            version_old=version_old,
            version_new=version_new,
            text_old=text_old,
            text_new=text_new,
        )

        raw_response = self._call_llm(SYSTEM_PROMPT, user_prompt)
        changes = self._parse_changes(raw_response)
        return changes, raw_response

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Gọi Ollama API (chat endpoint) với Qwen 2.5.
        Trả về nội dung phản hồi dạng text.
        """
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": LLM_TEMPERATURE,
                "num_predict": LLM_MAX_TOKENS,
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except requests.ConnectionError:
            return "[LỖI] Không thể kết nối đến Ollama. Hãy đảm bảo Ollama đang chạy tại " + OLLAMA_BASE_URL
        except requests.Timeout:
            return f"[LỖI] Ollama phản hồi quá thời gian chờ (timeout {LLM_TIMEOUT}s)."
        except Exception as exc:
            return f"[LỖI] Lỗi khi gọi LLM: {exc}"

    # ------------------------------------------------------------------
    # PARSE — trích xuất thay đổi từ output LLM
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_changes(raw_response: str) -> List[Dict[str, str]]:
        """
        Parse output LLM thành danh sách thay đổi có cấu trúc.
        Tìm các block có format:
            - **Loại thay đổi**: THÊM | XOÁ | SỬA
            - **Nội dung cũ**: «...»
            - **Nội dung mới**: «...»
            - **Vị trí**: ...
        """
        changes: List[Dict[str, str]] = []

        # Pattern linh hoạt để parse output LLM
        type_pattern = re.compile(
            r"\*{0,2}Loại thay đổi\*{0,2}\s*[:：]\s*(THÊM|XOÁ|XÓA|SỬA)",
            re.IGNORECASE,
        )
        old_pattern = re.compile(
            r"\*{0,2}N\u1ed9i dung c\u0169\*{0,2}\s*[:\uff1a]\s*[\u00ab\"'\u2018\u201c]?(.*?)[\u00bb\"'\u2019\u201d]?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        new_pattern = re.compile(
            r"\*{0,2}N\u1ed9i dung m\u1edbi\*{0,2}\s*[:\uff1a]\s*[\u00ab\"'\u2018\u201c]?(.*?)[\u00bb\"'\u2019\u201d]?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        loc_pattern = re.compile(
            r"\*{0,2}Vị trí\*{0,2}\s*[:：]\s*(.*?)$",
            re.IGNORECASE | re.MULTILINE,
        )

        # Tách thành các block bằng pattern "Loại thay đổi"
        type_matches = list(type_pattern.finditer(raw_response))

        for i, tmatch in enumerate(type_matches):
            start = tmatch.start()
            end = type_matches[i + 1].start() if i + 1 < len(type_matches) else len(raw_response)
            block = raw_response[start:end]

            change_type = tmatch.group(1).upper()
            if change_type == "XÓA":
                change_type = "XOÁ"

            old_m = old_pattern.search(block)
            new_m = new_pattern.search(block)
            loc_m = loc_pattern.search(block)

            changes.append({
                "type": change_type,
                "old_text": (old_m.group(1).strip() if old_m else ""),
                "new_text": (new_m.group(1).strip() if new_m else ""),
                "location": (loc_m.group(1).strip() if loc_m else ""),
            })

        # Fallback: nếu không parse được theo format chuẩn, trả response nguyên bản
        if not changes and "Không phát hiện thay đổi" not in raw_response:
            changes.append({
                "type": "RAW",
                "old_text": "",
                "new_text": "",
                "location": "",
                "raw": raw_response,
            })

        return changes

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _get_heading(metadata_lookup: Dict[str, Dict], clause_id: str) -> str:
        meta = metadata_lookup.get(clause_id, {})
        return meta.get("chunk_heading", clause_id)
