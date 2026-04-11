# Chứa các tham số cấu hình (đường dẫn DB, model name: bge-m3, ollama host)
import os
from pathlib import Path

# ==========================================
# 1. ĐỊNH TUYẾN THƯ MỤC (PATHS)
# Đảm bảo hệ thống luôn tìm đúng đường dẫn dù chạy ở máy nào (Local)
# ==========================================
# Lấy thư mục gốc của dự án.
# File này nằm ở: legal_rag/config.py -> cần lùi 1 cấp để về root project.
BASE_DIR = Path(__file__).resolve().parents[1]

# Các thư mục dữ liệu
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"                 # Chứa file DOCX/PDF gốc
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"    # Chứa kết quả chuẩn để đánh giá
CHROMA_DB_DIR = DATA_DIR / "chroma_db"          # Nơi lưu trữ Vector DB cục bộ

# Tự động tạo thư mục nếu chưa tồn tại
for path in [RAW_DATA_DIR, GROUND_TRUTH_DIR, CHROMA_DB_DIR]:
    path.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. CẤU HÌNH VECTOR DATABASE & EMBEDDING
# Chạy ở Tuần 3-4: Xây dựng cơ sở dữ liệu vector [cite: 34]
# ==========================================
CHROMA_COLLECTION_NAME = "legal_contracts_collection"

# Mô hình BGE-M3 (Hỗ trợ đa ngôn ngữ, tiếng Việt cực tốt, ngữ cảnh dài)
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
# Cấu hình thiết bị chạy: 'cuda' nếu bạn có GPU Nvidia, hoặc 'cpu'
DEVICE = "cuda" if os.environ.get("USE_GPU") == "1" else "cpu" 


# ==========================================
# 3. CẤU HÌNH CHUNKING (CHIA ĐOẠN)
# Xử lý theo cấu trúc hợp đồng [cite: 15]
# ==========================================
# Regex nhận diện các điều khoản pháp lý theo dạng "Điều 1", "Dieu 1"...
# Dùng named-group "heading" để tái sử dụng thống nhất trong processor.
LEGAL_CHUNK_REGEX = r"(?im)^(?P<heading>[ \t]*(?:điều|dieu)[ \t]+\d+[\.\:\-]?[ \t]*[^\n]*)$"

# Regex nhận diện các mốc cấu trúc cấp cao (Chương/Mục/Phần).
STRUCTURE_CHUNK_REGEX = (
    r"(?im)^(?P<heading>[ \t]*(?:chương|chuong|mục|muc|phần|phan)[ \t]+[ivxlcdm0-9]+(?:[\.\:\-]?[ \t]*[^\n]*)?)$"
)

# Regex heading tổng quát cho văn bản legal không ghi rõ "Điều x".
# Ví dụ: "Phạm vi điều chỉnh", "Đối tượng áp dụng", "Lấy người dùng làm trung tâm".
GENERIC_HEADING_REGEX = (
    r"(?im)^(?P<heading>"
    r"(?=.{4,120}$)"
    r"(?![ \t]*(?:\d+[\.\)]|[a-zđ]\)|[ivxlcdm]+\.)[ \t]*)"
    r"(?![ \t]*(?:căn cứ|can cu|quốc hội ban hành|quoc hoi ban hanh)\b)"
    r"[A-ZÀ-ỴĐ][^\n.;!?]*"
    r")$"
)

# Regex cho "Định nghĩa/Giải thích từ ngữ" (dự phòng cho rule riêng nếu cần).
DEFINITION_REGEX = r"(?im)^(?P<heading>[ \t]*(?:định nghĩa|giải thích từ ngữ)[\.\:\-]?[ \t]*)$"

# Mặc dù chia theo regex, vẫn cần một giới hạn an toàn cho fallback (trường hợp văn bản lỗi)
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64


# ==========================================
# 4. CẤU HÌNH LOCAL LLM (OLLAMA - QWEN 2.5)
# Chuẩn bị cho Tuần 7-8: Sinh báo cáo so sánh [cite: 36]
# ==========================================
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL_NAME = "qwen2.5:1.5b"

# THÔNG SỐ QUAN TRỌNG NHẤT:
# Temperature = 0.0 ép mô hình trả lời chính xác, không sáng tạo
# Giúp tuân thủ nguyên tắc "không bằng chứng -> không kết luận" [cite: 36]
# và không tự ý đưa ra tư vấn pháp lý [cite: 19]
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 4096 # Đủ dài để sinh báo cáo chi tiết
LLM_TIMEOUT = 300     # Giây — tăng cao cho CPU-only inference
