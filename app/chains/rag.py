from collections.abc import Iterable

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.chains.prompts import RAG_PROMPT
from app.config import get_settings


def get_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
    )


def format_docs(docs: Iterable[Document]) -> str:
    return "\n\n".join(f"[{d.metadata.get('source', 'unknown')}]: {d.page_content}" for d in docs)


def answer_question(question: str, retriever, history: list[BaseMessage] | None = None) -> str:
    settings = get_settings()
    llm = get_llm()
    docs = retriever.invoke(question)
    context = format_docs(docs)
    messages = RAG_PROMPT.format_messages(
        context=context,
        history=history or [],
        question=question,
    )
    response = llm.invoke(messages)
    return response.content
