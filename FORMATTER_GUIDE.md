# Output Formatter - Hướng Dẫn Sử Dụng

## Tổng Quan

Script xử lý đầu ra của quá trình Retrieval và chuyển đổi thành định dạng JSON có cấu trúc rõ ràng để hỗ trợ so sánh tài liệu.

**Thay vì danh sách lộn xộn:**
```
Chunk 1: Dieu 3...
Chunk 2: Dieu 3...  
Chunk 3: Dieu 3...
...
```

**Chúng ta có cấu trúc có tổ chức:**
```json
{
  "Điều 3": {
    "Bản_gốc": "nội dung v1...",
    "Bản_sửa_đổi": "nội dung v2..."
  }
}
```

---

## Cấu Trúc Thư Mục

```
src/legal_rag/retrieval/
├── output_formatter.py          # ✅ Class chính để xử lý output
└── retriever.py                 # Retrieve dữ liệu từ ChromaDB

(root)/
├── demo_retrieval_formatter.py  # ✅ Demo phơi bày cách sử dụng
├── retrieve_and_format.py       # ✅ CLI script để trích xuất
├── test_formatter.py            # ✅ Unit test cho formatter
└── dieu_compared.json           # ✅ Output mẫu
```

---

## 1. Định Dạng Output

### A. Định Dạng Ghép Cặp (Paired Format) - ĐỀ CẢ

**Cách sử dụng:**
```python
formatter = RetrievalOutputFormatter()
formatter.add_from_comparison_dict(comparison_data)
paired = formatter.get_paired_format()  # Dict
paired_json = formatter.to_json(detailed=False)  # JSON string
```

**Cấu trúc:**
```json
{
  "Điều 1": {
    "Bản_gốc": "nội dung phiên bản gốc v1...",
    "Bản_sửa_đổi": "nội dung phiên bản sửa_đổi v2..."
  },
  "Điều 3": {
    "Bản_gốc": "...",
    "Bản_sửa_đổi": "..."
  }
}
```

**Ưu điểm:**
- ✅ Đơn giản, dễ đọc
- ✅ Tập trung vào nội dung so sánh
- ✅ Phù hợp cho UI/Frontend
- ✅ Kích thước file nhỏ

---

### B. Định Dạng Chi Tiết (Detailed Format)

**Cách sử dụng:**
```python
detailed = formatter.get_detailed_format()  # Dict
detailed_json = formatter.to_json(detailed=True)  # JSON string
```

**Cấu trúc:**
```json
{
  "Điều 1": {
    "v1": {
      "document_id": "Hop_dong_A_v1.docx",
      "heading": "Dieu 1. Dinh nghia",
      "content": "nội dung...",
      "chunk_count": 3,
      "version": "v1"
    },
    "v2": {
      "document_id": "Hop_dong_A_v2.docx",
      "heading": "Dieu 1. Dinh nghia",
      "content": "nội dung...",
      "chunk_count": 3,
      "version": "v2"
    }
  }
}
```

**Ưu điểm:**
- ✅ Đầy đủ metadata
- ✅ Có thông tin nguồn (document_id, heading)
- ✅ Biết được số chunks được gộp
- ✅ Phù hợp cho audit trail / traceability

---

## 2. Các Phương Thức Của RetrievalOutputFormatter

### A. `add_clause_result()` - Thêm dữ liệu thủ công
```python
formatter.add_clause_result(
    clause_id="Dieu 3",
    version="v1",
    document_id="Hop_dong_A_v1.docx",
    heading="Dieu 3. Thoi gian va dia diem giao hang",
    content="Dieu 3. Thoi gian...",
    chunk_count=3
)
```

### B. `add_from_comparison_dict()` - Thêm từ kết quả retriever
```python
comparison = retriever.search_clause_with_both_versions(
    clause_id="Dieu 3",
    versions=["v1", "v2"]
)
formatter.add_from_comparison_dict(comparison)
```

### C. `get_paired_format()` - Lấy định dạng ghép cặp
```python
paired = formatter.get_paired_format()
# {"Dieu 1": {"Bản_gốc": "...", "Bản_sửa_đổi": "..."}, ...}
```

### D. `get_detailed_format()` - Lấy định dạng chi tiết
```python
detailed = formatter.get_detailed_format()
# {"Dieu 1": {"v1": {...}, "v2": {...}}, ...}
```

### E. `to_json()` - Xuất JSON string
```python
json_str = formatter.to_json(detailed=False)  # Ghép cặp
json_str = formatter.to_json(detailed=True)   # Chi tiết
```

