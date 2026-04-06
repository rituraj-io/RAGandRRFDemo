"""
Configuration — loads settings from .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"


    # Storage paths
    chroma_path: str = "data/chroma"
    sqlite_bm25_path: str = "data/bm25.db"
    sqlite_chat_path: str = "data/chat.db"


    # Chat (optional)
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    @property
    def chat_enabled(self) -> bool:
        return bool(self.llm_api_key)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
