from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.api import auth as auth_api
from app.chains.memory import get_session_history
from app.chains.rag import answer_question
from app.core import auth as auth_core
from app.core.security import InputSanitizer, OutputValidator
from app.ingestion.embedder import get_document_embeddings
from app.ingestion.loaders import load_file
from app.ingestion.splitters import split_documents
from app.retrieval.store import get_vector_store, list_user_documents

app = FastAPI(title="RAG App", version="0.1.0")
app.include_router(auth_api.router)

sanitizer = InputSanitizer()
validator = OutputValidator()

_bearer = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = auth_core.get_user(creds.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

ALLOWED_UPLOAD_EXTS = {".pdf", ".txt", ".md"}


def sanitize_upload_name(filename: str | None) -> str:
    name = Path((filename or "").replace("\\", "/")).name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="File name is required")
    return name


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str = "default"


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    sanitized: bool = False
    warning: str | None = None


class IngestResponse(BaseModel):
    documents: int
    chunks: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
) -> IngestResponse:
    from app.config import get_settings

    settings = get_settings()
    filename = sanitize_upload_name(file.filename)
    suffix = Path(filename).suffix
    if suffix.lower() not in ALLOWED_UPLOAD_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.max_upload_mb} MB)")

    tmp_path = settings.data_dir / f"_upload_{filename}"
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    tmp_path.write_bytes(data)

    try:
        docs = load_file(tmp_path)
        for doc in docs:
            doc.metadata["source"] = filename  # nama asli, tanpa prefix _upload_
            doc.metadata["user_id"] = user_id
        chunks = split_documents(docs, settings.chunk_size, settings.chunk_overlap)
        embeddings = get_document_embeddings(settings.embedding_model, settings.google_api_key)
        store = get_vector_store(embeddings=embeddings)
        ids = [f"{chunk.metadata.get('source', 'doc')}-{i}" for i, chunk in enumerate(chunks)]
        store.add_documents(chunks, ids=ids)
        return IngestResponse(documents=len(docs), chunks=len(chunks))
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, user_id: str = Depends(get_current_user)) -> QueryResponse:
    suspicious, reason = sanitizer.is_suspicious(req.question)
    if suspicious:
        return QueryResponse(answer="Blocked: suspicious input detected.", sources=[], sanitized=True, warning=reason)

    question = sanitizer.sanitize(req.question)
    history = get_session_history(user_id)  # session_id dipaksa = user_id (anti spoofing)

    from app.retrieval.store import get_retriever

    retriever = get_retriever(user_id=user_id)
    docs = retriever.invoke(question)
    if not docs:
        # Retrieve kosong -> jawab pasti tanpa panggil LLM
        return QueryResponse(answer="I don't have knowledge to answer this question.", sources=[], sanitized=question != req.question)

    from langchain_core.messages import AIMessage, HumanMessage

    try:
        answer = answer_question(question, retriever, history.messages)
    except Exception as e:
        history.add_message(HumanMessage(content=req.question))
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}") from e

    is_valid, cleaned, reason = validator.validate(answer)
    sources = [d.metadata.get("source", "unknown") for d in retriever.invoke(question)]

    history.add_message(HumanMessage(content=req.question))
    history.add_message(AIMessage(content=cleaned))

    return QueryResponse(
        answer=cleaned,
        sources=sources,
        sanitized=question != req.question,
        warning=reason,
    )


@app.get("/documents")
def documents(user_id: str = Depends(get_current_user)) -> dict:
    return {"documents": list_user_documents(user_id)}


# Frontend static — HARUS setelah semua route API agar /health, /ingest, /query tetap menang
app.mount("/", StaticFiles(directory="static", html=True), name="static")
