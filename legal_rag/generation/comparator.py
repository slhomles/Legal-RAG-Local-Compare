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
    LLM_NUM_CTX,
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
        Truy xuất chunks cho cả hai phiên bản và ghép cặp theo ngữ nghĩa.

        Returns:
            paired_data: {key: {version: joined_text}}
            metadata_lookup: {key: metadata dict}
        """
        filter_dict = {
            "$and": [
                {"doc_id": doc_id},
                {"version": {"$in": [version_old, version_new]}},
            ]
        }

        results = self.retriever.retrieve(
            query=f"hợp đồng {doc_id}",
            k=k,
            filter_dict=filter_dict,
        )

        # Ghép cặp theo ngữ nghĩa (cosine similarity của embeddings)
        embedding_model = self.retriever.vector_store.embeddings
        paired_data = self.context_pairer.pair_chunks_semantic(
            retrieved_chunks=results,
            embedding_model=embedding_model,
            version_old=version_old,
            version_new=version_new,
        )

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

        # Neu Ollama khong kha dung, dung rule-based fallback
        if raw_response.startswith("[LỖI]") or raw_response.startswith("[LOI]"):
            changes = self._rule_based_changes(text_old, text_new)
        else:
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
            "format": "json",
            "options": {
                "temperature": LLM_TEMPERATURE,
                "num_predict": LLM_MAX_TOKENS,
                "num_ctx": LLM_NUM_CTX,
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return self._sanitize_raw_json(content)
        except requests.ConnectionError:
            return "[LỖI] Không thể kết nối đến Ollama. Hãy đảm bảo Ollama đang chạy tại " + OLLAMA_BASE_URL
        except requests.Timeout:
            return f"[LỖI] Ollama phản hồi quá thời gian chờ (timeout {LLM_TIMEOUT}s)."
        except Exception as exc:
            return f"[LỖI] Lỗi khi gọi LLM: {exc}"

    @staticmethod
    def _sanitize_raw_json(raw: str) -> str:
        """
        Nếu raw là JSON có `changes`, loại bỏ các entry vô nghĩa
        (old_text trùng new_text, kể cả cả hai rỗng) và serialize lại.
        Dùng để raw_llm_response hiển thị trong debug đã sạch.
        """
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
        if not isinstance(data, dict) or not isinstance(data.get("changes"), list):
            return raw

        def _norm(s: object) -> str:
            return " ".join(str(s or "").split()).lower()

        cleaned = []
        for ch in data["changes"]:
            if not isinstance(ch, dict):
                continue
            if _norm(ch.get("old_text")) == _norm(ch.get("new_text")):
                continue
            cleaned.append(ch)
        data["changes"] = cleaned
        return json.dumps(data, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # RULE-BASED FALLBACK (dung khi Ollama khong kha dung)
    # ------------------------------------------------------------------
    @staticmethod
    def _rule_based_changes(
        text_old: str,
        text_new: str,
    ) -> List[Dict[str, str]]:
        """
        Phat hien thay doi don gian bang cach so sanh text truc tiep.
        Tra ve 1 change SUA neu noi dung khac nhau, danh sach rong neu giong nhau.
        """
        if text_old.strip() == text_new.strip():
            return []
        return [{
            "type": "SỬA",
            "old_text": text_old.strip()[:300],
            "new_text": text_new.strip()[:300],
            "location": "Rule-based (Ollama không khả dụng)",
        }]

    # ------------------------------------------------------------------
    # PARSE — trích xuất thay đổi từ output LLM
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_changes(raw_response: str) -> List[Dict[str, str]]:
        """
        Parse JSON response từ Ollama (đã bật format="json").
        Schema kỳ vọng: {"changes": [{"type", "old_text", "new_text", "location"}]}.
        """
        _TYPE_MAP = {
            "THÊM": "THÊM", "THEM": "THÊM", "ADD": "THÊM",
            "XOÁ": "XOÁ",  "XOA": "XOÁ",  "XÓA": "XOÁ", "DELETE": "XOÁ", "REMOVE": "XOÁ",
            "SỬA": "SỬA",  "SUA": "SỬA",  "MODIFY": "SỬA", "EDIT": "SỬA", "CHANGE": "SỬA",
        }

        try:
            data = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            return [{
                "type": "RAW", "old_text": "", "new_text": "",
                "location": "", "raw": raw_response,
            }]

        if isinstance(data, list):
            raw_changes = data
        elif isinstance(data, dict):
            raw_changes = data.get("changes") or data.get("thay_doi") or []
        else:
            raw_changes = []

        changes: List[Dict[str, str]] = []
        for _ch in raw_changes:
            if not isinstance(_ch, dict):
                continue
            _t_raw = str(_ch.get("type") or _ch.get("loai") or "").strip().upper()
            _old_raw = _ch.get("old_text") if _ch.get("old_text") is not None else _ch.get("cu", "")
            _new_raw = _ch.get("new_text") if _ch.get("new_text") is not None else _ch.get("moi", "")
            _loc_raw = _ch.get("location") if _ch.get("location") is not None else _ch.get("vi_tri", "")
            changes.append({
                "type": _TYPE_MAP.get(_t_raw, _t_raw),
                "old_text": str(_old_raw).strip().strip("«»\"'"),
                "new_text": str(_new_raw).strip().strip("«»\"'"),
                "location": str(_loc_raw).strip(),
            })

        # (regex fallback cũ đã bị bỏ — Ollama với format="json" đảm bảo JSON hợp lệ)

        _DELETE_ME_OLDPAT = re.compile(
            r"\*{0,2}(?:N[ộo]i dung c[ũu]|N[ộo]i dung cu)\*{0,2}"
            r"\s*[:：]\s*[«\"'\u2018\u201c]?(.*?)[»\"'\u2019\u201d]?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        # Nội dung mới — chấp nhận cả có và không dấu
        new_pattern = re.compile(
            r"\*{0,2}(?:N[ộo]i dung m[ớo]i|N[ộo]i dung moi)\*{0,2}"
            r"\s*[:：]\s*[«\"'\u2018\u201c]?(.*?)[»\"'\u2019\u201d]?\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        # Vị trí — chấp nhận cả có và không dấu
        loc_pattern = re.compile(
            r"\*{0,2}(?:V[ịi] tr[ií]|Vi tri)\*{0,2}\s*[:：]\s*(.*?)$",
            re.IGNORECASE | re.MULTILINE,
        )


        # Sanity filter + dedup cho output model nhỏ hay lặp/bịa:
        #   (a) bỏ change có old == new (SỬA X → X vô nghĩa).
        #   (b) dedup theo (type, old_norm, new_norm).
        #   (c) bỏ change là phép đảo ngược của một change đã có trước đó
        #       (vd: «50% → 40%» rồi «40% → 50%» — model 1.5B hay bịa kiểu này).
        seen_triples: set = set()
        seen_unordered_pairs: set = set()
        deduped: List[Dict[str, str]] = []
        for ch in changes:
            old_norm = " ".join(ch["old_text"].split()).lower()
            new_norm = " ".join(ch["new_text"].split()).lower()

            if old_norm == new_norm:
                continue

            triple = (ch["type"], old_norm, new_norm)
            if triple in seen_triples:
                continue

            pair = frozenset({old_norm, new_norm})
            if old_norm and new_norm and pair in seen_unordered_pairs:
                continue

            seen_triples.add(triple)
            seen_unordered_pairs.add(pair)
            deduped.append(ch)
        changes = deduped

        # Fallback: nếu không parse được, giữ nguyên response để hiển thị
        _no_change_phrases = ("không phát hiện thay đổi", "khong phat hien thay doi")
        if not changes and not any(p in raw_response.lower() for p in _no_change_phrases):
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
        base_id = clause_id.split("_new")[0] if "_new" in clause_id else clause_id
        meta = metadata_lookup.get(base_id, {})
        return meta.get("chunk_heading", base_id)
