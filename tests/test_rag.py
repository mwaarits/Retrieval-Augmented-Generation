from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_chroma import Chroma

from app.chains.rag import format_docs


def test_format_docs_joins_with_sources():
    docs = [
        Document(page_content="Hello", metadata={"source": "a.txt"}),
        Document(page_content="World", metadata={"source": "b.txt"}),
    ]
    out = format_docs(docs)
    assert "[a.txt]: Hello" in out
    assert "[b.txt]: World" in out


def test_vector_store_roundtrip(tmp_path):
    embeddings = DeterministicFakeEmbedding(size=8)
    store = Chroma.from_documents(
        documents=[Document(page_content="Gemini is a Google model", metadata={"source": "t.txt"})],
        embedding=embeddings,
        persist_directory=str(tmp_path),
    )
    results = store.similarity_search("Gemini", k=1)
    assert len(results) == 1
    assert results[0].page_content == "Gemini is a Google model"
