"""Multi-Retriever: dense + bm25 → RRF 融合 + 去重。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.rag.retrievers import RetrievedChunk, bm25_retrieve, dense_retrieve

RRF_K = 60


def multi_retrieve(db: Session, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    top_k = top_k or settings.top_k
    dense = dense_retrieve(db, query)
    bm25 = bm25_retrieve(db, query)

    merged: dict[int, RetrievedChunk] = {}
    for c in dense + bm25:
        if c.chunk_id not in merged:
            merged[c.chunk_id] = c
        else:
            ex = merged[c.chunk_id]
            ex.dense_rank = ex.dense_rank or c.dense_rank
            ex.bm25_rank = ex.bm25_rank or c.bm25_rank

    for c in merged.values():
        score = 0.0
        if c.dense_rank:
            score += 1.0 / (RRF_K + c.dense_rank)
        if c.bm25_rank:
            score += 1.0 / (RRF_K + c.bm25_rank)
        c.score = round(score, 6)

    ranked = sorted(merged.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]
