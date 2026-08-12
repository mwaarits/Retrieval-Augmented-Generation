import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

import app.api.main as api_main
from app.api.main import app, get_current_user
from app.config import Settings


@pytest.fixture(autouse=True)
def _auth_as_alice():
    app.dependency_overrides[get_current_user] = lambda: "alice"
    yield
    app.dependency_overrides.pop(get_current_user, None)


class FakeStore:
    def add_documents(self, docs, ids=None):
        pass


def _patch_pipeline(monkeypatch, tmp_path, max_upload_mb=25):
    settings = Settings(data_dir=tmp_path, max_upload_mb=max_upload_mb)
    monkeypatch.setattr("app.config.get_settings", lambda: settings)
    monkeypatch.setattr(api_main, "load_file", lambda path: [Document(page_content="c", metadata={"source": path.name})])
    monkeypatch.setattr(api_main, "split_documents", lambda docs, chunk_size, chunk_overlap: docs)
    monkeypatch.setattr(api_main, "get_document_embeddings", lambda model, api_key: None)
    monkeypatch.setattr(api_main, "get_vector_store", lambda embeddings: FakeStore())


def test_ingest_rejects_unsupported_extension(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, tmp_path)
    client = TestClient(app)
    resp = client.post("/ingest", files={"file": ("doc.exe", b"MZ", "application/octet-stream")})
    assert resp.status_code == 400


def test_ingest_rejects_oversized_file(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, tmp_path, max_upload_mb=1)
    client = TestClient(app)
    resp = client.post("/ingest", files={"file": ("big.txt", b"x" * (1024 * 1024 + 1), "text/plain")})
    assert resp.status_code == 413


def test_sanitize_upload_name_rejects_empty():
    import pytest
    from fastapi import HTTPException

    from app.api.main import sanitize_upload_name

    with pytest.raises(HTTPException):
        sanitize_upload_name(None)
    with pytest.raises(HTTPException):
        sanitize_upload_name("..")


def test_ingest_sanitizes_traversal_filename(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, tmp_path)
    client = TestClient(app)
    resp = client.post("/ingest", files={"file": ("../../evil.pdf", b"x", "application/pdf")})
    assert resp.status_code == 200
    assert not (tmp_path.parent / "evil.pdf").exists()
    assert list(tmp_path.glob("*")) == []


def test_ingest_sanitizes_fakepath_filename(monkeypatch, tmp_path):
    _patch_pipeline(monkeypatch, tmp_path)
    client = TestClient(app)
    resp = client.post("/ingest", files={"file": ("C:\\fakepath\\report.txt", b"x", "text/plain")})
    assert resp.status_code == 200
