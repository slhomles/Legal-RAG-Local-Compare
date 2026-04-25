"""
Script in ra toàn bộ thông tin gửi cho LLM (system prompt + user prompt cho từng điều khoản).
Dùng để kiểm tra/debug nội dung trước khi LLM xử lý.

Sử dụng:
    python scripts/debug_llm_input.py
    python scripts/debug_llm_input.py --doc-id Hop_dong_A --old v1 --new v2
    python scripts/debug_llm_input.py --out output/llm_input_debug.txt
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from legal_rag.generation.prompts import COMPARISON_USER_TEMPLATE, SYSTEM_PROMPT
from legal_rag.retrieval.context_pairing import ContextPairer
from legal_rag.retrieval.retriever import LegalRetriever


SEP_THICK = "=" * 72
SEP_THIN  = "-" * 72


def build_llm_inputs(
    doc_id: str,
    version_old: str,
    version_new: str,
    k: int = 20,
) -> list[dict]:
    """
    Truy xuất chunks, ghép cặp theo ngữ nghĩa, rồi tạo danh sách prompt cho từng điều khoản.
    Không gọi LLM — chỉ trả về dữ liệu đầu vào.
    """
    retriever = LegalRetriever()
    pairer    = ContextPairer()

    filter_dict = {
        "$and": [
            {"doc_id": doc_id},
            {"version": {"$in": [version_old, version_new]}},
        ]
    }
    results = retriever.retrieve(
        query=f"hop dong {doc_id}",
        k=k,
        filter_dict=filter_dict,
    )

    embedding_model = retriever.vector_store.embeddings
    paired_data = pairer.pair_chunks_semantic(
        retrieved_chunks=results,
        embedding_model=embedding_model,
        version_old=version_old,
        version_new=version_new,
    )

    # Metadata lookup để lấy heading
    meta_lookup: dict = {}
    for chunk in results:
        lid = chunk.get("metadata", {}).get("logical_id", "")
        if lid and lid not in meta_lookup:
            meta_lookup[lid] = chunk["metadata"]

    inputs = []
    for clause_id, versions in paired_data.items():
        has_old = version_old in versions
        has_new = version_new in versions

        meta     = meta_lookup.get(clause_id, {})
        heading  = meta.get("chunk_heading", clause_id)
        text_old = versions.get(version_old, "")
        text_new = versions.get(version_new, "")

        if has_old and has_new:
            clause_type = "CHUNG"
            user_prompt = COMPARISON_USER_TEMPLATE.format(
                clause_heading=heading,
                version_old=version_old,
                version_new=version_new,
                text_old=text_old,
                text_new=text_new,
            )
        elif not has_old and has_new:
            clause_type = "MỚI THÊM"
            user_prompt = f"(Điều khoản mới, không gửi cho LLM)\n\nNội dung:\n{text_new}"
        else:
            clause_type = "BỊ XOÁ"
            user_prompt = f"(Điều khoản bị xoá, không gửi cho LLM)\n\nNội dung cũ:\n{text_old}"

        inputs.append({
            "clause_id":   clause_id,
            "heading":     heading,
            "clause_type": clause_type,
            "system":      SYSTEM_PROMPT,
            "user":        user_prompt,
            "text_old":    text_old,
            "text_new":    text_new,
        })

    return inputs


def render_text(inputs: list[dict], doc_id: str, ver_old: str, ver_new: str) -> str:
    lines = [
        SEP_THICK,
        f"  DEBUG: DỮ LIỆU GỬI CHO LLM",
        f"  Tài liệu : {doc_id}   |   So sánh: {ver_old} → {ver_new}",
        f"  Tổng điều khoản: {len(inputs)}",
        SEP_THICK,
        "",
        "  [SYSTEM PROMPT — áp dụng cho MỌI lần gọi LLM]",
        SEP_THIN,
        SYSTEM_PROMPT,
        "",
    ]

    for i, item in enumerate(inputs, 1):
        lines += [
            SEP_THICK,
            f"  [{i}/{len(inputs)}]  {item['clause_type']}  —  {item['heading']}  ({item['clause_id']})",
            SEP_THICK,
        ]

        if item["clause_type"] == "CHUNG":
            lines += [
                "",
                "  [USER PROMPT]",
                SEP_THIN,
                item["user"],
                "",
                "  [NỘI DUNG CŨ — thô]",
                SEP_THIN,
                item["text_old"] or "(trống)",
                "",
                "  [NỘI DUNG MỚI — thô]",
                SEP_THIN,
                item["text_new"] or "(trống)",
            ]
        else:
            lines += [
                "",
                f"  → {item['user']}",
            ]

        lines.append("")

    lines += [SEP_THICK, "  KẾT THÚC", SEP_THICK]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="In dữ liệu gửi cho LLM ra file/terminal")
    parser.add_argument("--doc-id", default="Hop_dong_A")
    parser.add_argument("--old",    default="v1")
    parser.add_argument("--new",    default="v2")
    parser.add_argument("--k",      type=int, default=20)
    parser.add_argument("--out",    default=None, help="Luu vao file (mac dinh: in ra terminal)")
    args = parser.parse_args()

    print(f"[*] Truy xuat chunks cho {args.doc_id} ({args.old} / {args.new})...")
    inputs = build_llm_inputs(args.doc_id, args.old, args.new, k=args.k)
    print(f"[+] Tim thay {len(inputs)} dieu khoan.")

    output = render_text(inputs, args.doc_id, args.old, args.new)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"[+] Da luu vao: {args.out}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    main()
