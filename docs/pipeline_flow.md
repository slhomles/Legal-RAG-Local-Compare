# Luong xu ly so sanh hai phien ban hop dong

> Mo ta chi tiet tung buoc tu khi nguoi dung tai len 2 file DOCX cho den khi nhan duoc bao cao so sanh.

---

## Tong quan

```
Upload 2 DOCX ──► Xu ly van ban ──► Nhung vector ──► Luu ChromaDB
                                                           │
           Hien thi bao cao ◄── Sinh bao cao ◄── Trich dan ◄── So sanh LLM
```

**Cac module tham gia theo thu tu:**

| Buoc | Module | File |
|------|--------|------|
| 1 | Giao dien Gradio | `src/legal_rag/ui/app.py` |
| 2 | Xu ly van ban DOCX | `src/legal_rag/ingest/document_processor.py` |
| 3 | Nhung vector (Embedding) | `src/legal_rag/db/embedding.py` |
| 4 | Luu tru ChromaDB | `src/legal_rag/db/vector_store.py` |
| 5 | Truy xuat ngu nghia | `src/legal_rag/retrieval/retriever.py` |
| 6 | Ghep cap dieu khoan | `src/legal_rag/retrieval/context_pairing.py` |
| 7 | So sanh bang LLM | `src/legal_rag/generation/comparator.py` |
| 8 | Prompt va guardrails | `src/legal_rag/generation/prompts.py` |
| 9 | Anh xa trich dan | `src/legal_rag/generation/citation.py` |
| 10 | Sinh bao cao | `src/legal_rag/generation/report.py` |
| 11 | Cau hinh trung tam | `src/legal_rag/config.py` |

---

## Buoc 1: Nguoi dung tai len 2 file DOCX (UI)

**File:** `src/legal_rag/ui/app.py`

Nguoi dung truy cap giao dien Gradio tai `http://127.0.0.1:7860`, tai len 2 file `.docx` vao 2 o upload (phien ban cu va moi), sau do nhap "so sanh" vao khung chat.

### 1.1. Nhan dien tu khoa

Ham `handle_message()` kiem tra tin nhan cua nguoi dung co chua tu khoa so sanh khong:

```python
_COMPARE_KW = ["so sanh", "bao cao", "report", "compare", "phan tich", "thay doi"]
```

Neu khop → goi 2 ham chinh: `_ingest_files()` va `_run_comparison()`.

### 1.2. Trich xuat thong tin tu ten file

Ham `_extract_doc_info()` dung regex de lay `doc_id` va `version` tu ten file:

```python
# Regex: (.+?)_(v\d+)\.docx$
# Vi du: "Hop_dong_A_v1.docx" → doc_id="Hop_dong_A", version="v1"
```

Neu ten file khong theo quy uoc → dung ten file lam `doc_id`, gan `v1`/`v2` theo thu tu upload.

### 1.3. Sao chep va chuan bi

```python
# Copy file vao thu muc du lieu
shutil.copy2(path_old, "data/raw/Hop_dong_A_v1.docx")
shutil.copy2(path_new, "data/raw/Hop_dong_A_v2.docx")
```

Sau do khoi tao `DocumentProcessor` va `VectorStoreManager`, goi `store.reset_collection()` de xoa du lieu cu trong ChromaDB truoc khi nap moi.

---

## Buoc 2: Xu ly van ban DOCX (Document Processing)

**File:** `src/legal_rag/ingest/document_processor.py`

### 2.1. Doc file DOCX

Su dung thu vien `python-docx` de doc toan bo noi dung van ban:

```python
doc = Document(file_path)
raw_text = "\n".join([para.text for para in doc.paragraphs])
```

### 2.2. Lam sach van ban

```python
def clean_text(raw_text):
    text = raw_text.replace("\xa0", " ")       # Xoa non-breaking space
    text = re.sub(r"[ \t]{2,}", " ", text)     # Gop nhieu khoang trang
    text = re.sub(r"\n{3,}", "\n\n", text)     # Gop nhieu dong trong
    return text.strip()
```

### 2.3. Chia doan theo cau truc phap ly (Semantic Chunking)

Day la buoc quan trong nhat — he thong nhan dien cau truc hop dong bang **4 lop regex** theo thu tu uu tien:

