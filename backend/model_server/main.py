"""独立 model server (嵌入)。默认代理本地 Ollama 的 bge-m3。"""
from __future__ import annotations

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings

app = FastAPI(title="Nexora model_server (embeddings)")

_OLLAMA = settings.ollama_base_url.rstrip("/")


class EncodeRequest(BaseModel):
    texts: list[str]


class EncodeResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dim: int


def _embed_one(text: str) -> list[float]:
    resp = httpx.post(
        f"{_OLLAMA}/api/embeddings",
        json={"model": settings.embed_model, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    vec = resp.json().get("embedding")
    if not vec:
        raise RuntimeError(f"Ollama 未返回 embedding (model={settings.embed_model})")
    return vec


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/encode", response_model=EncodeResponse)
def encode(req: EncodeRequest) -> EncodeResponse:
    vecs = [_embed_one(t) for t in req.texts]
    dim = len(vecs[0]) if vecs else settings.embed_dim
    return EncodeResponse(embeddings=vecs, model=settings.embed_model, dim=dim)
