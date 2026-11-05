from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Glitch RAG"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:1.5b"
    llm_api_key: SecretStr
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    embedding_model: str = "bge-m3"
    embedding_batch_size: int = Field(default=32, gt=0)
    index_dir: Path = Path("data/index")


@lru_cache
def get_settings() -> Settings:
    return Settings()
