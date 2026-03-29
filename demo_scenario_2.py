import sys
import os
import re
import unicodedata

# Them thu muc src vao sys.path de import duoc package legal_rag
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from legal_rag.retrieval import LegalRetriever
except ImportError as e:
    print(f"[!] Loi import: {e}")
    print("[!] Hay chac chan ban dang chay script tu thu muc goc cua du an.")
    sys.exit(1)

def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

def slugify(value: str) -> str:
    folded = strip_accents(value).lower()
    folded = re.sub(r"[^a-z0-9]+", "_", folded).strip("_")
    return folded

def extract_clause_and_version(query: str):
    """Trích xuất tên điều và phiên bản từ câu truy vấn. Ví dụ: 'Điều 4 bản V1'."""
    # Tìm phiên bản (v1, v2)
    match = re.search(r'\b(v1|v2|bản v1|bản v2)\b', query.lower())
    version = "v1" # Mặc định
    if match:
        version_str = match.group(1)
        if "v1" in version_str:
            version = "v1"
        elif "v2" in version_str:
            version = "v2"
            
    # Xoá phần "bản V1" khỏi để lấy tên Điều
    clause_name = re.sub(r'(?i)\b(bản\s+)?v[12]\b', '', query).strip()
    return clause_name, version

def main():
    print("="*60)
    print("DEMO KỊCH BẢN 2: TÌM ĐIỀU ĐỔI SỐ THỨ TỰ BẰNG SEMANTIC SEARCH")
    print("="*60)
    
    clause_input = input("[?] Nhập câu truy vấn (ví dụ: Điều 4 bản V1): ").strip()
    if not clause_input:
        print("[!] Vui lòng nhập câu truy vấn.")
        return

    clause_name, source_version = extract_clause_and_version(clause_input)
    logical_id = slugify(clause_name)
    target_version = "v1" if source_version == "v2" else "v2"
    
    print(f"[*] Phân tích: Điều = '{clause_name}' (ID: {logical_id}), Phiên bản gốc = {source_version}, Tìm kiềm tại = {target_version}")

    retriever = LegalRetriever()

    # BƯỚC 1: LẤY RAW TEXT CỦA BẢN GỐC (Dùng filter chính xác)
    print(f"\n[*] BƯỚC 1: Lấy nội dung gốc của {clause_name} từ bản {source_version}...")
    source_results = retriever.retrieve(
        query=clause_name, # Query text không quan trọng lắm do dùng exact filter
        k=5, 
        filter_dict={"$and": [{"logical_id": logical_id}, {"version": source_version}]}
    )
    
    if not source_results:
        print(f"[!] Không tìm thấy dữ liệu cho '{clause_name}' trong phiên bản {source_version}.")
        return

    # Có thể clause_name bị chia thành nhiều chunk, nên nối lại
    source_text = "\n".join([res["content"] for res in source_results])
    
    print("\n" + "-"*30)
    print(f">>> RAW TEXT: {clause_name.upper()} ({source_version.upper()})")
    print("-"*30)
    print(source_text)
    print("-"*30)

    # BƯỚC 2: SEMANTIC SEARCH BẢN ĐÍCH DỰA TRÊN NỘI DUNG VỪA TÌM THẤY
    print(f"\n[*] BƯỚC 2: Tìm kiếm tương đồng ngữ nghĩa trong bản {target_version} dựa trên text của {source_version}...")
    
    # Chỉ lấy top 1 kết quả liên quan nhất
    target_results = retriever.retrieve(
        query=source_text,
        k=1,
        filter_dict={"version": target_version}
    )
    
    if not target_results:
        print(f"[!] Không tìm thấy nội dung tương tự nào trong phiên bản {target_version}.")
        return
        
    best_match = target_results[0]
    matched_id = best_match["metadata"].get("logical_id", "Unknown")
    matched_heading = best_match["metadata"].get("chunk_heading", "Unknown")
    distance = best_match.get("distance", "N/A")
    
    print("\n" + "="*60)
    print(f"KẾT QUẢ TÌM KIẾM TRONG BẢN {target_version.upper()}")
    print("="*60)
    print(f">>> Đã tìm thấy đoạn tương đồng ({matched_id} | distance = {distance:.4f}):")
    print(f"    Heading: {matched_heading}")
    print("-"*30)
    print(best_match["content"])
    print("-"*30)

if __name__ == "__main__":
    main()
