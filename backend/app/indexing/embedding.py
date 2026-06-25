"""文本嵌入 (Ollama embeddings)。

对应 Onyx 独立的 model server —— 这里直接调用 Ollama 的 /api/embeddings。
嵌入维度由 EMBED_DIM 决定，必须与 pgvector 列维度一致。
"""
from __future__ import annotations

import httpx

from app.config import settings

_BASE = settings.ollama_base_url.rstrip("/")


def embed_text(text: str) -> list[float]:
    """对单段文本生成嵌入向量。"""
    resp = httpx.post(
        f"{_BASE}/api/embeddings",
        json={"model": settings.embed_model, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    vec = resp.json().get("embedding")
    if not vec:
        raise RuntimeError(f"Ollama 未返回 embedding (model={settings.embed_model})")
    return vec


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量嵌入。Ollama 原生无批接口，这里逐条调用 (MVP 足够)。"""
    return [embed_text(t) for t in texts]
