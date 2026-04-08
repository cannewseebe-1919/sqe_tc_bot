import io

from docx import Document
from PyPDF2 import PdfReader


def parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n".join(texts)


def parse_file(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return parse_docx(file_bytes)
    elif lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Only .docx and .pdf are supported.")