### F. `save_json()` - Lưu file JSON
```python
formatter.save_json("output.json", detailed=False)
formatter.save_json("output_detailed.json", detailed=True)
```

### G. `display()` - In kết quả ra màn hình
```python
formatter.display(detailed=False)  # In ghép cặp
formatter.display(detailed=True)   # In chi tiết
```

### H. `get_comparison_summary()` - Lấy thống kê
```python
summary = formatter.get_comparison_summary()
# {
#     "total_clauses": 6,
#     "clauses_with_both_versions": 5,
#     "clauses_missing_v1": ["Dieu 6"],
#     "clauses_missing_v2": [],
#     "comparison_ready": True
# }
```

---

## 3. Ví Dụ Sử Dụng

### Ví Dụ 1: Trích xuất 1 điều khoản và xuất JSON
```python
from legal_rag.retrieval.retriever import LegalRetriever
from legal_rag.retrieval.output_formatter import RetrievalOutputFormatter

# Khởi tạo
retriever = LegalRetriever()
formatter = RetrievalOutputFormatter()

# Trích xuất 1 điều khoản
comparison = retriever.search_clause_with_both_versions(
    clause_id="Dieu 3",
    versions=["v1", "v2"]
)
formatter.add_from_comparison_dict(comparison)

# Xuất JSON
formatter.save_json("dieu3.json", detailed=False)
formatter.display(detailed=False)
```

### Ví Dụ 2: Trích xuất nhiều điều khoản
```python
clauses = ["Dieu 1", "Dieu 2", "Dieu 3", "Dieu 4", "Dieu 5"]

for clause_id in clauses:
    comparison = retriever.search_clause_with_both_versions(clause_id)
    formatter.add_from_comparison_dict(comparison)

# Xuất toàn bộ
formatter.save_json("all_clauses.json")
formatter.display()
```

### Ví Dụ 3: Lấy dữ liệu dưới dạng Python dict (không file)
```python
comparison = retriever.search_clause_with_both_versions("Dieu 3")
formatter.add_from_comparison_dict(comparison)

# Lấy dict
paired_data = formatter.to_dict(detailed=False)
detailed_data = formatter.to_dict(detailed=True)

# Xử lý trong code
print(paired_data["Dieu 3"]["Bản_gốc"])
print(paired_data["Dieu 3"]["Bản_sửa_đổi"])
```

---

## 4. Scripts Có Sẵn

### A. `demo_retrieval_formatter.py` - Demo Đầy Đủ
```bash
python demo_retrieval_formatter.py
```

Hoạt động:
1. Trích xuất 3 điều khoản
2. In định dạng ghép cặp
3. In thống kê
4. Lưu 2 file JSON

Output:
- `dieu_compared.json` - Ghép cặp (200 bytes)
- `dieu_compared_detailed.json` - Chi tiết (500 bytes)

---

### B. `retrieve_and_format.py` - CLI Script
```bash
# Trích xuất một điều khoản
python retrieve_and_format.py --clause-id "Dieu 3"

# Trích xuất một điều khoản, định dạng chi tiết
python retrieve_and_format.py --clause-id "Dieu 3" --detailed

# Trích xuất tất cả điều khoản
python retrieve_and_format.py

# Không lưu file, chỉ in
python retrieve_and_format.py --no-save

# Chỉ định file output
python retrieve_and_format.py --output-file "my_comparison.json"
```

**Tùy chọn:**
```
--clause-id CLAUSE_ID    Trích xuất một điều khoản cụ thể
--output-file FILE       Đường dẫn file JSON output
--detailed               Lưu với metadata đầy đủ
--paired                 In định dạng ghép cặp (mặc định)
--no-save                Không lưu file JSON
```

---

### C. `test_formatter.py` - Unit Test
```bash
python test_formatter.py
```

Kiểm thử:
- Thêm mock data
- Lấy định dạng ghép cặp
- Lấy định dạng chi tiết
- Kiểm thống kê

---

## 5. Quy Trình Công Việc (Workflow)

```
RETRIEVAL STEP          OUTPUT                      FORMATTER STEP
┌─────────────────┐     ┌──────────────────────────┐  ┌──────────────────┐
│ LegalRetriever  │────▶│ comparison_dict          │──▶│ RetrievalOutput  │
└─────────────────┘     │ {                        │  │ Formatter        │
                        │   "clause_id": "Dieu 3", │  └──────────────────┘
                        │   "comparison_ready": T, │      │
                        │   "versions": {...}     │      │
                        │ }                        │      ▼
                        └──────────────────────────┘  ┌──────────────────┐
                                                     │ Formatted Output │
                                                     │ ┌──────────────┐  │
                                                     │ │ Paired JSON: │  │
                                                     │ │ {            │  │
                                                     │ │  "Dieu 3": { │  │
                                                     │ │   "Bản_gốc"..│  │
                                                     │ │  }           │  │
                                                     │ │ }            │  │
                                                     │ └──────────────┘  │
                                                     └──────────────────┘
```

