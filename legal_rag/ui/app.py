# ---------------------------------------------------------------------------
# Giao diện chat bot so sánh hợp đồng pháp lý.
#
# Giao diện đơn giản với:
#   - Chat bot ở giữa
#   - Nút "+" mở menu: Nhập tài liệu / Sinh báo cáo
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os

# Đặt trước mọi import liên quan đến transformers / HuggingFace
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import concurrent.futures
import time

import gradio as gr

from legal_rag.config import RAW_DATA_DIR
from legal_rag.db.vector_store import VectorStoreManager
from legal_rag.generation.citation import CitationMapper
from legal_rag.generation.comparator import DocumentComparator
from legal_rag.generation.report import ReportGenerator
from legal_rag.generation.word_report import generate_word_report
from legal_rag.ingest.document_processor import DocumentProcessor


# ---------------------------------------------------------------------------
# Singletons — load model một lần duy nhất khi khởi động
# ---------------------------------------------------------------------------

_processor: Optional[DocumentProcessor] = None
_store: Optional[VectorStoreManager] = None


def _get_processor() -> DocumentProcessor:
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor


def _get_store() -> VectorStoreManager:
    global _store
    if _store is None:
        _store = VectorStoreManager()
    return _store


def _resolve_path(file_obj: Any) -> str:
    """Xử lý cả string path lẫn Gradio file object."""
    if isinstance(file_obj, str):
        return file_obj
    if hasattr(file_obj, "name"):
        return file_obj.name
    return str(file_obj)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_doc_info(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """Trích xuất doc_id và version từ tên file (VD: Hop_dong_A_v1.docx)."""
    m = re.match(r"(.+?)_(v\d+)\.docx$", filename, re.IGNORECASE)
    return (m.group(1), m.group(2)) if m else (None, None)


def _ingest_files(
    file_old: Any, file_new: Any
) -> Tuple[str, str, str, int]:
    """Xử lý 2 file DOCX: chunk và lưu vào ChromaDB."""
    path_old = _resolve_path(file_old)
    path_new = _resolve_path(file_new)

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

    processor = _get_processor()   # dùng singleton, không load lại model
    store = _get_store()            # dùng singleton, không load lại model
    store.reset_collection()

    all_chunks: List[Dict[str, Any]] = []
    for fpath in [target_old, target_new]:
        chunks = processor.process_file(fpath)
        all_chunks.extend(chunks)

    store.add_documents(all_chunks)
    return doc_id, version_old, version_new, len(all_chunks)


def _format_chat_response(report: Dict[str, Any]) -> str:
    """Tạo phản hồi tự nhiên cho chat (không phải format báo cáo kỹ thuật)."""
    from collections import Counter
    changes = report.get("changes_detail", [])
    summary = report.get("summary", "").strip()
    doc_id = report.get("doc_id", "")
    ver_old = report.get("version_old", "")
    ver_new = report.get("version_new", "")

    counts = Counter(c.get("type", "?") for c in changes)
    count_str = ", ".join(f"**{v} {k}**" for k, v in sorted(counts.items()))

    lines = [
        f"Đã phân tích xong tài liệu **{doc_id}** ({ver_old} → {ver_new}).",
        f"Phát hiện tổng cộng **{len(changes)}** thay đổi: {count_str}.",
        "",
    ]

    if summary:
        lines += ["---", "", summary]
    else:
        lines.append("_(LLM không phản hồi — xem chi tiết trong file Word.)_")

    lines += ["", "---", "File báo cáo Word đầy đủ đã được tạo bên dưới."]
    return "\n".join(lines)


def _run_pipeline(
    doc_id: str, ver_old: str, ver_new: str
) -> Tuple[Dict[str, Any], str]:
    """Chạy pipeline so sánh. Trả về (report_dict, chat_text)."""
    comparator = DocumentComparator()
    comparison = comparator.compare_versions(
        doc_id=doc_id, version_old=ver_old, version_new=ver_new, k=20,
    )
    citation_mapper = CitationMapper(retriever=comparator.retriever)
    enriched = citation_mapper.enrich_changes(comparison)
    report_gen = ReportGenerator()
    report = report_gen.generate_report(enriched)
    report["_enriched"] = enriched
    chat_text = _format_chat_response(report)   # chat: tóm tắt tự nhiên
    return report, chat_text


def _generate_word(report: Dict[str, Any], doc_id: str) -> str:
    """Sinh file Word từ report dict. Trả về đường dẫn file."""
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
    "Xin chào! Tôi là trợ lý so sánh hợp đồng pháp lý.\n\n"
    "Nhấn **+** để bắt đầu:\n"
    "- **Nhập tài liệu** — tải lên 2 phiên bản hợp đồng\n"
    "- **Sinh báo cáo** — phân tích và xuất báo cáo Word"
)