#### Lop 1 — Dieu khoan (uu tien cao nhat):
```
LEGAL_CHUNK_REGEX = r"(?im)^(?P<heading>[ \t]*(?:dieu|đieu)[ \t]+\d+[\.:\-]?[ \t]*[^\n]*)$"
```
Nhan dien: `Dieu 1.`, `Dieu 2:`, `Dieu 3 - Ten dieu khoan`

#### Lop 2 — Cau truc cap cao (Chuong/Muc/Phan):
```
STRUCTURE_CHUNK_REGEX = r"(?im)^(?P<heading>[ \t]*(?:chuong|muc|phan)[ \t]+[ivxlcdm0-9]+...)"
```
Nhan dien: `Chuong I`, `Muc II.`, `Phan III - ...`

#### Lop 3 — Dinh nghia:
```
DEFINITION_REGEX = r"(?im)^(?P<heading>[ \t]*(?:dinh nghia|giai thich tu ngu)[\.:\-]?[ \t]*)$"
```

#### Lop 4 — Heading tong quat (uu tien thap nhat):
```
GENERIC_HEADING_REGEX — Nhan dien dong bat dau bang chu in hoa, dai 4-120 ky tu
```

### 2.4. Quy trinh chia doan chi tiet

```
1. Tim tat ca heading trong van ban bang 4 regex
2. Loai bo trung lap tai cung vi tri (giu regex co uu tien cao hon)
3. Sap xep theo vi tri xuat hien
4. Chon marker de chia:
   - Neu co "Dieu X" → chi dung cac dieu khoan
   - Neu khong → dung tat ca heading
5. Cat van ban tai cac vi tri heading
6. Moi doan duoc gan metadata:
   - logical_id: "dieu_3" (slug cua heading)
   - chunk_heading: "Dieu 3. Thoi gian giao hang"
   - hierarchy_path: "Phan I > Chuong II > Dieu 3"
7. Neu doan qua dai (> 512 token):
   - Chia nho bang token-based splitting
   - Overlap: 64 token giua cac phan
```

### 2.5. Dinh dang chunk_id

```python
# Format: "{doc_id}:{version}:{logical_id}:{part_index}"
# Vi du: "Hop_dong_A:v1:dieu_3:p01"
#         "Hop_dong_A:v2:dieu_3:p02" (neu dieu 3 bi chia thanh 2 phan)
```

### 2.6. Cau truc du lieu dau ra cua moi chunk

```json
{
  "id": "Hop_dong_A:v1:dieu_3:p01",
  "content": "Dieu 3. Thoi gian va dia diem giao hang\nTrong vong 30 ngay ke tu ngay ky...",
  "metadata": {
    "doc_id": "Hop_dong_A",
    "version": "v1",
    "chunk_index": 5,
    "chunk_heading": "Dieu 3. Thoi gian va dia diem giao hang",
    "hierarchy_path": "Dieu 3. Thoi gian va dia diem giao hang",
    "logical_id": "dieu_3"
  }
}
```

### 2.7. Fallback khi khong tim thay cau truc

Neu khong co heading nao duoc phat hien (van ban khong co cau truc ro rang):

```python
def _fallback_chunk_by_tokens(text, metadata):
    # Chia theo gioi han token: 512 token/chunk, overlap 64 token
    # Dat ten: "Doan 1", "Doan 2", ...
    # logical_id: "doan_1", "doan_2", ...
```

---

## Buoc 3: Nhung vector (Embedding)

**File:** `src/legal_rag/db/embedding.py`

### 3.1. Tai mo hinh BGE-M3

```python
class BGEEmbeddingModel:
    def __init__(self, model_name="BAAI/bge-m3", device="cpu"):
        # Che do offline — khong tai tu internet
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        self.model = AutoModel.from_pretrained(model_name, local_files_only=True)
        self.model.to(device)
        self.model.eval()  # Che do suy luan, tat gradient
```

**Tai sao chon BGE-M3?**
- Ho tro da ngon ngu, dac biet tieng Viet
- Xu ly ngu canh dai (len den 8192 token)
- Kich thuoc vector: 1024 chieu

### 3.2. Quy trinh nhung (embed_documents)

