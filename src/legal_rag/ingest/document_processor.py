import re
from pathlib import Path
from typing import Any, Dict, List

import docx

from legal_rag.config import (
    CHUNK_OVERLAP,
    DEFINITION_REGEX,
    GENERIC_HEADING_REGEX,
    LEGAL_CHUNK_REGEX,
    MAX_CHUNK_SIZE,
    STRUCTURE_CHUNK_REGEX,
)

class DocumentProcessor:

    def __init__(self):
        self.legal_regex = re.compile(LEGAL_CHUNK_REGEX, re.MULTILINE)
        self.structure_regex = re.compile(STRUCTURE_CHUNK_REGEX, re.MULTILINE)
        self.generic_heading_regex = re.compile(GENERIC_HEADING_REGEX, re.MULTILINE)
        self.def_regex = re.compile(DEFINITION_REGEX, re.MULTILINE)
    
    def _normalize_clause_id(self, heading: str) -> str:
        """
        Tách clause_id từ heading.
        
        Ví dụ:
          "Điều 1. Định nghĩa" → "Dieu 1"
          "Dieu 1. Dinh nghia" → "Dieu 1"
          "Điều 3. Giá trị hợp đồng" → "Dieu 3"
          "Chương I. Quy định chung" → "Chuong I"
          "Article 5. Payment Terms" → "Article 5"
          "Mở đầu" → "Mo_dau"
        
        Returns:
            str: Clause ID đơn giản, loại bỏ dấu và phần nội dung
        """
        heading = heading.strip()
        
        # Pattern 1: Điều/Dieu/Article X
        pattern_dieu = re.match(r'^(Điều|Dieu|Article|Cau)\s+(\d+)', heading, re.IGNORECASE)
        if pattern_dieu:
            dieu_num = pattern_dieu.group(2)
            return f"Dieu {dieu_num}"
        
        # Pattern 2: Chương/Chuong/Chapter I, II, III, ...
        pattern_chuong = re.match(r'^(Chương|Chuong|Chapter)\s+([IVX]+|i+|v+|x+)', heading, re.IGNORECASE)
        if pattern_chuong:
            chuong_num = pattern_chuong.group(2)
            return f"Chuong {chuong_num}"
        
        # Pattern 3: Mục/Muc/Section X.Y
        pattern_muc = re.match(r'^(Mục|Muc|Section)\s+([\d\.]+)', heading, re.IGNORECASE)
        if pattern_muc:
            muc_num = pattern_muc.group(2)
            return f"Muc {muc_num}"
        
        # Pattern 4: Lớp/Class, Phần/Part/Phan
        pattern_other = re.match(r'^(Lớp|Class|Phần|Phan|Part)\s+(\w+)', heading, re.IGNORECASE)
        if pattern_other:
            other_type = pattern_other.group(1).replace('ớp', '').replace('ần', '')
            other_num = pattern_other.group(2)
            return f"{other_type} {other_num}"
        
        # Fallback: Mở đầu hoặc tên khác
        if "Mở đầu" in heading or "Opening" in heading:
            return "Mo_dau"
        
        # Nếu không match pattern nào, lấy chữ cái đầu tiên của từng từ trong 30 ký tự đầu
        simple_heading = heading[:30].replace(".", "").replace(",", "").strip()
        return simple_heading.replace(" ", "_")
        
    def read_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                # Skip space
                if para.text.strip():
                    full_text.append(para.text.strip())
            return '\n'.join(full_text)
        except Exception as e:
            print(f"Not a docx file {file_path}: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _fallback_chunk_by_length(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not text:
            return []

        chunks = []
        start = 0
        idx = 1
        text_len = len(text)

        while start < text_len:
            end = min(text_len, start + MAX_CHUNK_SIZE)
            if end < text_len:
                split_at = text.rfind("\n", start, end)
                if split_at > start + (MAX_CHUNK_SIZE // 2):
                    end = split_at

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunk_meta = metadata.copy()
                chunk_meta["chunk_heading"] = f"Đoạn {idx}"
                chunk_meta["clause_id"] = f"Doan_{idx}"  # ✅ Thêm clause_id cho fallback
                chunks.append({"content": chunk_content, "metadata": chunk_meta})
                idx += 1

            if end >= text_len:
                break
            start = max(end - CHUNK_OVERLAP, start + 1)

        return chunks

    def _extract_heading_matches(self, text: str) -> List[re.Match]:
        legal_matches = list(self.legal_regex.finditer(text))
        if legal_matches:
            return legal_matches

        mixed_matches = (
            list(self.structure_regex.finditer(text))
            + list(self.def_regex.finditer(text))
            + list(self.generic_heading_regex.finditer(text))
        )

        mixed_matches.sort(key=lambda m: m.start())
        deduped: List[re.Match] = []
        seen_positions = set()

        for match in mixed_matches:
            pos = match.start()
            if pos in seen_positions:
                continue
            seen_positions.add(pos)
            deduped.append(match)

        return deduped

    def _split_by_matches(
        self, text: str, metadata: Dict[str, Any], matches: List[re.Match]
    ) -> List[Dict[str, Any]]:
        def append_with_size_guard(
            target: List[Dict[str, Any]],
            chunk_content: str,
            chunk_meta: Dict[str, Any],
            base_heading: str,
        ) -> None:
            if len(chunk_content) <= MAX_CHUNK_SIZE:
                target.append({"content": chunk_content, "metadata": chunk_meta})
                return

            start = 0
            part_idx = 1
            total_len = len(chunk_content)

            while start < total_len:
                end = min(total_len, start + MAX_CHUNK_SIZE)
                if end < total_len:
                    split_at = chunk_content.rfind("\n", start, end)
                    if split_at <= start + (MAX_CHUNK_SIZE // 2):
                        split_at = chunk_content.rfind(". ", start, end)
                        if split_at > start + (MAX_CHUNK_SIZE // 2):
                            split_at += 1
                    if split_at > start + (MAX_CHUNK_SIZE // 2):
                        end = split_at

                part = chunk_content[start:end].strip()
                if part:
                    part_meta = chunk_meta.copy()
                    if part_idx > 1:
                        part_meta["chunk_heading"] = f"{base_heading} (phần {part_idx})"
                    target.append({"content": part, "metadata": part_meta})
                    part_idx += 1

                if end >= total_len:
                    break
                start = max(end - CHUNK_OVERLAP, start + 1)

        chunks = []

        first_start = matches[0].start()
        if first_start > 0:
            preface = text[:first_start].strip()
            if preface:
                preface_meta = metadata.copy()
                preface_meta["chunk_heading"] = "Mở đầu"
                preface_meta["clause_id"] = self._normalize_clause_id("Mở đầu")  # ✅ Thêm clause_id
                append_with_size_guard(chunks, preface, preface_meta, "Mở đầu")

        for i, match in enumerate(matches):
            start_index = match.start()
            heading = (match.groupdict().get("heading") or match.group(0)).strip()
            end_index = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            chunk_content = text[start_index:end_index].strip()
            if not chunk_content:
                continue

            body = chunk_content.removeprefix(heading).strip()
            if not body and i + 1 < len(matches):
                continue

            chunk_meta = metadata.copy()
            chunk_meta["chunk_heading"] = heading
            # ✅ Thêm clause_id dạng "Dieu X"
            chunk_meta["clause_id"] = self._normalize_clause_id(heading)
            append_with_size_guard(chunks, chunk_content, chunk_meta, heading)

        return chunks

    def semantic_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:

        matches = self._extract_heading_matches(text)

        if not matches:
            return self._fallback_chunk_by_length(text, metadata)

        chunks = self._split_by_matches(text, metadata, matches)
        if chunks:
            return chunks

        return self._fallback_chunk_by_length(text, metadata)

    def process_file(self, file_path: str, version: str) -> List[Dict[str, Any]]:

        path_obj = Path(file_path)
        doc_name = path_obj.name
        
        if path_obj.suffix.lower() == '.docx':
            text = self.read_docx(file_path)
        else:
            print(f"Not a docx file {path_obj.suffix}. please insert a .docx")
            return []
            
        clean_txt = self.clean_text(text)
        
        base_metadata = {
            "document_id": doc_name,
            "version": version
        }
        
        chunks = self.semantic_chunking(clean_txt, base_metadata)
        
        return chunks

if __name__ == "__main__":
    print("Document Processor Ready.")

