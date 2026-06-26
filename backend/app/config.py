"""集中配置 (pydantic-settings)。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "./uploads"
    rate_limit_per_min: int = 60

    # --- Postgres ---
    database_url: str = "postgresql+psycopg://nexora:nexora@localhost:5432/nexora"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Milvus (向量库) ---
    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "nexora_chunks"

    # --- Model server (嵌入) ---
    model_server_url: str = "http://localhost:9000"
    embed_dim: int = 1024
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"

    # --- LLM (LangChain). llm_router 按任务选模型 ---
    llm_provider: str = "ollama"  # ollama | anthropic | openai
    llm_model_main: str = "qwen2.5:3b"   # 生成主力
    llm_model_fast: str = "qwen2.5:3b"   # 改写/意图等轻任务
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # --- Retrieval / rerank ---
    top_k: int = 5
    retrieve_pool: int = 20
    chunk_size: int = 800
    chunk_overlap: int = 120
    rerank_mode: str = "llm"  # llm | none

    # --- MCP / tools ---
    mcp_server_url: str = ""  # 配了则走真实 MCP server, 否则用内置 mock

    # --- Langfuse ---
    langfuse_host: str = "http://localhost:3001"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