```
Dau vao: Danh sach cac doan van ban (strings)
         ↓
[1] Tokenize: AutoTokenizer(texts, padding=True, truncation=True)
         ↓
[2] Forward pass: model(**tokens) → outputs.last_hidden_state
    Ket qua: Ma tran [batch_size × seq_len × 1024]
    (Moi token duoc bieu dien bang vector 1024 chieu)
         ↓
[3] Mean Pooling: Tinh trung binh co trong cua tat ca token
    Formula: embedding[i] = Sum(token[j] * mask[j]) / Sum(mask[j])
    (mask = attention_mask, bo qua cac token padding)
    Ket qua: Vector [batch_size × 1024]
         ↓
[4] L2 Normalization: Chuan hoa do dai vector = 1
    Formula: v_norm = v / ||v||
    (Dam bao khoang cach cosine hoat dong chinh xac)
         ↓
Dau ra: Danh sach cac vector [1024 chieu], moi vector dai 1.0
```

### 3.3. Vi sao can Mean Pooling + L2 Norm?

- **Mean Pooling**: Mo hinh tra ve embedding cho TUNG token. Can gop thanh 1 vector dai dien cho CA doan van. Mean pooling tinh trung binh, trong so boi attention mask de bo qua padding.
- **L2 Normalization**: Chuan hoa de khoang cach cosine giua 2 vector nam trong [0, 2]. Vector cung huong = khoang cach nho = ngu nghia tuong tu.

---

## Buoc 4: Luu tru vao ChromaDB

**File:** `src/legal_rag/db/vector_store.py`

### 4.1. Khoi tao ket noi

```python
client = chromadb.PersistentClient(path="data/chroma_db/")
vector_db = client.get_or_create_collection(name="legal_contracts_collection")
```

ChromaDB luu tru duoi dang SQLite tai `data/chroma_db/chroma.sqlite3`.

### 4.2. Luu du lieu (Upsert)

```python
vector_db.upsert(
    ids=["Hop_dong_A:v1:dieu_1:p01", "Hop_dong_A:v1:dieu_2:p01", ...],
    documents=["Noi dung dieu 1...", "Noi dung dieu 2...", ...],
    metadatas=[{"doc_id": "Hop_dong_A", "version": "v1", ...}, ...],
    embeddings=[[0.023, -0.015, ...], [0.041, 0.008, ...], ...]
)
```

**Upsert**: Neu `id` da ton tai → ghi de. Neu chua → them moi. Dam bao khong trung lap.

### 4.3. Cau truc du lieu trong ChromaDB

```
Collection: "legal_contracts_collection"
├── Document 1: id="Hop_dong_A:v1:dieu_1:p01"
│   ├── text: "Dieu 1. Dinh nghia..."
│   ├── embedding: [1024 floats]
│   └── metadata: {doc_id, version, logical_id, chunk_heading, ...}
├── Document 2: id="Hop_dong_A:v1:dieu_2:p01"
│   └── ...
├── Document 3: id="Hop_dong_A:v2:dieu_1:p01"
│   └── ...
└── ...
```

---

## Buoc 5: Truy xuat ngu nghia (Semantic Retrieval)

**File:** `src/legal_rag/retrieval/retriever.py`

Khi bat dau so sanh, `DocumentComparator` goi `LegalRetriever` de lay tat ca chunk cua 2 phien ban.

### 5.1. Truy van voi bo loc metadata

```python
filter_dict = {
    "$and": [
        {"doc_id": "Hop_dong_A"},
        {"version": {"$in": ["v1", "v2"]}}
    ]
}

results = retriever.retrieve(
    query="hop dong Hop_dong_A",  # Query tong quat (metadata filter la chinh)
    k=20,                         # Lay toi da 20 chunk
    filter_dict=filter_dict
)
```

### 5.2. Quy trinh truy xuat

```
Query text: "hop dong Hop_dong_A"
         ↓
[1] Nhung query: embed_query(text) → vector [1024]
         ↓
[2] Tim kiem KNN trong ChromaDB:
    - So sanh khoang cach cosine voi tat ca vector trong collection
    - Loc theo metadata: chi lay chunk co doc_id va version phu hop
    - Tra ve top-k ket qua gan nhat
         ↓
[3] Dinh dang ket qua:
    Moi ket qua gom: {rank, id, content, metadata, distance}
```

