# ---------------------------------------------------------------------------
# Module tổng hợp báo cáo thay đổi quan trọng giữa hai phiên bản hợp đồng.
#
# Luồng:
#   1. Nhận danh sách thay đổi (output từ DocumentComparator + CitationMapper)
#   2. Định dạng thành văn bản đầu vào cho LLM
#   3. Gọi LLM với SUMMARY_USER_TEMPLATE để tóm tắt
#   4. Kiểm tra guardrails trước khi trả kết quả
# ---------------------------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, List

import requests

from legal_rag.config import (
    LLM_MAX_TOKENS,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    OLLAMA_BASE_URL,
)
from legal_rag.generation.prompts import (
    GUARDRAIL_WARNING,
    SUMMARY_USER_TEMPLATE,
    SYSTEM_PROMPT,
    check_guardrails,
)


class ReportGenerator:
    """
    Sinh báo cáo tóm tắt các thay đổi quan trọng giữa hai phiên bản hợp đồng.
    """

    def generate_report(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nhận kết quả từ DocumentComparator (đã qua CitationMapper nếu có)
        và sinh báo cáo tóm tắt.

        Returns:
            {
                "doc_id": "Hop_dong_A",
                "version_old": "v1",
                "version_new": "v2",
                "changes_detail": [...],
                "summary": "...",
                "guardrail_ok": True,
                "guardrail_violations": []
            }
        """
        doc_id = comparison_result["doc_id"]
        version_old = comparison_result["version_old"]
        version_new = comparison_result["version_new"]

        # Bước 1: Tập hợp tất cả thay đổi thành văn bản
        changes_detail = self._collect_changes(comparison_result)
        changes_text = self._format_changes_text(changes_detail)

        # Bước 2: Gọi LLM để tóm tắt
        if not changes_detail:
            summary = "Khong phat hien thay doi nao giua hai phien ban."
            guardrail_ok = True
            violations = []
        else:
            user_prompt = SUMMARY_USER_TEMPLATE.format(
                doc_id=doc_id,
                version_old=version_old,
                version_new=version_new,
                changes_text=changes_text,
            )
            summary = self._call_llm(SYSTEM_PROMPT, user_prompt)
            guardrail_ok, violations = check_guardrails(summary)

            if not guardrail_ok:
                summary = f"{GUARDRAIL_WARNING}\n\n{summary}"

        return {
            "doc_id": doc_id,
            "version_old": version_old,
            "version_new": version_new,
            "changes_detail": changes_detail,
            "summary": summary,
            "guardrail_ok": guardrail_ok,
            "guardrail_violations": violations,
        }

    # ------------------------------------------------------------------
    # Thu thập & định dạng thay đổi
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_changes(comparison_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Thu thập tất cả thay đổi từ comparison_result thành danh sách phẳng,
        mỗi item gắn kèm clause_id và heading.
        """
        all_changes: List[Dict[str, Any]] = []

        for clause_id, clause_data in comparison_result.get("clauses", {}).items():
            heading = clause_data.get("heading", clause_id)
            for change in clause_data.get("changes", []):
                all_changes.append({
                    "clause_id": clause_id,
                    "heading": heading,
                    **change,
                })

        return all_changes

    @staticmethod
    def _format_changes_text(changes: List[Dict[str, Any]]) -> str:
        """
        Định dạng danh sách thay đổi thành văn bản dạng bullet list
        để đưa vào prompt LLM.
        """
        lines: List[str] = []

        for i, change in enumerate(changes, 1):
            heading = change.get("heading", "")
            change_type = change.get("type", "")
            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")
            location = change.get("location", "")

            line = f"{i}. [{heading}] Loai: {change_type}"
            if old_text:
                line += f"\n   Noi dung cu: {old_text}"
            if new_text:
                line += f"\n   Noi dung moi: {new_text}"
            if location:
                line += f"\n   Vi tri: {location}"

            # Thêm citation nếu có
            citations = change.get("citations", {})
            for source_key in ("old_source", "new_source"):
                src = citations.get(source_key, {})
                if src.get("found"):
                    chunk_id = src.get("chunk_id", "")
                    match_type = src.get("match_type", "")
                    char_start = src.get("char_start", "")
                    line += f"\n   Trich dan ({source_key}): chunk={chunk_id}, match={match_type}, pos={char_start}"

            lines.append(line)

        return "\n\n".join(lines)

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------
    @staticmethod
    def _call_llm(system_prompt: str, user_prompt: str) -> str:
        """Gọi Ollama API để sinh tóm tắt."""
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
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except requests.ConnectionError:
            return (
                "[LOI] Khong the ket noi den Ollama. "
                "Hay dam bao Ollama dang chay tai " + OLLAMA_BASE_URL
            )
        except requests.Timeout:
            return "[LOI] Ollama phan hoi qua thoi gian cho (timeout 120s)."
        except Exception as exc:
            return f"[LOI] Loi khi goi LLM: {exc}"

    # ------------------------------------------------------------------
    # Formatted plain-text output
    # ------------------------------------------------------------------
    @staticmethod
    def format_plain_text(report: Dict[str, Any]) -> str:
        """
        Xuất báo cáo dạng plain-text để in ra console hoặc lưu file.
        """
        lines: List[str] = []
        lines.append("=" * 70)
        lines.append(f"BAO CAO THAY DOI HOP DONG: {report['doc_id']}")
        lines.append(f"So sanh: {report['version_old']} -> {report['version_new']}")
        lines.append("=" * 70)

        # Chi tiết thay đổi
        lines.append("\n--- CHI TIET THAY DOI ---\n")
        for i, change in enumerate(report.get("changes_detail", []), 1):
            heading = change.get("heading", "")
            ctype = change.get("type", "")
            lines.append(f"  {i}. [{ctype}] {heading}")

            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")
            if old_text:
                lines.append(f"     Cu : {old_text[:120]}{'...' if len(old_text) > 120 else ''}")
            if new_text:
                lines.append(f"     Moi: {new_text[:120]}{'...' if len(new_text) > 120 else ''}")

            # Citation info
            citations = change.get("citations", {})
            for src_key in ("old_source", "new_source"):
                src = citations.get(src_key, {})
                if src.get("found"):
                    lines.append(
                        f"     -> {src_key}: {src.get('chunk_id', '')} "
                        f"[{src.get('match_type', '')}] pos={src.get('char_start', '')}"
                    )

            lines.append("")

        # Tóm tắt LLM
        lines.append("--- TOM TAT THAY DOI QUAN TRONG ---\n")
        lines.append(report.get("summary", "(Khong co tom tat)"))

        # Guardrail warning
        if not report.get("guardrail_ok", True):
            lines.append(f"\n{GUARDRAIL_WARNING}")
            lines.append(f"Cum tu vi pham: {report.get('guardrail_violations', [])}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
