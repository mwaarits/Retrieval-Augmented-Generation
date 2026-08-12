# Retrieval Augmented Generation

Local RAG Q&A app: upload documents (PDF/TXT/MD) → chunk → Gemini embeddings → Chroma vector store → question-answering with hybrid search (BM25 + vector) and multi-user auth.

## Prerequisites

- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- Google AI Studio API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))

## Setup

```bash
uv sync
cp .env.example .env
# then edit .env:
#   GOOGLE_API_KEY=<your key>
#   AUTH_USERS=[{"username":"alice","password":"secret123"}]
```

> Upgrading from a pre-auth version? Run `rm -rf chroma_db/` (old chunks without `user_id` will be invisible).

## Running

```bash
uv run uvicorn app.api.main:app --reload
```

Open `http://localhost:8000/` and log in with one of the `AUTH_USERS` accounts.

## How to use

1. **Upload documents** (left panel) — multi-file, uploaded sequentially with per-file status, max 25 MB per file (.pdf/.txt/.md).
2. **Ask questions** (right panel) — answers are grounded in your account's documents, with source chips.
3. If the answer is not in the documents, the app replies "I don't know" instead of guessing.
4. **Data is isolated per account** — different account, different files and chat history.

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | — | `{username,password}` → `{token,user_id}` |
| POST | `/auth/logout` | Bearer | Revoke token |
| GET | `/health` | — | Status |
| POST | `/ingest` | Bearer | Upload file (multipart) |
| POST | `/query` | Bearer | `{question}` → `{answer,sources,warning}` |
| GET | `/documents` | Bearer | List files owned by the account |

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | required |
| `AUTH_USERS` | `[]` | JSON accounts (plaintext passwords, local scale only) |
| `LLM_MODEL` | `gemini-2.5-flash` | chat model |
| `EMBEDDING_MODEL` | `models/gemini-embedding-001` | embedding model |
| `TOP_K` / `CHUNK_SIZE` / `CHUNK_OVERLAP` / `MAX_UPLOAD_MB` | 4 / 1000 / 200 / 25 | retrieval & chunking |
| `COLLECTION_NAME` / `CHROMA_DIR` / `DATA_DIR` | — | vector store paths |

## Test

```bash
uv run pytest   # 25 passed
```

## Flow

```
browser (login → token) → /ingest → sanitize name → chunk → embed → Chroma (+user_id)
                        → /query  → sanitize → hybrid retrieve (BM25+vector, filtered by user)
                                  → LLM → validator → answer + source chips
```

## Notes

- Token & chat history are in-memory — everyone re-logs in after a server restart (Chroma data persists).
- Plaintext passwords are for local scale only; make sure `.env` stays git-ignored.
- CLI ingest/query is disabled — everything goes through the web UI.