### 5.3. Cau truc ket qua tra ve

```python
[
    {
        "rank": 1,
        "id": "Hop_dong_A:v1:dieu_1:p01",
        "content": "Dieu 1. Dinh nghia\n\"Hang hoa\" la san pham dien tu...",
        "metadata": {
            "doc_id": "Hop_dong_A",
            "version": "v1",
            "logical_id": "dieu_1",
            "chunk_heading": "Dieu 1. Dinh nghia",
            "hierarchy_path": "Dieu 1. Dinh nghia"
        },
        "distance": 0.234
    },
    {
        "rank": 2,
        "id": "Hop_dong_A:v2:dieu_1:p01",
        "content": "Dieu 1. Dinh nghia\n\"Hang hoa\" la san pham dien tu bao gom...",
        "metadata": {"version": "v2", ...},
        "distance": 0.241
    },
    ...
]
```

---

## Buoc 6: Ghep cap dieu khoan (Context Pairing)

**File:** `src/legal_rag/retrieval/context_pairing.py`

### 6.1. Nhom theo logical_id va version

```python
class ContextPairer:
    def pair_chunks(self, retrieved_chunks):
        # Nhom: {logical_id → {version → [list of content strings]}}
        # Noi cac chunk cung logical_id + version lai voi nhau
```

### 6.2. Minh hoa quy trinh ghep cap

```
Dau vao (danh sach chunk phang):
  chunk 1: logical_id="dieu_1", version="v1", content="..."
  chunk 2: logical_id="dieu_1", version="v2", content="..."
  chunk 3: logical_id="dieu_3", version="v1", content="..."
  chunk 4: logical_id="dieu_3", version="v2", content="..."
  chunk 5: logical_id="dieu_6", version="v2", content="..."  ← chi co v2
         ↓
Dau ra (dict ghep cap):
{
  "dieu_1": {
    "v1": "Noi dung dieu 1 phien ban cu...",
    "v2": "Noi dung dieu 1 phien ban moi..."
  },
  "dieu_3": {
    "v1": "Noi dung dieu 3 phien ban cu...",
    "v2": "Noi dung dieu 3 phien ban moi..."
  },
  "dieu_6": {
    "v2": "Noi dung dieu 6 chi co trong phien ban moi..."
  }
}
```

### 6.3. Phan loai dieu khoan

Sau khi ghep cap, `DocumentComparator` phan loai:

```python
common_clauses = [cid for cid if cid co ca v1 va v2]     # → So sanh bang LLM
new_clauses = [cid for cid if chi co v2]                  # → Danh dau la THEM
removed_clauses = [cid for cid if chi co v1]              # → Danh dau la XOA
```

---

## Buoc 7: So sanh tung dieu khoan bang LLM

**File:** `src/legal_rag/generation/comparator.py`

### 7.1. Voi moi cap dieu khoan chung (common_clauses)

```
Dieu 3 phien ban v1: "Trong vong 30 ngay ke tu ngay ky hop dong."
Dieu 3 phien ban v2: "Trong vong 45 ngay ke tu ngay ky hop dong."
         ↓
Dien vao COMPARISON_USER_TEMPLATE
         ↓
Gui den Ollama API (qwen2.5:latest)
```

### 7.2. Goi Ollama API

```python
url = "http://localhost:11434/api/chat"
payload = {
    "model": "qwen2.5:latest",
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    "stream": False,
    "options": {
        "temperature": 0.0,      # Khong sang tao, chi mo ta chinh xac
        "num_predict": 4096      # Gioi han do dai phan hoi
    }
}
response = requests.post(url, json=payload, timeout=300)
```

**Tai sao temperature = 0.0?**
He thong phap ly yeu cau do chinh xac tuyet doi. Temperature 0.0 ep mo hinh luon chon tu co xac suat cao nhat, khong ngau nhien, khong sang tao.

### 7.3. Prompt he thong (SYSTEM_PROMPT)

**File:** `src/legal_rag/generation/prompts.py`

LLM duoc huong dan boi 5 quy tac nghiem ngat:

