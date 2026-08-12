from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )


def split_documents(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    return get_splitter(chunk_size, chunk_overlap).split_documents(docs)
