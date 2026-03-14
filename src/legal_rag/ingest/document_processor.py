import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    
    @staticmethod
    def _extract_document_id_and_version(filename: str) -> tuple[str, str]:
        """
        Trích xuất document_id và version từ tên file.
        Ví dụ: "Hop_dong_A_v1.docx" → ("Hop_dong_A", "v1")
        """
        name_without_ext = Path(filename).stem
        match = re.search(r'_v(\d+)$', name_without_ext, re.IGNORECASE)
        
        if match:
            version = f"v{match.group(1)}"
            document_id = name_without_ext[:match.start()]
            return document_id, version
        
        return name_without_ext, "v1"
    
    @staticmethod
    def _normalize_clause_id(heading: str) -> str:
        """
        Chuẩn hóa clause_id từ heading.
        """
        if not heading:
            return "GENERAL"
        
        heading = heading.strip()
        
        # Pattern cho "Điều/Article X"
        match = re.search(r'(Điều|Article)\s+(\d+)', heading, re.IGNORECASE)
        if match:
            num = int(match.group(2))
            return f'CLAUSE_{num:03d}'
        
        # Pattern cho "Chương/Chapter X"
        match = re.search(r'(Chương|Chapter)\s+([IVXivx]+)', heading, re.IGNORECASE)
        if match:
            roman = match.group(2).upper()
            return f'CHAPTER_{roman}'
        
        # Pattern cho "Mục/Section X.Y.Z"
        match = re.search(r'(Mục|Section)\s+([\d.]+)', heading, re.IGNORECASE)
        if match:
            num_str = match.group(2).replace('.', '_')
            return f'SECTION_{num_str}'
        
        # Default
        return "CLAUSE_" + heading.upper().replace(" ", "_")[:50]
        
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
                chunk_meta["chunk_heading"] = f"Äoáº¡n {idx}"
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

    def process_file(self, file_path: str, version: Optional[str] = None) -> List[Dict[str, Any]]:

        path_obj = Path(file_path)
        doc_name = path_obj.name
        
        if path_obj.suffix.lower() == '.docx':
            text = self.read_docx(file_path)
        else:
            print(f"Not a docx file {path_obj.suffix}. please insert a .docx")
            return []
            
        clean_txt = self.clean_text(text)
        
        # Trích xuất document_id và version từ filename
        document_id, extracted_version = self._extract_document_id_and_version(doc_name)
        if version is None:
            version = extracted_version
        
        base_metadata = {
            "document_id": document_id,
            "version": version,
            "doc_id": doc_name
        }
        
        chunks = self.semantic_chunking(clean_txt, base_metadata)
        
        # Thêm clause_id cho mỗi chunk
        for chunk in chunks:
            heading = chunk["metadata"].get("chunk_heading", "")
            chunk["metadata"]["clause_id"] = self._normalize_clause_id(heading)
        
        return chunks

if __name__ == "__main__":
    print("Document Processor Ready.")

