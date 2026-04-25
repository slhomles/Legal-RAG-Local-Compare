import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from legal_rag.ingest.chunker import LegalChunker
from legal_rag.ingest.loader import DocumentLoader


class DocumentProcessor:
    VERSION_SUFFIX_REGEX = re.compile(r"^(?P<doc_id>.+?)[_-](?P<version>v\d+)$", re.IGNORECASE)

    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = LegalChunker()

    def _infer_doc_identity(self, stem: str, version_override: Optional[str]) -> tuple[str, str]:
        match = self.VERSION_SUFFIX_REGEX.match(stem)
        if match:
            doc_id = match.group("doc_id")
            version = version_override or match.group("version").lower()
            return doc_id, version

        return stem, (version_override or "v1")

    def process_file(self, file_path: str, version_override: Optional[str] = None) -> List[Dict[str, Any]]:
        path_obj = Path(file_path)
        if path_obj.suffix.lower() != ".docx":
            print(f"Not a docx file {path_obj.suffix}. please insert a .docx")
            return []

        text = self.loader.read_docx(file_path)
        clean_text = self.loader.clean_text(text)
        doc_id, version = self._infer_doc_identity(path_obj.stem, version_override)
        base_metadata = {
            "doc_id": doc_id,
            "version": version,
        }
        return self.chunker.semantic_chunking(clean_text, base_metadata)


if __name__ == "__main__":
    print("Document Processor Ready.")
