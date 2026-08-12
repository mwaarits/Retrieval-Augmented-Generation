from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    docs = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": path.name, "page": page_num},
                )
            )
    if not docs:
        raise ValueError(f"No extractable text found in {path.name}")
    return docs


def load_text(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [Document(page_content=text, metadata={"source": path.name})]


SUPPORTED_EXTS = {
    ".pdf": load_pdf,
    ".txt": load_text,
    ".md": load_text,
}


def load_file(path: Path) -> list[Document]:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported file type {ext!r} for {path.name}")
    return SUPPORTED_EXTS[ext](path)


def load_directory(dir_path: Path) -> list[Document]:
    if not dir_path.exists():
        raise FileNotFoundError(f"Data directory not found: {dir_path}")
    files = [p for p in sorted(dir_path.iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    if not files:
        raise ValueError(f"No supported documents found in {dir_path}")
    docs: list[Document] = []
    for file in files:
        docs.extend(load_file(file))
    return docs