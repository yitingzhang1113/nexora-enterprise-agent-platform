"""嵌入 (复用 rag.embedder, 走 model_server)。"""
from __future__ import annotations

from app.rag.embedder import embed_texts

__all__ = ["embed_texts"]