```
1. CHI DUA TREN BANG CHUNG: Chi trich xuat noi dung co trong van ban.
   Khong co bang chung → Khong ket luan.

2. CAM KET LUAN PHAP LY: Khong duoc noi "hop phap", "vi pham phap luat",
   "khuyen nghi", "rui ro phap ly".

3. CAM DANH GIA: Chi MO TA thay doi, khong DANH GIA
   (khong noi "tot hon", "chat che hon", "long leo hon").

4. DINH DANG: Tra loi bang tieng Viet, theo cau truc co dinh.

5. KHI KHONG CO THAY DOI: Tra ve "Khong phat hien thay doi nao."
```

### 7.4. Prompt so sanh (COMPARISON_USER_TEMPLATE)

```
So sanh dieu khoan: {clause_heading}

PHIEN BAN CU ({version_old}):
{text_old}

PHIEN BAN MOI ({version_new}):
{text_new}

Yeu cau: Liet ke TUNG thay doi voi format:
- **Loai thay doi**: THEM | XOA | SUA
- **Noi dung cu**: «...» (de trong neu THEM)
- **Noi dung moi**: «...» (de trong neu XOA)
- **Vi tri**: mo ta vi tri thay doi
```

### 7.5. Parse ket qua LLM

LLM tra ve van ban dang:

```
**Loai thay doi**: SUA
**Noi dung cu**: «Trong vong 30 ngay ke tu ngay ky hop dong.»
**Noi dung moi**: «Trong vong 45 ngay ke tu ngay ky hop dong.»
**Vi tri**: Thoi han giao hang
```

He thong dung regex de trich xuat thanh cau truc:

```python
# Regex nhan dien loai thay doi
type_pattern = r"\*{0,2}Loai thay doi\*{0,2}\s*[:]\s*(THEM|XOA|SUA)"

# Regex nhan dien noi dung cu/moi (ho tro nhieu dang ngoac kep)
old_pattern = r"\*{0,2}Noi dung cu\*{0,2}\s*[:]\s*[«\"']?(.*?)[»\"']?\s*$"
new_pattern = r"\*{0,2}Noi dung moi\*{0,2}\s*[:]\s*[«\"']?(.*?)[»\"']?\s*$"

# Regex nhan dien vi tri
loc_pattern = r"\*{0,2}Vi tri\*{0,2}\s*[:]\s*(.*?)$"
```

**Fallback**: Neu LLM tra ve format khac voi mong doi → luu nguyen ban voi `type="RAW"`.

### 7.6. Kiem tra guardrails

Sau khi nhan ket qua, kiem tra xem LLM co vi pham quy tac khong:

```python
GUARDRAIL_BANNED_PHRASES = [
    "hop phap",
    "vi pham phap luat",
    "vi pham luat",
    "khuyen nghi",
    "rui ro phap ly",
    "nen thay doi",
    "nen sua",
    "nen bo sung",
    "co loi hon",
    "bat loi hon",
    "chat che hon",
    "long leo hon",
    "tu van phap luat",
    "theo quy dinh cua phap luat",
    "trai phap luat",
]

def check_guardrails(text):
    violations = [phrase for phrase in BANNED if phrase in text.lower()]
    return (len(violations) == 0, violations)
```

### 7.7. Cau truc du lieu sau buoc so sanh

```json
{
  "doc_id": "Hop_dong_A",
  "version_old": "v1",
  "version_new": "v2",
  "clauses": {
    "dieu_1": {
      "heading": "Dieu 1. Dinh nghia",
      "changes": [
        {
          "type": "SUA",
          "old_text": "laptop, may tinh ban va phu kien",
          "new_text": "laptop, may tinh ban, man hinh va phu kien",
          "location": "Danh sach hang hoa"
        }
      ],
      "raw_llm_response": "...",
      "guardrail_ok": true,
      "guardrail_violations": []
    },
    "dieu_3": {
      "heading": "Dieu 3. Thoi gian giao hang",
      "changes": [
        {
          "type": "SUA",
          "old_text": "30 ngay",
          "new_text": "45 ngay",
          "location": "Thoi han giao hang"
        },
        {
          "type": "THEM",
          "old_text": "",
          "new_text": "Ben A duoc quyen lua chon don vi van chuyen.",
          "location": "Quyen lua chon van chuyen"
        }
      ],
      "guardrail_ok": true
    },
    "dieu_6": {
      "heading": "Dieu 6. Phat vi pham",
      "changes": [
        {
          "type": "THEM",
          "old_text": "",
          "new_text": "Dieu 6. Phat vi pham\n5.1. Ben nao vi pham...",
          "location": "Dieu khoan moi trong v2"
        }
      ]
    }
  },
  "new_clauses": ["dieu_6", "dieu_7"],
  "removed_clauses": []
}
```

