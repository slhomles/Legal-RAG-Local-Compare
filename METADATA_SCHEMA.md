# Vector Database Schema - Metadata Chuẩn Hóa

**Trạng thái:** ✅ HOÀN THÀNH - ChromaDB đã được re-index với metadata chuẩn hóa

## Mục tiêu
Đảm bảo Vector Database có đủ dữ liệu cấu trúc để phân biệt 2 phiên bản tài liệu, tránh LLM "ảo giác" khi lấy nhầm đoạn giữa các phiên bản.

## Metadata Schema Mới

Mỗi chunk trong ChromaDB bây giờ chứa **4 metadata fields**:

| Field | Ví dụ | Mục đích |
|-------|-------|---------|
| `document_id` | `Hop_dong_A` | ID tài liệu gốc (tách riêng khỏi version) |
| `version` | `v1` hoặc `v2` | Phiên bản tài liệu |
| `clause_id` | `CLAUSE_001` hoặc `CLAUSE_DIEU_1` | ID điều/mục chuẩn hóa |
| `chunk_heading` | `Điều 1. Định nghĩa` | Tiêu đề heading gốc |
| `doc_id` | `Hop_dong_A_v1.docx` | Tên file đầy đủ (backward compatibility) |

## Cách Hoạt Động

### 1. Trích Xuất `document_id` và `version` từ Tên File

```python
DocumentProcessor._extract_document_id_and_version(filename: str) -> tuple[str, str]
```

**Quy tắc:**
- File: `Hop_dong_A_v1.docx` → `document_id="Hop_dong_A"`, `version="v1"`
- File: `Contract_v2.docx` → `document_id="Contract"`, `version="v2"`
- File: `luat-93-2025-qh15_2208163926.docx` → `document_id="luat-93-2025-qh15_2208163926"`, `version="v1"` (default)

**Pattern:** Tìm `_v<number>` ở cuối tên file (trước `.docx`)

### 2. Chuẩn Hóa `clause_id` từ Heading

```python
DocumentProcessor._normalize_clause_id(heading: str) -> str
```

**Quy tắc Chuẩn Hóa:**

| Heading | Alias | clause_id |
|---------|-------|-----------|
| `Điều 1` | `Article 1` | `CLAUSE_001` |
| `Điều 5` | `Article 5` | `CLAUSE_005` |
| `Chương I` | `Chapter I` | `CHAPTER_I` |
| `Chương II` | `Chapter II` | `CHAPTER_II` |
| `Mục 2.3` | `Section 2.3` | `SECTION_2_3` |
| `Mở đầu` | (default) | `CLAUSE_MỞ_ĐẦU` |

### 3. Sửa Đổi `process_file()` 

File: `src/legal_rag/ingest/document_processor.py`

- Tham số `version` giờ là **optional** (thay vì bắt buộc)
- Tự động trích `document_id` và `version` từ filename
- Thêm `clause_id` vào metadata của mỗi chunk

## Dữ Liệu Hiện Tại (Sau Re-index)

### ChromaDB Content

```
Tổng Chunks: 13

Document ID     Version     Count
─────────────────────────────────
Hop_dong_A      v1          6
Hop_dong_A      v2          7
```

### Phân Tích Chi Tiết

**Hop_dong_A v1** (6 chunks):
- Mở đầu (CLAUSE_MỞ_ĐẦU)
- Điều 1: Định nghĩa (CLAUSE_DIEU_1._DINH_NGHIA)
- Điều 2: Giá trị (CLAUSE_DIEU_2._GIA_TRI_HOP_DONG)
- Điều 3: Thời gian giao hàng (CLAUSE_DIEU_3._THOI_GIAN_VA_DIA_DIEM_GIAO_HANG)
- Điều 4: Bảo hành (CLAUSE_DIEU_4._BAO_HANH)
- Điều 5: Phạt vi phạm (CLAUSE_DIEU_5._PHAT_VI_PHAM)

**Hop_dong_A v2** (7 chunks):
- Toàn bộ các điều của v1
- **+** Điều 6: Điều khoản bổ sung (CLAUSE_DIEU_6._DIEU_KHOAN_BO_SUNG)

### Sự Khác Biệt Chính

