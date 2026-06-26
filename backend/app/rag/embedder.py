"""嵌入 (调用独立 model_server)。"""
from __future__ import annotations

import httpx

from app.config import settings

_MS = settings.model_server_url.rstrip("/")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = httpx.post(f"{_MS}/api/encode", json={"texts": texts}, timeout=300)
    resp.raise_for_status()
    return resp.json()["embeddings"]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