---

## Buoc 8: Anh xa trich dan (Citation Mapping)

**File:** `src/legal_rag/generation/citation.py`

Muc dich: Voi moi thay doi LLM phat hien, tim lai **vi tri chinh xac** trong chunk goc de chung minh nguon goc.

### 8.1. Xay dung bang tra cuu chunk

```python
def _build_chunk_lookup(doc_id, version_old, version_new, k=50):
    # Truy xuat 50 chunk tu ChromaDB (nhieu hon buoc so sanh de dam bao day du)
    # Nhom theo "logical_id:version" lam key
    # Vi du: chunk_lookup["dieu_3:v1"] = {chunk_id, content, metadata}
```

```
chunk_lookup = {
    "dieu_1:v1": {
        "chunk_id": "Hop_dong_A:v1:dieu_1:p01",
        "content": "Dieu 1. Dinh nghia\n\"Hang hoa\" la san pham...",
        "metadata": {...}
    },
    "dieu_1:v2": {
        "chunk_id": "Hop_dong_A:v2:dieu_1:p01",
        "content": "Dieu 1. Dinh nghia\n\"Hang hoa\" la san pham dien tu bao gom...",
        "metadata": {...}
    },
    ...
}
```

### 8.2. Tim kiem trich dan cho moi thay doi

Voi moi thay doi, tim 2 nguon:
- `old_source`: Tim `old_text` trong chunk cua phien ban cu
- `new_source`: Tim `new_text` trong chunk cua phien ban moi

### 8.3. Quy trinh doi chieu — 3 cap do

Ham `_locate_excerpt()` thu 3 phuong phap theo thu tu:

```
Dau vao: excerpt = "Trong vong 30 ngay ke tu ngay ky hop dong."
         chunk_content = "Dieu 3. Thoi gian...\nTrong vong 30 ngay ke tu ngay ky hop dong.\n..."
         ↓
[Cap do 1] EXACT MATCH (Khop chinh xac):
  pos = chunk_content.find(excerpt)
  Neu tim thay → tra ve match_type="exact", char_start=pos
         ↓ (neu khong khop)
[Cap do 2] NORMALIZED MATCH (Chuan hoa khoang trang):
  Gop tat ca khoang trang/tab/xuong dong thanh 1 khoang trang
  normalized_content = " ".join(content.split())
  normalized_excerpt = " ".join(excerpt.split())
  Neu tim thay → tra ve match_type="normalized"
         ↓ (neu van khong khop)
[Cap do 3] PARTIAL MATCH (Khop 40 ky tu dau):
  partial = excerpt[:40]
  pos = chunk_content.find(partial)
  Neu tim thay → tra ve match_type="partial"
         ↓ (neu van khong)
Tra ve: {"found": False, "reason": "Khong tim thay trong chunk"}
```

### 8.4. Cau truc trich dan dau ra

```json
{
  "old_source": {
    "found": true,
    "match_type": "exact",
    "chunk_id": "Hop_dong_A:v1:dieu_3:p01",
    "heading": "Dieu 3. Thoi gian giao hang",
    "hierarchy_path": "Dieu 3. Thoi gian giao hang",
    "doc_id": "Hop_dong_A",
    "version": "v1",
    "excerpt": "Trong vong 30 ngay ke tu ngay ky hop dong.",
    "char_start": 66,
    "char_end": 110
  },
  "new_source": {
    "found": true,
    "match_type": "exact",
    "chunk_id": "Hop_dong_A:v2:dieu_3:p01",
    "heading": "Dieu 3. Thoi gian giao hang",
    "char_start": 66,
    "char_end": 110
  }
}
```