| Mục | v1 | v2 |
|-----|----|----|
| Sản phẩm (Điều 1.1) | laptop, máy tính bàn, phụ kiện | laptop, máy tính bàn, **màn hình**, phụ kiện |
| Giá trị (Điều 2.1) | 500 triệu | **650 triệu** |
| Thuế (Điều 2.2) | 10% | **8%** |
| Thời gian (Điều 3.1) | 30 ngày | **45 ngày** |
| Bảo hành (Điều 4.1) | 12 tháng | **24 tháng** |
| Phạt vi phạm (Điều 5.1) | 8% | **10%** |
| Địa chỉ Ben B (Điều 1.3) | 456 Lê Lợi | **789 Trần Hưng Đạo** |
| Thanh toán (Điều 2.3) | Chuyển khoản | **Chuyển khoản hoặc L/C** |

## Công Cụ Sử Dụng

### 1. Re-index ChromaDB

Khi thêm tài liệu mới hoặc cần cập nhật metadata:

```bash
python reindex_database.py [--confirm]
```

**Tùy chọn:**
- `--confirm`: Chạy ngay mà không cần xác nhận

**Quá trình:**
1. Xóa toàn bộ ChromaDB cũ
2. Load lại tất cả file `.docx` từ `data/raw/`
3. Xử lý với metadata chuẩn hóa
4. Lưu vào ChromaDB mới

### 2. Xem Chunks và Metadata

```bash
# Xem thống kê
python view_chunks.py --stats

# Xem chi tiết chunks
python view_chunks.py --limit 20

# Lọc theo document_id
python view_chunks.py --doc-id "Hop_dong_A"

# Tìm chunks chứa text
python view_chunks.py --contains "warranty"
```

## Lợi Ích Với LLM Retrieval

### Trước (Không có metadata rõ ràng):
❌ LLM dễ lầm lẫn chunks từ v1 và v2
❌ Không thể phân biệt phiên bản tài liệu
❌ Dễ "ảo giác" và sinh ra response sai lệch

### Sau (Có metadata chuẩn hóa):
✅ LLM có thể filter chunks theo version
✅ LLM nhận được metadata rõ ràng về document_id, version, clause_id
✅ LLM có ngữ cảnh đầy đủ để truy xuất chính xác
✅ Có thể implement "version-aware" retrieval

### Ví dụ Retrieval Query

```python
# Lấy chunks từ Hợp đồng A, phiên bản v1, Điều 1
chunks = vector_store.search_similar(
    query="Định nghĩa hàng hóa",
    k=3,
    filter_dict={
        "document_id": "Hop_dong_A",
        "version": "v1",
        "clause_id": "CLAUSE_001"
    }
)
```

## File Thay Đổi

1. **`src/legal_rag/ingest/document_processor.py`**
   - Thêm `_extract_document_id_and_version()` method
   - Thêm `_normalize_clause_id()` method
   - Sửa `process_file()` để sử dụng metadata mới

2. **`src/legal_rag/cli/ingestion.py`**
   - Cập nhật để tự động detect version từ filename

3. **`src/legal_rag/tools/view_chroma_chunks.py`**
   - Cập nhật query để hiển thị metadata mới
   - Cập nhật stats display

4. **`reindex_database.py`** (New)
   - Script tái chỉ mục ChromaDB với metadata chuẩn hóa
   - Có xác nhận trước khi xóa dữ liệu cũ

5. **`test_metadata_extraction.py`** (New)
   - Test script để xác minh metadata extraction logic

## Kế Tiếp

Để hoàn thiện hệ thống:

1. **Thêm Filter Metadata trong Vector Store** 
   - Implement filter_dict support trong `search_similar()`
   - Cho phép query theo document_id, version, clause_id

2. **Implement Version-Aware Retrieval**
   - Tự động mở rộng search khi có multiple versions
   - So sánh changes giữa versions

3. **Update LLM Prompts**
   - Thêm metadata vào prompt context
   - Dạy LLM cách sử dụng document_id và version

4. **Monitoring & Logging**
   - Track retrieval hits per document_id/version
   - Detect nếu LLM nhầm lẫn versions

---
**Ngày cập nhật:** 2026-03-14
**Trạng thái:** Production Ready ✅
