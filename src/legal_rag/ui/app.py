# ---------------------------------------------------------------------------
# Giao dien chat bot so sanh hai phien ban hop dong phap ly.
#
# Chuc nang:
#   - Tai len 2 file DOCX (phien ban cu va moi)
#   - Nhap "so sanh" de chat bot phan tich va tra ve bao cao thay doi
#   - Hien thi chi tiet thay doi, trich dan va tom tat
#
# Su dung:
#   python run_ui.py
# ---------------------------------------------------------------------------
from __future__ import annotations

import os
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from legal_rag.config import RAW_DATA_DIR
from legal_rag.db.vector_store import VectorStoreManager
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.report import ReportGenerator
from legal_rag.ingest.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_doc_info(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Trich xuat doc_id va version tu ten file (VD: Hop_dong_A_v1.docx)."""
    m = re.match(r"(.+?)_(v\d+)\.docx$", filename, re.IGNORECASE)
    return (m.group(1), m.group(2)) if m else (None, None)


def _ingest_files(
    path_old: str, path_new: str
) -> Tuple[str, str, str, int]:
    """
    Xu ly 2 file DOCX: trich xuat doc_id/version, chunk, luu vao ChromaDB.
    Tra ve (doc_id, version_old, version_new, so_chunks).
    """
    name_old = os.path.basename(path_old)
    name_new = os.path.basename(path_new)

    doc_id_old, ver_old = _extract_doc_info(name_old)
    doc_id_new, ver_new = _extract_doc_info(name_new)

    doc_id = doc_id_old or re.sub(r"\.docx$", "", name_old, flags=re.IGNORECASE)
    version_old = ver_old or "v1"
    version_new = ver_new or "v2"

    # Copy vao data/raw/ theo quy uoc dat ten
    target_old = str(RAW_DATA_DIR / f"{doc_id}_{version_old}.docx")
    target_new = str(RAW_DATA_DIR / f"{doc_id}_{version_new}.docx")
    shutil.copy2(path_old, target_old)
    shutil.copy2(path_new, target_new)

    # Xu ly va luu vao ChromaDB
    processor = DocumentProcessor()
    store = VectorStoreManager()
    store.reset_collection()

    all_chunks: List[Dict[str, Any]] = []
    for fpath in [target_old, target_new]:
        chunks = processor.process_file(fpath)
        all_chunks.extend(chunks)

    store.add_documents(all_chunks)
    return doc_id, version_old, version_new, len(all_chunks)


def _run_comparison(
    doc_id: str, version_old: str, version_new: str
) -> Tuple[Dict[str, Any], str]:
    """Chay pipeline: comparator -> citation -> report."""
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(
        doc_id=doc_id,
        version_old=version_old,
        version_new=version_new,
        k=20,
    )

    citation_mapper = CitationMapper(retriever=comparator.retriever)
    enriched = citation_mapper.enrich_changes(comparison)

    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)
    report_text = report_gen.format_plain_text(report)
    return report, report_text


# ---------------------------------------------------------------------------
# Chat logic
# ---------------------------------------------------------------------------

_state: Dict[str, Any] = {
    "doc_id": None,
    "ver_old": None,
    "ver_new": None,
    "report_text": None,
}

WELCOME = (
    "Xin chao! Toi la tro ly so sanh hop dong phap ly.\n\n"
    "**Cach su dung:**\n"
    "1. Tai len 2 file DOCX (phien ban cu va moi) o phia tren\n"
    "2. Nhap **so sanh** de bat dau phan tich\n"
    "3. Doi de nhan bao cao thay doi\n\n"
    "*Luu y: Qua trinh phan tich co the mat vai phut neu chay LLM tren CPU.*"
)

_COMPARE_KW = ["so sanh", "bao cao", "report", "compare", "phan tich", "thay doi"]
_REVIEW_KW = ["chi tiet", "xem lai", "detail", "xem"]


def handle_message(
    message: str,
    history: List[Dict[str, str]],
    file_old: Optional[str],
    file_new: Optional[str],
) -> Tuple[List[Dict[str, str]], str]:
    """Xu ly tin nhan tu nguoi dung, tra ve (history, cleared_textbox)."""
    if not message or not message.strip():
        return history, ""

    history = history + [{"role": "user", "content": message}]
    msg_lower = message.lower().strip()

    # --- Kiem tra file ---
    if file_old is None or file_new is None:
        history += [
            {
                "role": "assistant",
                "content": "Vui long tai len ca 2 file DOCX (phien ban cu va moi) truoc khi bat dau.",
            }
        ]
        return history, ""

    # --- Lenh so sanh ---
    if any(kw in msg_lower for kw in _COMPARE_KW):
        _state["doc_id"] = None
        _state["report_text"] = None

        # Buoc 1: Ingest
        try:
            doc_id, ver_old, ver_new, n_chunks = _ingest_files(file_old, file_new)
            _state["doc_id"] = doc_id
            _state["ver_old"] = ver_old
            _state["ver_new"] = ver_new
        except Exception as exc:
            history += [{"role": "assistant", "content": f"Loi khi xu ly tai lieu:\n```\n{exc}\n```"}]
            return history, ""

        # Buoc 2: So sanh
        try:
            _, report_text = _run_comparison(doc_id, ver_old, ver_new)
            _state["report_text"] = report_text
            header = (
                f"Da phan tich **{n_chunks}** doan van ban "
                f"(`{doc_id}`: {ver_old} -> {ver_new}).\n\n"
            )
            history += [{"role": "assistant", "content": header + report_text}]
        except Exception as exc:
            history += [{"role": "assistant", "content": f"Loi khi so sanh:\n```\n{exc}\n```"}]

        return history, ""

    # --- Xem lai bao cao ---
    if any(kw in msg_lower for kw in _REVIEW_KW) and _state.get("report_text"):
        history += [{"role": "assistant", "content": _state["report_text"]}]
        return history, ""

    # --- Mac dinh ---
    history += [
        {
            "role": "assistant",
            "content": (
                "Ban co the:\n"
                "- Nhap **so sanh** de phan tich hai phien ban hop dong\n"
                "- Nhap **xem lai** de xem lai bao cao truoc do\n"
                "- Tai len 2 file DOCX moi de so sanh tai lieu khac"
            ),
        }
    ]
    return history, ""


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="Legal RAG - So sanh hop dong",
    ) as app:
        gr.Markdown("# Legal RAG - So sanh hop dong phap ly")
        gr.Markdown(
            "Tai len **2 phien ban** hop dong (`.docx`) roi nhap `so sanh` de nhan bao cao thay doi.  \n"
            "Ten file theo quy uoc `TenTaiLieu_v1.docx`, `TenTaiLieu_v2.docx` "
            "(VD: `Hop_dong_A_v1.docx`, `Hop_dong_A_v2.docx`)."
        )

        with gr.Row():
            file_old = gr.File(
                label="Phien ban cu (v1)",
                file_types=[".docx"],
            )
            file_new = gr.File(
                label="Phien ban moi (v2)",
                file_types=[".docx"],
            )

        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME}],
            label="Chat",
            height=500,
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Nhap 'so sanh' de bat dau phan tich...",
                show_label=False,
                scale=4,
            )
            send_btn = gr.Button("Gui", variant="primary", scale=1)

        # Events
        send_btn.click(
            handle_message,
            inputs=[msg, chatbot, file_old, file_new],
            outputs=[chatbot, msg],
        )
        msg.submit(
            handle_message,
            inputs=[msg, chatbot, file_old, file_new],
            outputs=[chatbot, msg],
        )

    return app


def main() -> None:
    app = create_app()
    app.launch(theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