CSS = """
/* ----- Khung tổng & nền ----- */
.gradio-container {
    background: linear-gradient(180deg, #f5f6ff 0%, #fbfbfe 38%, #ffffff 100%) !important;
    max-width: 860px !important;
    margin: 0 auto !important;
    padding: 0 20px 28px 20px !important;
}

/* ----- Header ----- */
.app-header {
    text-align: center;
    padding: 44px 0 22px 0;
}
.app-header .app-icon {
    font-size: 2.6em;
    line-height: 1;
    display: block;
    margin-bottom: 6px;
}
.app-header h1 {
    font-size: 2.2em;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0;
    background: linear-gradient(95deg, #4f46e5 0%, #7c3aed 55%, #6366f1 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-header .app-subtitle {
    margin-top: 8px;
    font-size: 1.0em;
    color: #6b7280;
    font-weight: 400;
}

/* ----- Chatbot ----- */
#main-chat {
    border: 1px solid #e6e7f2 !important;
    border-radius: 20px !important;
    background: #ffffff !important;
    box-shadow: 0 8px 30px rgba(79, 70, 229, 0.07) !important;
    padding: 8px !important;
}
/* Bong bóng tin nhắn (selector nội bộ Gradio — tinh chỉnh nhẹ) */
#main-chat .message,
#main-chat .bubble {
    border-radius: 16px !important;
    line-height: 1.6 !important;
}

/* ----- Thanh nhập dạng pill ----- */
.input-bar {
    margin-top: 14px !important;
    align-items: center !important;
    gap: 8px !important;
}
.input-bar textarea,
.input-bar input[type="text"] {
    border-radius: 24px !important;
    border: 1px solid #e0e1ee !important;
    padding: 13px 18px !important;
    background: #ffffff !important;
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.05) !important;
    transition: border-color .15s ease, box-shadow .15s ease !important;
}
.input-bar textarea:focus,
.input-bar input[type="text"]:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18) !important;
    outline: none !important;
}

/* ----- Nút "+" tròn (FAB) ----- */
.plus-btn {
    min-width: 46px !important;
    max-width: 46px !important;
    height: 46px !important;
    border-radius: 50% !important;
    font-size: 1.45em !important;
    padding: 0 !important;
    border: 1px solid #d7d9ec !important;
    background: #ffffff !important;
    color: #4f46e5 !important;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.08) !important;
    transition: all .15s ease !important;
}
.plus-btn:hover {
    background: #eef0ff !important;
    border-color: #6366f1 !important;
    color: #4338ca !important;
}

/* ----- Nút Gửi (primary) ----- */
.send-btn {
    border-radius: 24px !important;
    min-width: 72px !important;
    height: 46px !important;
    font-weight: 600 !important;
    border: none !important;
    color: #ffffff !important;
    background: linear-gradient(95deg, #4f46e5 0%, #6366f1 100%) !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28) !important;
    transition: filter .15s ease, transform .05s ease !important;
}
.send-btn:hover {
    filter: brightness(1.06) !important;
}
.send-btn:active {
    transform: translateY(1px) !important;
}

/* ----- Menu chức năng ----- */
.action-menu {
    border: 1px solid #e6e7f2;
    border-radius: 16px;
    padding: 6px;
    background: #ffffff;
    box-shadow: 0 10px 30px rgba(79, 70, 229, 0.12);
    max-width: 280px;
    margin-top: 6px;
}
.action-item {
    border: none !important;
    background: none !important;
    text-align: left !important;
    padding: 12px 18px !important;
    font-size: 0.96em !important;
    color: #374151 !important;
    border-radius: 12px !important;
    margin: 2px !important;
    transition: background .12s ease, color .12s ease !important;
}
.action-item:hover {
    background: #eef0ff !important;
    color: #4338ca !important;
}

/* ----- Panel upload ----- */
.upload-panel {
    border: 1px solid #e6e7f2;
    border-radius: 18px;
    padding: 22px;
    background: #fbfbff;
    margin-top: 12px;
    box-shadow: 0 6px 22px rgba(79, 70, 229, 0.07);
}
"""