---

## 6. JSON Output Examples

### Paired Format (dieu_compared.json)
```json
{
  "Dieu 1": {
    "Bản_gốc": "Dieu 1. Dinh nghia\n1.1. \"Hang hoa\" la san pham dien tu bao gom laptop, may tinh ban va phu kien kem theo.",
    "Bản_sửa_đổi": "Dieu 1. Dinh nghia\n1.1. \"Hang hoa\" la san pham dien tu bao gom laptop, may tinh ban, man hinh va phu kien kem theo."
  }
}
```

**Khác biệt giữa v1 vs v2:**
- v1: "laptop, may tinh ban" (2 items)
- v2: "laptop, may tinh ban, man hinh" (3 items - thêm màn hình)

---

## 7. Trường Hợp Sử Dụng

| Trường Hợp | Phương Pháp | Output Format |
|-----------|-----------|───────────---|
| Hiển thị UI so sánh | RetrievalOutputFormatter | Paired JSON |
| Audit trail / Traceability | RetrievalOutputFormatter | Detailed JSON |
| Xử lý trong code | to_dict() | Python dict |
| Lưu cho sau này | save_json() | JSON file |
| Kiểm tra thủ công | display() | Console output |

---

## 8. Tích Hợp Với Các Thành Phần Khác

### Tích Hợp Với UI/Frontend
```python
# Backend
formatter = RetrievalOutputFormatter()
# ... thêm dữ liệu ...
json_output = formatter.to_json(detailed=False)

# API Response
{
    "status": "success",
    "data": json.loads(json_output)
}
```

### Tích Hợp Với Evaluation/Metrics
```python
detailed_data = formatter.get_detailed_format()

for clause_id, versions in detailed_data.items():
    v1_content = versions.get("v1", {}).get("content", "")
    v2_content = versions.get("v2", {}).get("content", "")
    
    # So sánh
    similarity = calculate_similarity(v1_content, v2_content)
    print(f"{clause_id}: {similarity:.2%}")
```

### Tích Hợp Với Comparator/Generation
```python
from legal_rag.generation.comparator import Comparator

formatter = RetrievalOutputFormatter()
# ... thêm dữ liệu ...
paired = formatter.to_dict(detailed=False)

comparator = Comparator()
for clause_id, versions in paired.items():
    analysis = comparator.compare(
        original=versions["Bản_gốc"],
        modified=versions["Bản_sửa_đổi"]
    )
    print(f"{clause_id}: {analysis}")
```

---

## 9. Lưu Ý & Best Practices

### ✅ Best Practices
1. Sử dụng `to_dict()` cho xử lý trong code
2. Sử dụng `save_json()` cho lưu file
3. Luôn kiểm tra `comparison_ready` trước khi sử dụng
4. Sử dụng paired format cho UI/display
5. Sử dụng detailed format cho audit trail

### ⚠️ Lưu Ý
- Formatter không gọi retriever - phải pass dữ liệu từ retriever
- Dữ liệu `None` sẽ bị bỏ qua khi thêm
- JSON sử dụng `ensure_ascii=False` để hỗ trợ tiếng Việt
- Filename có thể chứa khoảng trắng phải encode

### 🔧 Troubleshooting
**Vấn đề:** Để trống dict
- **Nguyên nhân:** Không thêm dữ liệu
- **Giải pháp:** Gọi `add_from_comparison_dict()` hoặc `add_clause_result()`

**Vấn đề:** Thiếu versions
- **Nguyên nhân:** Chỉ có v1 hoặc v2
- **Giải pháp:** Kiểm tra `comparison_ready` trước sử dụng

---

## 10. Lệnh Nhanh

```bash
# Demo đầy đủ
python demo_retrieval_formatter.py

# CLI - trích xuất tất cả
python retrieve_and_format.py

# CLI - một điều khoản
python retrieve_and_format.py --clause-id "Dieu 3"

# Kiểm tra file output
cat dieu_compared.json | jq '.'

# Test
python test_formatter.py
```

---

**Tác giả:** Legal RAG System  
**Ngày cập nhật:** 2026-03-14  
**Phiên bản:** 1.0
