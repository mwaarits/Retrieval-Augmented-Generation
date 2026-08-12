from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str = ""
    auth_users: str = "[]"
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"

    data_dir: Path = BASE_DIR / "data"
    chroma_dir: Path = BASE_DIR / "chroma_db"
    collection_name: str = "knowledge_base"

    chunk_size: int = 1000
    chunk_overlap: int = 300
    top_k: int = 4
    max_upload_mb: int = 25

    @property
    def llm_temperature(self) -> float:
        return 0.5


@lru_cache
def get_settings() -> Settings:
    return Settings()