`char_start` va `char_end` cho phep xac dinh **chinh xac vi tri** trong chunk goc — huu ich khi can highlight trong UI.

---

## Buoc 9: Sinh bao cao (Report Generation)

**File:** `src/legal_rag/generation/report.py`

### 9.1. Thu thap tat ca thay doi

```python
def _collect_changes(comparison_result):
    # Duyet tat ca clauses → gop thanh 1 danh sach phang
    # Moi item gom: clause_id, heading, type, old_text, new_text, location, citations
```

### 9.2. Dinh dang van ban dau vao cho LLM

```python
def _format_changes_text(changes):
    # Gioi han old_text/new_text toi da 120 ky tu (giam kich thuoc prompt)
    MAX_TEXT = 120

    # Format thanh danh sach co so thu tu:
    # "1. [Dieu 1. Dinh nghia] Loai: SUA
    #    Noi dung cu: laptop, may tinh ban va phu kien...
    #    Noi dung moi: laptop, may tinh ban, man hinh va phu kien...
    #    Trich dan (old_source): chunk=..., match=exact, pos=25"
```

### 9.3. Goi LLM de tom tat

Su dung `SUMMARY_USER_TEMPLATE` yeu cau LLM nhom thay doi theo:

```
1. Thay doi ve noi dung tai chinh (gia ca, thanh toan)
2. Thay doi ve thoi han va dieu kien
3. Thay doi ve quyen va nghia vu cac ben
4. Dieu khoan them moi hoac bi xoa
```

### 9.4. Fallback khi LLM that bai

Neu LLM timeout hoac loi ket noi (phan hoi bat dau bang `[LOI]`):

```python
def _rule_based_summary(changes, doc_id, version_old, version_new):
    # Dem so luong theo loai thay doi
    # Liet ke cac dieu khoan bi anh huong
    # Tra ve tom tat don gian khong can LLM:

    # "Tom tat thay doi giua v1 va v2 cua tai lieu Hop_dong_A:
    #  - Tong so thay doi phat hien: 9
    #    + SUA: 3 thay doi
    #    + THEM: 5 thay doi
    #    + RAW: 1 thay doi
    #  - Cac dieu khoan bi anh huong: Dieu 1, Dieu 3, Dieu 6, ...
    #  (Tom tat duoc tao tu quy tac do LLM khong phan hoi trong thoi gian cho.)"
```

### 9.5. Kiem tra guardrails lan cuoi

Neu LLM tra ve tom tat thanh cong → kiem tra lai `check_guardrails()`.
Neu phat hien cum tu vi pham → chen canh bao vao dau bao cao.

### 9.6. Cau truc bao cao cuoi cung

```json
{
  "doc_id": "Hop_dong_A",
  "version_old": "v1",
  "version_new": "v2",
  "changes_detail": [
    {
      "clause_id": "dieu_1",
      "heading": "Dieu 1. Dinh nghia",
      "type": "SUA",
      "old_text": "...",
      "new_text": "...",
      "location": "...",
      "citations": {"old_source": {...}, "new_source": {...}}
    },
    ...
  ],
  "summary": "Tom tat cac thay doi quan trong...",
  "guardrail_ok": true,
  "guardrail_violations": []
}
```

---

## Buoc 10: Hien thi bao cao cho nguoi dung

### 10.1. Dinh dang plain text

Ham `format_plain_text()` chuyen bao cao JSON thanh van ban de doc:

