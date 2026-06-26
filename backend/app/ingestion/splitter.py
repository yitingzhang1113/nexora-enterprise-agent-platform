"""切分: 复用 rag.chunker 的算法。"""
from __future__ import annotations

from app.rag.chunker import chunk_text


def split(text: str) -> list[str]:
    return chunk_text(text)
