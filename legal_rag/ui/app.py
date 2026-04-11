# ---------------------------------------------------------------------------
# Giao dien chat bot so sanh hop dong phap ly.
#
# Giao dien don gian voi:
#   - Chat bot o giua
#   - Nut "+" mo menu: Nhap tai lieu / Sinh bao cao
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from legal_rag.config import RAW_DATA_DIR
from legal_rag.db.vector_store import VectorStoreManager
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.report import ReportGenerator
from legal_rag.generation.word_report import generate_word_report
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
    """Xu ly 2 file DOCX: chunk va luu vao ChromaDB."""
    name_old = os.path.basename(path_old)
    name_new = os.path.basename(path_new)

    doc_id_old, ver_old = _extract_doc_info(name_old)
    doc_id_new, ver_new = _extract_doc_info(name_new)

    doc_id = doc_id_old or re.sub(r"\.docx$", "", name_old, flags=re.IGNORECASE)
    version_old = ver_old or "v1"
    version_new = ver_new or "v2"

    target_old = str(RAW_DATA_DIR / f"{doc_id}_{version_old}.docx")
    target_new = str(RAW_DATA_DIR / f"{doc_id}_{version_new}.docx")
    shutil.copy2(path_old, target_old)
    shutil.copy2(path_new, target_new)

    processor = DocumentProcessor()
    store = VectorStoreManager()
    store.reset_collection()

    all_chunks: List[Dict[str, Any]] = []
    for fpath in [target_old, target_new]:
        chunks = processor.process_file(fpath)
        all_chunks.extend(chunks)

    store.add_documents(all_chunks)
    return doc_id, version_old, version_new, len(all_chunks)


def _run_pipeline(
    doc_id: str, ver_old: str, ver_new: str
) -> Tuple[Dict[str, Any], str]:
    """Chay pipeline so sanh. Tra ve (report_dict, report_text)."""
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(
        doc_id=doc_id, version_old=ver_old, version_new=ver_new, k=20,
    )
    citation_mapper = CitationMapper(retriever=comparator.retriever)
    enriched = citation_mapper.enrich_changes(comparison)
    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)
    report["_enriched"] = enriched
    report_text = report_gen.format_plain_text(report)
    return report, report_text


def _generate_word(report: Dict[str, Any], doc_id: str) -> str:
    """Sinh file Word tu report dict. Tra ve duong dan file."""
    Path("output").mkdir(exist_ok=True)
    json_path = "output/report_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    output_path = f"output/bao_cao_{doc_id}.docx"
    generate_word_report(from_json=json_path, output_path=output_path)
    return output_path


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

WELCOME = (
    "Xin chao! Toi la tro ly so sanh hop dong phap ly.\n\n"
    "Nhan **+** de bat dau:\n"
    "- **Nhap tai lieu** — tai len 2 phien ban hop dong\n"
    "- **Sinh bao cao** — phan tich va xuat bao cao Word"
)

CSS = """
.welcome-title {
    text-align: center;
    padding: 48px 0 8px 0;
}
.welcome-title h1 {
    font-size: 2em;
    font-weight: 300;
    color: #1a1a1a;
}
.plus-btn {
    min-width: 42px !important;
    max-width: 42px !important;
    height: 42px !important;
    border-radius: 50% !important;
    font-size: 1.4em !important;
    padding: 0 !important;
    border: 1px solid #d0d0d0 !important;
    background: white !important;
    color: #555 !important;
}
.plus-btn:hover {
    background: #f5f5f5 !important;
    border-color: #999 !important;
}
.action-menu {
    border: 1px solid #e5e5e5;
    border-radius: 16px;
    padding: 4px 0;
    background: white;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    max-width: 260px;
    margin-top: 4px;
}
.action-item {
    border: none !important;
    background: none !important;
    text-align: left !important;
    padding: 12px 20px !important;
    font-size: 0.95em !important;
    color: #333 !important;
    border-radius: 12px !important;
    margin: 2px 4px !important;
}
.action-item:hover {
    background: #f5f5f5 !important;
}
.upload-panel {
    border: 1px solid #e5e5e5;
    border-radius: 16px;
    padding: 20px;
    background: #fafafa;
    margin-top: 8px;
}
"""


