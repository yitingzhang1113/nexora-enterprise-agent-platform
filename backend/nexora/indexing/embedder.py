"""嵌入 (调用独立 model_server, 对应 onyx/indexing/embedder.py)。

注意: 这里不直接调 Ollama, 而是走 model_server 的 /api/encode ——
保持与 Onyx 一致的「嵌入服务解耦」边界。
"""
from __future__ import annotations

import httpx

from nexora.configs.app_configs import settings

_MS = settings.model_server_url.rstrip("/")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = httpx.post(f"{_MS}/api/encode", json={"texts": texts}, timeout=300)
    resp.raise_for_status()
    return resp.json()["embeddings"]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
