from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.retrieval.store import make_hybrid_retriever


class FakeVectorRetriever(BaseRetriever):
    docs: list[Document]

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        return self.docs


def test_hybrid_falls_back_to_vector_when_corpus_empty():
    vector = FakeVectorRetriever(docs=[Document(page_content="apapun")])
    assert make_hybrid_retriever(vector, [], k=4) is vector


def test_hybrid_surfaces_keyword_match():
    # Vector "gagal" menemukan keyword persis (di dunia nyata: embedding tidak mirip)
    vector = FakeVectorRetriever(docs=[Document(page_content="cuaca hari ini cerah")])
    corpus = [
        Document(page_content="laporan keuangan nomor INV-2024-001 lunas", metadata={"source": "laporan.txt"}),
        Document(page_content="resep rendang padang asli", metadata={"source": "resep.txt"}),
    ]
    hybrid = make_hybrid_retriever(vector, corpus, k=2)
    results = hybrid.invoke("INV-2024-001")
    assert any("INV-2024-001" in d.page_content for d in results)
