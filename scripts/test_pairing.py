"""
Script kiểm tra ghép cặp điều khoản (Hybrid Score + Graph CC).
In ra: danh sách chunks, ma trận hybrid score, threshold thực tế, và các cặp ghép.

Sử dụng:
    python scripts/test_pairing.py
    python scripts/test_pairing.py --doc-id Hop_dong_I
    python scripts/test_pairing.py --list-docs
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from legal_rag.db.vector_store import VectorStoreManager
from legal_rag.retrieval.context_pairing import ContextPairer

SEP = "=" * 72
THIN = "-" * 72


def fetch_all_chunks(vector_store, doc_id: str, version_old: str, version_new: str):
    """
    Lấy TẤT CẢ chunks của doc_id thuộc hai phiên bản (không giới hạn bởi k như KNN).
    Dùng collection.get() với metadata filter.
    """
    filter_dict = {
        "$and": [
            {"doc_id": doc_id},
            {"version": {"$in": [version_old, version_new]}},
        ]
    }
    raw = vector_store.vector_db.get(
        where=filter_dict,
        include=["documents", "metadatas"],
    )
    ids = raw.get("ids", []) or []
    docs = raw.get("documents", []) or []
    metas = raw.get("metadatas", []) or []

    results = []
    for idx, cid in enumerate(ids):
        results.append({
            "id": cid,
            "content": docs[idx] if idx < len(docs) else "",
            "metadata": metas[idx] if idx < len(metas) else {},
        })
    # Sắp xếp ổn định theo version, chunk_index để in dễ đọc
    results.sort(key=lambda r: (
        r["metadata"].get("version", ""),
        r["metadata"].get("logical_id", ""),
        r["metadata"].get("chunk_index", 0),
    ))
    return results


def list_available_docs(vector_store):
    raw = vector_store.vector_db.get(include=["metadatas"])
    metas = raw.get("metadatas", []) or []
    seen = defaultdict(set)
    for m in metas:
        did = m.get("doc_id", "?")
        ver = m.get("version", "?")
        seen[did].add(ver)
    return {d: sorted(v) for d, v in seen.items()}


def main():
    parser = argparse.ArgumentParser(description="Test ghép cặp điều khoản")
    parser.add_argument("--doc-id", default=None, help="ID tài liệu (bỏ trống để auto-chọn)")
    parser.add_argument("--old", default="v1")
    parser.add_argument("--new", default="v2")
    parser.add_argument("--list-docs", action="store_true", help="Liệt kê doc_id có trong DB rồi thoát")
    args = parser.parse_args()

    print(SEP)
    print("  TEST GHÉP CẶP ĐIỀU KHOẢN — HYBRID SCORE + GRAPH CC")
    print(SEP)

    print("\n[1] Khởi tạo ChromaDB và mô hình nhúng...")
    vector_store = VectorStoreManager()

    available = list_available_docs(vector_store)
    if args.list_docs or not available:
        print(f"\n{THIN}")
        print("  DOC_ID CÓ TRONG CHROMADB")
        print(THIN)
        if not available:
            print("  (trống — hãy chạy `python scripts/ingest.py`)")
            return
        for d, vers in available.items():
            print(f"  - {d:15s} versions: {vers}")
        if args.list_docs:
            return

    # Auto-chọn doc_id nếu người dùng không truyền
    doc_id = args.doc_id
    if doc_id is None:
        doc_id = next(iter(available))
        print(f"\n[!] --doc-id không được chỉ định → tự chọn: {doc_id}")
    elif doc_id not in available:
        print(f"\n[!] doc_id '{doc_id}' không có trong DB. Các doc_id khả dụng: {list(available)}")
        return

    VER_OLD, VER_NEW = args.old, args.new
    print(f"\n  Document: {doc_id}  |  {VER_OLD} → {VER_NEW}")

    # ── 1. Lấy tất cả chunks theo metadata ────────────────────────────
    results = fetch_all_chunks(vector_store, doc_id, VER_OLD, VER_NEW)
    print(f"[+] Đã lấy {len(results)} chunks từ ChromaDB.")

    if not results:
        print(f"[!] Không tìm thấy chunks cho doc_id='{doc_id}', versions=['{VER_OLD}','{VER_NEW}'].")
        return

    print(f"\n{THIN}")
    print("  DANH SÁCH CHUNKS")
    print(THIN)
    for r in results:
        m = r.get("metadata", {})
        lid = m.get("logical_id", "?")
        ver = m.get("version", "?")
        preview = r.get("content", "")[:80].replace("\n", " ")
        print(f"  [{ver}] {lid:15s} │ {preview}...")

    # ── 2. Gom nội dung & tính Hybrid matrix ──────────────────────────
    print(f"\n{THIN}")
    print("  HYBRID SCORE MATRIX")
    print(THIN)

    v1_data = defaultdict(list)
    v2_data = defaultdict(list)
    for chunk in results:
        meta = chunk.get("metadata", {})
        lid = meta.get("logical_id", "unknown")
        ver = meta.get("version", "")
        content = chunk.get("content", "").strip()
        if not content:
            continue
        if ver == VER_OLD:
            v1_data[lid].append(content)
        elif ver == VER_NEW:
            v2_data[lid].append(content)

    v1_clauses = {lid: "\n".join(parts) for lid, parts in v1_data.items()}
    v2_clauses = {lid: "\n".join(parts) for lid, parts in v2_data.items()}
    v1_ids = list(v1_clauses)
    v2_ids = list(v2_clauses)

    print(f"  Điều khoản bản cũ ({VER_OLD}): {v1_ids}")
    print(f"  Điều khoản bản mới ({VER_NEW}): {v2_ids}")

    pairer = ContextPairer()

    if not v1_ids or not v2_ids:
        print(f"\n[!] Một trong hai phiên bản không có chunks → fallback sang pair_chunks() theo logical_id.")
        paired_data = pairer.pair_chunks(results)
        _print_pairs(paired_data, VER_OLD, VER_NEW)
        return

    embedding_model = vector_store.embeddings
    v1_emb = np.array(embedding_model.embed_documents([v1_clauses[i] for i in v1_ids]))
    v2_emb = np.array(embedding_model.embed_documents([v2_clauses[j] for j in v2_ids]))
    sim_matrix = v1_emb @ v2_emb.T

    bonus_matrix = np.zeros_like(sim_matrix)
    for i, v1_id in enumerate(v1_ids):
        for j, v2_id in enumerate(v2_ids):
            if v1_id == v2_id:
                bonus_matrix[i, j] = 0.15
    hybrid_matrix = sim_matrix + bonus_matrix

    header = "".ljust(18) + "".join(f"{v2_id:>14s}" for v2_id in v2_ids)
    print(f"\n  Cosine Similarity:")
    print(f"  {header}")
    for i, v1_id in enumerate(v1_ids):
        row = f"  {v1_id:16s}" + "".join(f"{sim_matrix[i, j]:14.4f}" for j in range(len(v2_ids)))
        print(row)

    print(f"\n  Hybrid Score (Cosine + Bonus):")
    print(f"  {header}")
    for i, v1_id in enumerate(v1_ids):
        row = f"  {v1_id:16s}"
        for j in range(len(v2_ids)):
            mark = " *" if bonus_matrix[i, j] > 0 else "  "
            row += f"{hybrid_matrix[i, j]:12.4f}{mark}"
        print(row)
    print("  (* = cùng logical_id, được cộng bonus +0.15)")

    # ── 3. Adaptive Threshold ────────────────────────────────────────
    adaptive_thr = pairer._compute_adaptive_threshold(hybrid_matrix, margin=0.10, absolute_min=0.55)
    row_maxes = np.max(hybrid_matrix, axis=1)
    baseline = float(np.mean(row_maxes))
    print(f"\n  Adaptive Threshold:")
    print(f"    Row maxes = {[f'{x:.4f}' for x in row_maxes]}")
    print(f"    Baseline  = {baseline:.4f}")
    print(f"    Threshold = max({baseline - 0.10:.4f}, 0.55) = {adaptive_thr:.4f}")

    # ── 4. Ghép cặp ──────────────────────────────────────────────────
    print(f"\n{THIN}")
    print("  KẾT QUẢ GHÉP CẶP (GRAPH CONNECTED COMPONENTS)")
    print(THIN)

    paired_data = pairer.pair_chunks_semantic(
        retrieved_chunks=results,
        embedding_model=embedding_model,
        version_old=VER_OLD,
        version_new=VER_NEW,
    )
    _print_pairs(paired_data, VER_OLD, VER_NEW)

    # ── 5. Đối chiếu ground truth (nếu có) ───────────────────────────
    gt_path = Path(__file__).parent.parent / "data" / "ground_truth" / f"{doc_id}_ground_truth.json"
    if gt_path.exists():
        print(f"\n{THIN}")
        print("  ĐỐI CHIẾU GROUND TRUTH")
        print(THIN)
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        for change in gt.get("changes", []):
            cid = change.get("clause_id", "")
            ctype = change.get("type", "")
            desc = change.get("description", "")
            found = [k for k in paired_data if cid in k]
            status = "[OK]   " if found else "[MISS] "
            print(f"  {status}{cid:12s} ({ctype:4s}) → key: {found[0] if found else 'N/A'}")
            print(f"           {desc}")

    print(f"\n{SEP}\n  HOÀN THÀNH\n{SEP}")


def _print_pairs(paired_data, ver_old, ver_new):
    for i, (key, versions) in enumerate(paired_data.items(), 1):
        has_old = ver_old in versions
        has_new = ver_new in versions
        if has_old and has_new:
            tag = "CHUNG (ghép cặp)"
        elif has_old:
            tag = "BỊ XOÁ"
        else:
            tag = "MỚI THÊM"
        old_prev = versions.get(ver_old, "")[:120].replace("\n", " ")
        new_prev = versions.get(ver_new, "")[:120].replace("\n", " ")
        print(f"\n  [{i}] Key: {key}")
        print(f"      Loại: {tag}")
        if has_old:
            print(f"      {ver_old}: {old_prev}...")
        if has_new:
            print(f"      {ver_new}: {new_prev}...")


if __name__ == "__main__":
    main()
