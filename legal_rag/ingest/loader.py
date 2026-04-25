import docx
#đọc file .docx -> text -> chuẩn hóa khoảng trắng, ký tự đặc biệt

class DocumentLoader:
    def read_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
            return "\n".join(full_text)
        except Exception as exc:
            print(f"Not a docx file {file_path}: {exc}")
            return ""

    def clean_text(self, text: str) -> str:
        import re

        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
