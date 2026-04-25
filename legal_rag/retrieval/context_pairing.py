from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple


class ContextPairer:
    """
    Ghép cặp điều khoản giữa hai phiên bản hợp đồng.

    - pair_chunks()          : ghép theo logical_id (số điều khoản) — nhanh, dùng làm fallback
    - pair_chunks_semantic() : ghép theo cosine similarity của embeddings — chính xác hơn khi
                               hợp đồng tái cấu trúc (đổi số điều nhưng giữ nội dung)
    """

    def pair_chunks(self, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """Ghép cặp theo logical_id (số điều khoản)."""
        paired: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            logical_id = meta.get("logical_id", "unknown_clause")
            version    = meta.get("version", "unknown_version")
            content    = chunk.get("content", "").strip()
            if content:
                paired[logical_id][version].append(content)

        final: Dict[str, Dict[str, str]] = {}
        for lid, versions in paired.items():
            final[lid] = {ver: "\n".join(parts) for ver, parts in versions.items()}
        return final

    # ------------------------------------------------------------------
    # Hằng số mặc định
    # ------------------------------------------------------------------
    _BONUS_SAME_ID: float = 0.15          # điểm thưởng khi cùng logical_id
    _ADAPTIVE_MARGIN: float = 0.10        # biên trừ khi tính ngưỡng thích ứng
    _ABSOLUTE_MIN_THRESHOLD: float = 0.55 # điểm sàn tuyệt đối

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_adaptive_threshold(
        hybrid_matrix,                     # np.ndarray [n_v1, n_v2]
        margin: float = 0.10,
        absolute_min: float = 0.55,
    ) -> float:
        """
        Tính ngưỡng thích ứng (Adaptive Threshold) dựa trên phân phối
        của ma trận hybrid similarity.

        Thuật toán:
        1. Với mỗi điều khoản v1, lấy điểm tương đồng cao nhất với v2.
        2. Tính trung bình (mean) của các điểm cực đại đó.
        3. Trừ đi biên dao động (margin) để mở rộng phạm vi chấp nhận.
        4. Không cho phép hạ dưới điểm sàn (absolute_min) để tránh ghép sai.

        Returns:
            Ngưỡng (float) đã được clamp trong [absolute_min, 1.0].
        """
        import numpy as np

        if hybrid_matrix.size == 0:
            return absolute_min

        # Lấy max similarity theo mỗi hàng (mỗi điều khoản v1)
        row_maxes = np.max(hybrid_matrix, axis=1)          # shape [n_v1]
        baseline  = float(np.mean(row_maxes))
        threshold = baseline - margin

        return float(np.clip(threshold, absolute_min, 1.0))

    # ------------------------------------------------------------------
    def pair_chunks_semantic(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        embedding_model: Any,
        version_old: str,
        version_new: str,
        threshold: float | None = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Ghép cặp điều khoản theo ngữ nghĩa kết hợp cấu trúc (Hybrid Score)
        và cho phép ánh xạ N-M thông qua đồ thị liên kết (Connected Components).

        Quy trình:
        1. Gom nội dung theo (version, logical_id).
        2. Embed toàn bộ điều khoản bằng mô hình BGE-M3.
        3. Tính ma trận Cosine Similarity, cộng bonus cho cặp cùng logical_id
           → ma trận Hybrid Score.
        4. Xác định ngưỡng thích ứng (Adaptive Threshold) nếu không truyền
           threshold cố định.
        5. Xây dựng đồ thị hai phía (Bipartite Graph): mỗi cặp (v1_i, v2_j)
           có Hybrid Score >= threshold tạo thành một cạnh.
        6. Tìm các cụm liên kết (Connected Components) → hỗ trợ ghép 1-N,
           N-1, N-M (tách / gộp điều khoản).
        7. Xuất kết quả: gom nội dung theo cụm; điều khoản cô lập → mới
           thêm hoặc bị xoá.

        Args:
            retrieved_chunks: danh sách chunks đã retrieve từ ChromaDB.
            embedding_model:  mô hình embedding (cần có embed_documents()).
            version_old:      tên phiên bản cũ (vd "2020").
            version_new:      tên phiên bản mới (vd "2023").
            threshold:        ngưỡng cố định; nếu None → dùng Adaptive Threshold.

        Returns:
            { key: { version_old: text, version_new: text } }
            Key = logical_id(s) v1 nối bằng " | " nếu nhiều điều trong cụm.
        """
        import numpy as np

        # ── Bước 1: gom nội dung theo (version, logical_id) ────────────
        v1_data: Dict[str, List[str]] = defaultdict(list)
        v2_data: Dict[str, List[str]] = defaultdict(list)
        v1_meta: Dict[str, Dict]      = {}
        v2_meta: Dict[str, Dict]      = {}

        for chunk in retrieved_chunks:
            meta    = chunk.get("metadata", {})
            lid     = meta.get("logical_id", "unknown")
            ver     = meta.get("version", "")
            content = chunk.get("content", "").strip()
            if not content:
                continue
            if ver == version_old:
                v1_data[lid].append(content)
                v1_meta.setdefault(lid, meta)
            elif ver == version_new:
                v2_data[lid].append(content)
                v2_meta.setdefault(lid, meta)

        v1_clauses = {lid: "\n".join(parts) for lid, parts in v1_data.items()}
        v2_clauses = {lid: "\n".join(parts) for lid, parts in v2_data.items()}

        v1_ids = list(v1_clauses)
        v2_ids = list(v2_clauses)

        # Fallback nếu một bên không có chunks
        if not v1_ids or not v2_ids:
            return self.pair_chunks(retrieved_chunks)

        # ── Bước 2: embed tất cả điều khoản ────────────────────────────
        v1_emb = np.array(embedding_model.embed_documents([v1_clauses[i] for i in v1_ids]))
        v2_emb = np.array(embedding_model.embed_documents([v2_clauses[j] for j in v2_ids]))

        # ── Bước 3: Hybrid Score = cosine similarity + bonus cùng ID ───
        sim_matrix = v1_emb @ v2_emb.T  # shape [n_v1, n_v2]

        # Tạo ma trận bonus: +0.15 nếu logical_id giống nhau
        bonus_matrix = np.zeros_like(sim_matrix)
        for i, v1_id in enumerate(v1_ids):
            for j, v2_id in enumerate(v2_ids):
                if v1_id == v2_id:
                    bonus_matrix[i, j] = self._BONUS_SAME_ID

        hybrid_matrix = sim_matrix + bonus_matrix  # Clamp tối đa 1.0 không cần
        # (giá trị > 1.0 vẫn vượt threshold → không ảnh hưởng logic)

        # ── Bước 4: Adaptive Threshold ─────────────────────────────────
        effective_threshold = (
            threshold
            if threshold is not None
            else self._compute_adaptive_threshold(
                hybrid_matrix,
                margin=self._ADAPTIVE_MARGIN,
                absolute_min=self._ABSOLUTE_MIN_THRESHOLD,
            )
        )

        # ── Bước 5: xây đồ thị hai phía (Bipartite Graph) ─────────────
        #   Đỉnh: "v1_{i}" và "v2_{j}"
        #   Cạnh: hybrid_matrix[i,j] >= effective_threshold
        # Dùng Union-Find để tìm Connected Components hiệu quả.

        parent: Dict[str, str] = {}

        def find(x: str) -> str:
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]   # path compression
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        n_v1, n_v2 = len(v1_ids), len(v2_ids)

        # Đăng ký tất cả đỉnh
        for i in range(n_v1):
            parent[f"v1_{i}"] = f"v1_{i}"
        for j in range(n_v2):
            parent[f"v2_{j}"] = f"v2_{j}"

        # Tạo cạnh nếu hybrid score >= threshold
        for i in range(n_v1):
            for j in range(n_v2):
                if hybrid_matrix[i, j] >= effective_threshold:
                    union(f"v1_{i}", f"v2_{j}")

        # ── Bước 6: gom các đỉnh theo component ───────────────────────
        components: Dict[str, List[str]] = defaultdict(list)
        for node in parent:
            components[find(node)].append(node)

        # ── Bước 7: xây dựng paired dict ──────────────────────────────
        paired: Dict[str, Dict[str, str]] = {}

        for _root, members in components.items():
            comp_v1 = sorted([int(m.split("_")[1]) for m in members if m.startswith("v1_")])
            comp_v2 = sorted([int(m.split("_")[1]) for m in members if m.startswith("v2_")])

            if comp_v1 and comp_v2:
                # Cụm có cả v1 lẫn v2 → ghép cặp (có thể 1-N, N-1, N-M)
                key = " | ".join(v1_ids[i] for i in comp_v1)
                old_text = "\n\n".join(v1_clauses[v1_ids[i]] for i in comp_v1)
                new_text = "\n\n".join(v2_clauses[v2_ids[j]] for j in comp_v2)
                paired[key] = {
                    version_old: old_text,
                    version_new: new_text,
                }
            elif comp_v1:
                # Chỉ có v1 → điều khoản bị xoá
                for i in comp_v1:
                    paired[v1_ids[i]] = {version_old: v1_clauses[v1_ids[i]]}
            else:
                # Chỉ có v2 → điều khoản mới thêm
                for j in comp_v2:
                    safe_key = v2_ids[j]
                    while safe_key in paired:
                        safe_key += "_new"
                    paired[safe_key] = {version_new: v2_clauses[v2_ids[j]]}

        return paired
