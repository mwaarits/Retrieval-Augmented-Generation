import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.core import auth as auth_core


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_users(monkeypatch):
    monkeypatch.setattr(auth_core, "load_users", lambda: {"alice": "pw", "bob": "pw"})


def _login(client, username="alice", password="pw"):
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_login_success(client, auth_users):
    r = client.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["user_id"] == "alice"


def test_login_wrong_password(client, auth_users):
    r = client.post("/auth/login", json={"username": "alice", "password": "salah"})
    assert r.status_code == 401


def test_login_unknown_user(client, auth_users):
    r = client.post("/auth/login", json={"username": "nobody", "password": "pw"})
    assert r.status_code == 401


def test_ingest_requires_token(client):
    r = client.post("/ingest", files={"file": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 401


def test_documents_requires_token(client):
    r = client.get("/documents")
    assert r.status_code == 401


def test_ingest_sets_user_id(monkeypatch, tmp_path, client, auth_users):
    import app.api.main as api_main
    from langchain_core.documents import Document

    from app.config import Settings

    class RecStore:
        captured = None

        def add_documents(self, docs, ids=None):
            RecStore.captured = docs

    settings = Settings(data_dir=tmp_path, max_upload_mb=25)
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr(api_main, "load_file", lambda path: [Document(page_content="x", metadata={})])
    monkeypatch.setattr(api_main, "split_documents", lambda docs, chunk_size, chunk_overlap: docs)
    monkeypatch.setattr(api_main, "get_document_embeddings", lambda m, k: None)
    monkeypatch.setattr(api_main, "get_vector_store", lambda embeddings=None: RecStore())

    r = client.post("/ingest", files={"file": ("a.txt", b"x", "text/plain")}, headers=_login(client))
    assert r.status_code == 200
    assert RecStore.captured[0].metadata["user_id"] == "alice"


def test_list_user_documents_filters(monkeypatch):
    import app.retrieval.store as store_module

    class FakeStore:
        def get(self, where=None, include=None):
            if where == {"user_id": "alice"}:
                return {"metadatas": [{"source": "a.txt", "user_id": "alice"}, {"source": "b.txt", "user_id": "alice"}]}
            if where == {"user_id": "bob"}:
                return {"metadatas": [{"source": "c.txt", "user_id": "bob"}]}
            return {"metadatas": []}

    monkeypatch.setattr(store_module, "get_query_store", lambda: FakeStore())
    assert store_module.list_user_documents("alice") == ["a.txt", "b.txt"]
    assert store_module.list_user_documents("bob") == ["c.txt"]


def test_get_retriever_filters_by_user(monkeypatch):
    import app.retrieval.store as store_module

    captured = {}

    class FakeStore:
        def as_retriever(self, search_type, search_kwargs):
            captured["search_kwargs"] = search_kwargs
            return object()

        def get(self, where=None):
            captured["where"] = where
            return {"documents": [], "metadatas": []}

    monkeypatch.setattr(store_module, "get_query_store", lambda: FakeStore())
    store_module.get_retriever(user_id="alice")
    assert captured["search_kwargs"]["filter"] == {"user_id": "alice"}
    assert captured["where"] == {"user_id": "alice"}  # corpus BM25 ikut difilter