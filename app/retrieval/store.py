from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever

from app.config import get_settings


_doc_store: Chroma | None = None


def get_vector_store(embeddings: Embeddings | None = None) -> Chroma:
    # Singleton manual: @lru_cache tidak bisa dipakai karena Embeddings unhashable
    global _doc_store
    if _doc_store is None:
        settings = get_settings()
        if embeddings is None:
            from app.ingestion.embedder import get_document_embeddings

            embeddings = get_document_embeddings(settings.embedding_model, settings.google_api_key)
        _doc_store = Chroma(
            collection_name=settings.collection_name,
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
        )
    return _doc_store


@lru_cache
def get_query_store() -> Chroma:
    settings = get_settings()
    from app.ingestion.embedder import get_query_embeddings

    query_embeddings = get_query_embeddings(settings.embedding_model, settings.google_api_key)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=query_embeddings,
        persist_directory=str(settings.chroma_dir),
    )


def make_hybrid_retriever(vector_retriever: BaseRetriever, docs: list[Document], k: int) -> BaseRetriever:
    """Gabungkan BM25 (keyword) + vector (semantik) via RRF. Corpus kosong -> vector only."""
    if not docs:
        return vector_retriever

    from langchain_classic.retrievers import EnsembleRetriever
    from langchain_community.retrievers import BM25Retriever

    bm25 = BM25Retriever.from_documents(docs, preprocess_func=lambda s: s.lower().split())
    bm25.k = k
    return EnsembleRetriever(retrievers=[bm25, vector_retriever], weights=[0.5, 0.5])


def get_retriever(
    k: int | None = None,
    search_type: str = "similarity",
    user_id: str | None = None,
    **kwargs: Any,
) -> BaseRetriever:
    settings = get_settings()
    search_kwargs = {"k": k or settings.top_k}
    search_kwargs.update(kwargs)
    if user_id:
        search_kwargs["filter"] = {"user_id": user_id}
    store = get_query_store()
    vector_retriever = store.as_retriever(search_type=search_type, search_kwargs=search_kwargs)

    # Corpus BM25 difilter per user (hindari mencampur dokumen antar akun)
    if user_id:
        rows = store.get(where={"user_id": user_id})
    else:
        rows = store.get()
    docs = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(rows.get("documents") or [], rows.get("metadatas") or [])
    ]
    return make_hybrid_retriever(vector_retriever, docs, k or settings.top_k)


def list_user_documents(user_id: str) -> list[str]:
    """Daftar nama sumber (source) milik user, urut alfabetis."""
    store = get_query_store()
    rows = store.get(where={"user_id": user_id}, include=["metadatas"])
    sources = {m.get("source") for m in (rows.get("metadatas") or []) if isinstance(m, dict)}
    return sorted(s for s in sources if s)