def create_app() -> gr.Blocks:
    with gr.Blocks(title="Legal RAG", css=CSS, theme=gr.themes.Soft()) as app:
        # --- State ---
        doc_state = gr.State({
            "doc_id": None, "ver_old": None, "ver_new": None,
            "ingested": False, "report_text": None,
        })
        menu_open = gr.State(False)

        # --- Layout ---
        gr.HTML("<div class='welcome-title'><h1>Legal RAG</h1></div>")

        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME}],
            height=460,
            show_label=False,
        )

        # Thanh nhap lieu
        with gr.Row():
            plus_btn = gr.Button("+", elem_classes=["plus-btn"], scale=0)
            msg = gr.Textbox(
                placeholder="Ban can ho tro gi?",
                show_label=False,
                scale=4,
                container=False,
            )
            send_btn = gr.Button("Gui", variant="primary", scale=0, min_width=60)

        # Menu chuc nang (an mac dinh)
        with gr.Column(visible=False, elem_classes=["action-menu"]) as action_menu:
            ingest_btn = gr.Button("Nhap tai lieu", elem_classes=["action-item"])
            report_btn = gr.Button("Sinh bao cao", elem_classes=["action-item"])

        # Panel upload (an mac dinh)
        with gr.Column(visible=False, elem_classes=["upload-panel"]) as upload_panel:
            gr.Markdown("**Tai len 2 phien ban hop dong (.docx)**")
            with gr.Row():
                file_old = gr.File(label="Phien ban cu (v1)", file_types=[".docx"])
                file_new = gr.File(label="Phien ban moi (v2)", file_types=[".docx"])
            with gr.Row():
                confirm_btn = gr.Button("Nhap", variant="primary", scale=1)
                cancel_btn = gr.Button("Huy", variant="secondary", scale=1)

        # File bao cao (an cho den khi sinh xong)
        report_file = gr.File(visible=False, label="Tai bao cao")

        # --- Events ---

        # Dong/mo menu
        def toggle_menu(is_open):
            return gr.Column(visible=not is_open), not is_open

        plus_btn.click(toggle_menu, [menu_open], [action_menu, menu_open])

        # Mo panel upload
        def show_upload():
            return gr.Column(visible=False), gr.Column(visible=True), False

        ingest_btn.click(show_upload, [], [action_menu, upload_panel, menu_open])

        # Dong panel upload
        cancel_btn.click(
            lambda: gr.Column(visible=False),
            [], [upload_panel],
        )

        # Nhap tai lieu
        def do_ingest(f_old, f_new, history, state):
            if f_old is None or f_new is None:
                history = history + [
                    {"role": "assistant",
                     "content": "Vui long tai len ca 2 file DOCX."}
                ]
                return history, state, gr.Column(visible=True)

            try:
                doc_id, ver_old, ver_new, n = _ingest_files(f_old, f_new)
                state = {
                    "doc_id": doc_id, "ver_old": ver_old, "ver_new": ver_new,
                    "ingested": True, "report_text": None,
                }
                history = history + [
                    {"role": "assistant",
                     "content": (
                         f"Da nhap thanh cong **{n}** doan van ban "
                         f"tu `{doc_id}` ({ver_old}, {ver_new}).\n\n"
                         f"Nhan **+** > **Sinh bao cao** de phan tich."
                     )}
                ]
            except Exception as exc:
                history = history + [
                    {"role": "assistant",
                     "content": f"Loi khi nhap tai lieu:\n```\n{exc}\n```"}
                ]

            return history, state, gr.Column(visible=False)

        confirm_btn.click(
            do_ingest,
            [file_old, file_new, chatbot, doc_state],
            [chatbot, doc_state, upload_panel],
        )

        # Sinh bao cao
        def do_report(history, state):
            if not state.get("ingested"):
                history = history + [
                    {"role": "assistant",
                     "content": "Vui long nhap tai lieu truoc khi sinh bao cao."}
                ]
                return history, state, gr.Column(visible=False), gr.File(visible=False), False

            doc_id = state["doc_id"]
            ver_old = state["ver_old"]
            ver_new = state["ver_new"]

            try:
                report, report_text = _run_pipeline(doc_id, ver_old, ver_new)
                state["report_text"] = report_text
                word_path = _generate_word(report, doc_id)

                history = history + [
                    {"role": "assistant", "content": report_text}
                ]
                return (
                    history, state,
                    gr.Column(visible=False),
                    gr.File(value=word_path, visible=True),
                    False,
                )
            except Exception as exc:
                history = history + [
                    {"role": "assistant",
                     "content": f"Loi khi sinh bao cao:\n```\n{exc}\n```"}
                ]
                return (
                    history, state,
                    gr.Column(visible=False),
                    gr.File(visible=False),
                    False,
                )

        report_btn.click(
            do_report,
            [chatbot, doc_state],
            [chatbot, doc_state, action_menu, report_file, menu_open],
        )

        # Xu ly tin nhan text
        def handle_msg(message, history, state):
            if not message or not message.strip():
                return history, state, ""

            history = history + [{"role": "user", "content": message}]
            msg_lower = message.lower().strip()

            compare_kw = ["so sanh", "bao cao", "report", "compare", "phan tich"]
            review_kw = ["xem lai", "chi tiet", "detail", "xem"]

            if any(kw in msg_lower for kw in compare_kw):
                if not state.get("ingested"):
                    history += [{"role": "assistant",
                                 "content": "Vui long nhap tai lieu truoc (nhan **+** > **Nhap tai lieu**)."}]
                    return history, state, ""
                try:
                    _, report_text = _run_pipeline(
                        state["doc_id"], state["ver_old"], state["ver_new"],
                    )
                    state["report_text"] = report_text
                    history += [{"role": "assistant", "content": report_text}]
                except Exception as exc:
                    history += [{"role": "assistant",
                                 "content": f"Loi:\n```\n{exc}\n```"}]
                return history, state, ""

            if any(kw in msg_lower for kw in review_kw) and state.get("report_text"):
                history += [{"role": "assistant", "content": state["report_text"]}]
                return history, state, ""

            history += [
                {"role": "assistant",
                 "content": (
                     "Nhan **+** de:\n"
                     "- **Nhap tai lieu** — tai len hop dong\n"
                     "- **Sinh bao cao** — phan tich va xuat bao cao\n\n"
                     "Hoac nhap **so sanh** sau khi da nhap tai lieu."
                 )}
            ]
            return history, state, ""

        msg.submit(
            handle_msg, [msg, chatbot, doc_state], [chatbot, doc_state, msg],
        )
        send_btn.click(
            handle_msg, [msg, chatbot, doc_state], [chatbot, doc_state, msg],
        )

    return app


def main() -> None:
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()
