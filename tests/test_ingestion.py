from langchain_core.documents import Document

from app.ingestion.loaders import load_file
from app.ingestion.splitters import split_documents


def test_split_documents(tmp_path):
    text = "word " * 3000
    docs = [Document(page_content=text, metadata={"source": "test.txt"})]
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
    assert len(chunks) > 1
    assert all(len(c.page_content) <= 500 for c in chunks)


def test_load_file_txt(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello world")
    docs = load_file(f)
    assert len(docs) == 1
    assert "Hello world" in docs[0].page_content
    assert docs[0].metadata["source"] == "sample.txt"


def test_load_file_unsupported(tmp_path):
    f = tmp_path / "sample.docx"
    f.write_bytes(b"fake")
    import pytest

    with pytest.raises(ValueError):
        load_file(f)
