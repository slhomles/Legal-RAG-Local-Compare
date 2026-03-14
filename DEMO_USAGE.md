# DEMO_RETRIEVAL - Hướng Dẫn Sử Dụng

## Tổng Quan

Script `demo_retrieval.py` cho phép truy xuất và so sánh nội dung bản gốc (v1) vs bản sửa đổi (v2) của một điều khoản bất kỳ.

---

## Cách Chạy

### Cách 1: Chạy và nhập clause_id tương tác
```bash
python demo_retrieval.py
```

Màn hình sẽ hiến thị:
```
====... LEGAL RAG - DEMO TRY XUAT DIEU KHOAN ====...
Cac dieu khoan co san: Dieu 1, Dieu 2, Dieu 3, Dieu 4, Dieu 5, Dieu 6, Mo_dau

Nhap clause_id (vi du 'Dieu 5'): 
```

Sau đó gõ: `Dieu 5` và Enter

---

### Cách 2: Chạy với argument (nhanh hơn)
```bash
python demo_retrieval.py "Dieu 1"
python demo_retrieval.py "Dieu 3"
python demo_retrieval.py "Dieu 5"
```

---

## Output Format

Script sẽ in ra hai cột so sánh:

```
====================================================================================================
DIEU KHOAN: Dieu 5
====================================================================================================
BAN GOC (v1)                             | BAN SUA DOI (v2)
---------------------------------------- | ----------------------------------------
Dieu 5. Phat vi pham                     | Dieu 5. Phat vi pham
5.1. Ben nao vi pham hop dong phai... | 5.1. Ben nao vi pham hop dong phai...
5.2. Truong hop bat kha khang, hai... | 5.2. Truong hop bat kha khang, hai...
====================================================================================================

[INFO] Chi tiet:
  Ban goc (v1):
    - Document: Hop_dong_A_v1.docx
    - Heading: Dieu 5. Phat vi pham
    - Chunks: 3
  Ban sua doi (v2):
    - Document: Hop_dong_A_v2.docx
    - Heading: Dieu 5. Phat vi pham
    - Chunks: 3

[SUCCESS] Hoan tat!
```

---

## Ghi Chú

1. **Các điều khoản có sẵn**: Dieu 1, 2, 3, 4, 5, 6, Mo_dau
2. **Nếu nhập sai**: Script sẽ báo lỗi "Khong tim thay"
3. **Nếu thiếu dữ liệu**: Script sẽ báo "Khong co du lieu day du"

---

## Ví Dụ Thực Tế

```bash
# Xem điều 1
python demo_retrieval.py "Dieu 1"

# Xem điều 3
python demo_retrieval.py "Dieu 3"

# Xem phần mở đầu
python demo_retrieval.py "Mo_dau"
```

---

## Điểm Khác Biệt Giữa Phiên Bản

Ví dụ **Dieu 3**:
- v1: "Thoi gian giao hang: **Trong vong 30 ngay**..."
- v2: "Thoi gian giao hang: **Trong vong 45 ngay**..." (thay đổi: 30 → 45)

---

## Troubleshooting

| Vấn Đề | Giải Pháp |
|--------|----------|
| "Khong tim thay" | Kiểm tra tên clause_id (case-sensitive) |
| "Khong co du lieu day du" | Dữ liệu chỉ có 1 phiên bản, có thể kiểm tra "Dieu 6" |
| Encoding lỗi | Đảm bảo Python 3.8+ |

---

**Tác giả**: Legal RAG System  
**Ngày tạo**: 2026-03-14  
**Phiên bản**: 1.0