```
======================================================================
BAO CAO THAY DOI HOP DONG: Hop_dong_A
So sanh: v1 -> v2
======================================================================

--- CHI TIET THAY DOI ---

  1. [SUA] Dieu 1. Dinh nghia
     Cu : laptop, may tinh ban va phu kien kem theo
     Moi: laptop, may tinh ban, man hinh va phu kien kem theo
     -> old_source: Hop_dong_A:v1:dieu_1:p01 [exact] pos=25
     -> new_source: Hop_dong_A:v2:dieu_1:p01 [exact] pos=25

  2. [SUA] Dieu 3. Thoi gian giao hang
     Cu : Trong vong 30 ngay ke tu ngay ky hop dong.
     Moi: Trong vong 45 ngay ke tu ngay ky hop dong.
     -> old_source: Hop_dong_A:v1:dieu_3:p01 [exact] pos=66
     -> new_source: Hop_dong_A:v2:dieu_3:p01 [exact] pos=66

  3. [THEM] Dieu 6. Phat vi pham
     Moi: Dieu 6. Phat vi pham...
     -> new_source: Hop_dong_A:v2:dieu_6:p01 [exact] pos=0

--- TOM TAT THAY DOI QUAN TRONG ---

Tom tat thay doi giua v1 va v2 cua tai lieu Hop_dong_A:
- Tong so thay doi phat hien: 9
  + SUA: 3 thay doi
  + THEM: 5 thay doi
- Cac dieu khoan bi anh huong: Dieu 1, Dieu 3, Dieu 6, ...

======================================================================
```

### 10.2. Hien thi trong chat

Bao cao duoc tra ve trong Gradio chatbot duoi dang tin nhan cua assistant:

```python
history += [{
    "role": "assistant",
    "content": f"Da phan tich {n_chunks} doan van ban ({doc_id}: {ver_old} -> {ver_new}).\n\n{report_text}"
}]
```

---

## So do tong hop

```
                         NGUOI DUNG
                            │
                    Upload 2 file DOCX
                    Nhap "so sanh"
                            │
                     ┌──────▼──────┐
                     │   GRADIO UI  │  (app.py)
                     │  handle_msg  │
                     └──────┬──────┘
                            │
              ┌─────────────▼─────────────┐
              │      _ingest_files()       │
              │                            │
              │  ┌──────────────────────┐  │
              │  │  DocumentProcessor   │  │  doc_processor.py
              │  │  read_docx()         │  │
              │  │  clean_text()        │  │
              │  │  semantic_chunking() │  │  ← 4 lop regex
              │  └──────────┬───────────┘  │
              │             │              │
              │  ┌──────────▼───────────┐  │
              │  │  BGEEmbeddingModel   │  │  embedding.py
              │  │  tokenize → forward  │  │
              │  │  mean pool → L2 norm │  │
              │  └──────────┬───────────┘  │
              │             │              │
              │  ┌──────────▼───────────┐  │
              │  │  VectorStoreManager  │  │  vector_store.py
              │  │  ChromaDB.upsert()   │  │
              │  └──────────────────────┘  │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼─────────────┐
              │     _run_comparison()      │
              │                            │
              │  ┌──────────────────────┐  │
              │  │ DocumentComparator   │  │  comparator.py
              │  │                      │  │
              │  │ [1] Retrieve chunks  │◄─┼── retriever.py
              │  │     (metadata filter)│  │
              │  │ [2] Pair by clause   │◄─┼── context_pairing.py
              │  │ [3] For each pair:   │  │
              │  │     Call Ollama LLM   │◄─┼── prompts.py (COMPARISON_TEMPLATE)
              │  │     Parse response   │  │
              │  │     Check guardrails │  │
              │  └──────────┬───────────┘  │
              │             │              │
              │  ┌──────────▼───────────┐  │
              │  │   CitationMapper     │  │  citation.py
              │  │                      │  │
              │  │ [4] Build chunk      │  │
              │  │     lookup table     │  │
              │  │ [5] For each change: │  │
              │  │     Exact match      │  │
              │  │     → Normalized     │  │
              │  │     → Partial        │  │
              │  │     → Not found      │  │
              │  └──────────┬───────────┘  │
              │             │              │
              │  ┌──────────▼───────────┐  │
              │  │  ReportGenerator     │  │  report.py
              │  │                      │  │
              │  │ [6] Collect changes  │  │
              │  │ [7] Format text      │  │
              │  │ [8] Call LLM summary │◄─┼── prompts.py (SUMMARY_TEMPLATE)
              │  │     OR fallback      │  │
              │  │ [9] Check guardrails │  │
              │  │ [10] format_plain()  │  │
              │  └──────────┬───────────┘  │
              └─────────────┬──────────────┘
                            │
                     ┌──────▼──────┐
                     │   GRADIO UI  │
                     │  Hien thi    │
                     │  bao cao     │
                     └──────┬──────┘
                            │
                      NGUOI DUNG DOC
                       BAO CAO
```
