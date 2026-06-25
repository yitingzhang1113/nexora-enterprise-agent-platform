"""集中配置 (对应 Onyx 的 onyx/configs/*)。

所有可调项从环境变量 / .env 读取，便于 docker-compose 与 K8s (ConfigMap/Secret) 注入。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_api_prefix: str = "/api"  # 对齐 Onyx: 所有业务路由挂在 /api 下
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "./uploads"

    # --- Postgres (仅存元数据; chunk 不再入库) ---
    database_url: str = "postgresql+psycopg://nexora:nexora@localhost:5432/nexora"

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"

    # --- OpenSearch (向量 + 关键词混合检索, 替代 Onyx 的 Vespa) ---
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "nexora_chunks"

    # --- Model server (独立嵌入服务) ---
    model_server_url: str = "http://localhost:9000"
    embed_dim: int = 1024  # bge-m3

    # --- model_server 内部: 默认代理 Ollama 做嵌入 ---
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"

    # --- LLM (LiteLLM 模型串) ---
    # 例: ollama/qwen2.5:3b | anthropic/claude-sonnet-4-6 | openai/gpt-4o
    llm_model: str = "ollama/qwen2.5:3b"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # --- Retrieval ---
    top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 150

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