def create_app() -> gr.Blocks:
    with gr.Blocks(title="Legal RAG") as app:
        # --- State ---
        doc_state = gr.State({
            "doc_id": None, "ver_old": None, "ver_new": None,
            "ingested": False, "report_text": None,
        })
        menu_open = gr.State(False)

        # --- Layout ---
        gr.HTML(
            "<div class='app-header'>"
            "<span class='app-icon'>⚖️</span>"
            "<h1>Legal RAG</h1>"
            "<div class='app-subtitle'>Trợ lý so sánh &amp; phân tích thay đổi hợp đồng pháp lý</div>"
            "</div>"
        )

        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": WELCOME}],
            height=460,
            show_label=False,
            elem_id="main-chat",
        )

        # Thanh nhập liệu
        with gr.Row(elem_classes=["input-bar"]):
            plus_btn = gr.Button("+", elem_classes=["plus-btn"], scale=0)
            msg = gr.Textbox(
                placeholder="Bạn cần hỗ trợ gì?",
                show_label=False,
                scale=4,
                container=False,
            )
            send_btn = gr.Button(
                "Gửi", variant="primary", scale=0, min_width=72,
                elem_classes=["send-btn"],
            )

        # Menu chức năng (ẩn mặc định)
        with gr.Column(visible=False, elem_classes=["action-menu"]) as action_menu:
            ingest_btn = gr.Button("Nhập tài liệu", elem_classes=["action-item"])
            report_btn = gr.Button("Sinh báo cáo", elem_classes=["action-item"])

        # Panel upload (ẩn mặc định)
        with gr.Column(visible=False, elem_classes=["upload-panel"]) as upload_panel:
            gr.Markdown("**Tải lên 2 phiên bản hợp đồng (.docx)**")
            with gr.Row():
                file_old = gr.File(label="Phiên bản cũ (v1)", file_types=[".docx"])
                file_new = gr.File(label="Phiên bản mới (v2)", file_types=[".docx"])
            with gr.Row():
                confirm_btn = gr.Button("Nhập", variant="primary", scale=1)
                cancel_btn = gr.Button("Hủy", variant="secondary", scale=1)

        # File báo cáo (ẩn cho đến khi sinh xong)
        report_file = gr.File(visible=False, label="Tải báo cáo")

        # --- Events ---

        # Đóng/mở menu
        def toggle_menu(is_open):
            return gr.update(visible=not is_open), not is_open

        plus_btn.click(toggle_menu, [menu_open], [action_menu, menu_open])

        # Mở panel upload
        def show_upload():
            return gr.update(visible=False), gr.update(visible=True), False

        ingest_btn.click(show_upload, [], [action_menu, upload_panel, menu_open])

        # Đóng panel upload
        cancel_btn.click(
            lambda: gr.update(visible=False),
            [], [upload_panel],
        )

        # Nhập tài liệu
        def do_ingest(f_old, f_new, history, state):
            if f_old is None or f_new is None:
                yield (
                    history + [{"role": "assistant", "content": "Vui lòng tải lên cả 2 file DOCX."}],
                    state,
                    gr.update(visible=True),
                )
                return

            yield (
                history + [{"role": "assistant", "content": "Đang xử lý tài liệu ."}],
                state,
                gr.update(visible=False),
            )

            # Chạy ingest trong background thread, yield heartbeat để giữ kết nối
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_ingest_files, f_old, f_new)
                dots = 1
                while not future.done():
                    time.sleep(3)
                    dots = dots % 3 + 1
                    # Tạo object mới mỗi lần để Gradio detect thay đổi và gửi SSE
                    yield (
                        history + [{"role": "assistant", "content": "Đang xử lý tài liệu " + "." * dots}],
                        state,
                        gr.update(visible=False),
                    )

            try:
                doc_id, ver_old, ver_new, n = future.result()
                state = {
                    "doc_id": doc_id, "ver_old": ver_old, "ver_new": ver_new,
                    "ingested": True, "report_text": None,
                }
                yield (
                    history + [{"role": "assistant", "content": (
                        f"Đã nhập thành công **{n}** đoạn văn bản "
                        f"từ `{doc_id}` ({ver_old}, {ver_new}).\n\n"
                        f"Nhấn **+** > **Sinh báo cáo** để phân tích."
                    )}],
                    state,
                    gr.update(visible=False),
                )
            except Exception as exc:
                yield (
                    history + [{"role": "assistant", "content": f"Lỗi khi nhập tài liệu:\n```\n{exc}\n```"}],
                    state,
                    gr.update(visible=False),
                )

        confirm_btn.click(
            do_ingest,
            [file_old, file_new, chatbot, doc_state],
            [chatbot, doc_state, upload_panel],
        )

        # Sinh báo cáo
        def do_report(history, state):
            if not state.get("ingested"):
                yield (
                    history + [{"role": "assistant", "content": "Vui lòng nhập tài liệu trước khi sinh báo cáo."}],
                    state,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    False,
                )
                return

            doc_id = state["doc_id"]
            ver_old = state["ver_old"]
            ver_new = state["ver_new"]

            yield (
                history + [{"role": "assistant", "content": "Đang phân tích tài liệu ."}],
                state,
                gr.update(visible=False),
                gr.update(visible=False),
                False,
            )

            # Chạy pipeline trong background thread, yield heartbeat để giữ kết nối
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_pipeline, doc_id, ver_old, ver_new)
                dots = 1
                while not future.done():
                    time.sleep(3)
                    dots = dots % 3 + 1
                    yield (
                        history + [{"role": "assistant", "content": "Đang phân tích tài liệu " + "." * dots}],
                        state,
                        gr.update(visible=False),
                        gr.update(visible=False),
                        False,
                    )

            try:
                report, report_text = future.result()
                state["report_text"] = report_text
                word_path = _generate_word(report, doc_id)
                yield (
                    history + [{"role": "assistant", "content": report_text}],
                    state,
                    gr.update(visible=False),
                    gr.update(value=word_path, visible=True),
                    False,
                )
            except Exception as exc:
                yield (
                    history + [{"role": "assistant", "content": f"Lỗi khi sinh báo cáo:\n```\n{exc}\n```"}],
                    state,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    False,
                )

        report_btn.click(
            do_report,
            [chatbot, doc_state],
            [chatbot, doc_state, action_menu, report_file, menu_open],
        )

        # Xử lý tin nhắn text
        def handle_msg(message, history, state):
            if not message or not message.strip():
                return history, state, ""

            history = history + [{"role": "user", "content": message}]
            msg_lower = message.lower().strip()

            # Giữ từ khóa không dấu + bổ sung biến thể có dấu để khớp cả hai kiểu gõ
            compare_kw = [
                "so sanh", "so sánh", "bao cao", "báo cáo",
                "report", "compare", "phan tich", "phân tích",
            ]
            review_kw = ["xem lai", "xem lại", "chi tiet", "chi tiết", "detail", "xem"]

            if any(kw in msg_lower for kw in compare_kw):
                if not state.get("ingested"):
                    history += [{"role": "assistant",
                                 "content": "Vui lòng nhập tài liệu trước (nhấn **+** > **Nhập tài liệu**)."}]
                    return history, state, ""
                try:
                    _, report_text = _run_pipeline(
                        state["doc_id"], state["ver_old"], state["ver_new"],
                    )
                    state["report_text"] = report_text
                    history += [{"role": "assistant", "content": report_text}]
                except Exception as exc:
                    history += [{"role": "assistant",
                                 "content": f"Lỗi:\n```\n{exc}\n```"}]
                return history, state, ""

            if any(kw in msg_lower for kw in review_kw) and state.get("report_text"):
                history += [{"role": "assistant", "content": state["report_text"]}]
                return history, state, ""

            history += [
                {"role": "assistant",
                 "content": (
                     "Nhấn **+** để:\n"
                     "- **Nhập tài liệu** — tải lên hợp đồng\n"
                     "- **Sinh báo cáo** — phân tích và xuất báo cáo\n\n"
                     "Hoặc nhập **so sánh** sau khi đã nhập tài liệu."
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
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.indigo,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    ).set(
        body_background_fill="transparent",
        block_radius="16px",
    )
    app.launch(css=CSS, theme=theme)


if __name__ == "__main__":
    main()
