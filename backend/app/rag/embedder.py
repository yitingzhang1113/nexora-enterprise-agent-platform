"""嵌入 (调用独立 model_server)。query 嵌入带 Redis 缓存 (重复查询免重复嵌入)。"""
from __future__ import annotations

import httpx

from app import cache
from app.config import settings

_MS = settings.model_server_url.rstrip("/")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = httpx.post(f"{_MS}/api/encode", json={"texts": texts}, timeout=300)
    resp.raise_for_status()
    return resp.json()["embeddings"]


def embed_query(text: str) -> list[float]:
    # 嵌入是检索热路径里最贵的一步 (本地 Ollama bge-m3 ~数秒)。
    # 缓存命中时跳过整次嵌入调用, 大幅降低重复/相似查询延迟。
    return cache.cached("embed_query", text, lambda: embed_texts([text])[0], ttl=600)
