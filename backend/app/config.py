"""集中配置 (pydantic-settings)。

对应 Onyx 的 `backend/onyx/configs/*` —— 所有可调项都从环境变量 / .env 读取，
方便在 docker-compose 与 Kubernetes (ConfigMap/Secret) 两种环境注入。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- DB ---
    database_url: str = "postgresql+psycopg://nexora:nexora@localhost:5432/nexora"

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    gen_model: str = "llama3.1"
    embed_model: str = "bge-m3"
    embed_dim: int = 1024

    # --- LLM provider 抽象 ---
    llm_provider: str = "ollama"  # ollama | anthropic
    anthropic_api_key: str = ""

    # --- Retrieval ---
    top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # --- App ---
    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
