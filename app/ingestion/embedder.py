from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings


@lru_cache
def get_document_embeddings(model: str, api_key: str) -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(model=model, api_key=api_key, task_type="retrieval_document")


@lru_cache
def get_query_embeddings(model: str, api_key: str) -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(model=model, api_key=api_key, task_type="retrieval_query")
