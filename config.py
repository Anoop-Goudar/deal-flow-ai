from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("DEALFLOW_LLM_PROVIDER", "mock")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    embedding_provider: str = os.getenv("DEALFLOW_EMBEDDING_PROVIDER", "openai")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimensions: int = int(os.getenv("DEALFLOW_EMBEDDING_DIMENSIONS", "256"))
    allowed_origins: str = os.getenv(
        "DEALFLOW_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )


settings = Settings()
