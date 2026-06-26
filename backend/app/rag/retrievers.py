"""检索器: Milvus dense + BM25(jieba) 关键词。

dense: 向量近邻 (Milvus)。bm25: 对 Postgres 中所有 chunk 文本用 jieba 分词后 BM25 打分
(中文友好, 修复纯 Postgres simple 分词不切中文的问题)。
"""
from __future__ import annotations

from dataclasses import dataclass

import jieba
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import milvus
from app.db.models import Chunk
from app.rag.embedder import embed_query


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    doc_title: str
    chunk_index: int
    content: str
    link: str | None = None
    score: float = 0.0
    dense_rank: int | None = None
    bm25_rank: int | None = None


def _load_chunks(db: Session, ids: list[int]) -> dict[int, Chunk]:
    if not ids:
        return {}
    rows = db.execute(select(Chunk).where(Chunk.id.in_(ids))).scalars()
    return {c.id: c for c in rows}


def dense_retrieve(db: Session, query: str, pool: int | None = None) -> list[RetrievedChunk]:
    pool = pool or settings.retrieve_pool
    qvec = embed_query(query)
    hits = milvus.search(qvec, pool)
    chunk_map = _load_chunks(db, [h["id"] for h in hits])
    out = []
    for rank, h in enumerate(hits, start=1):
        c = chunk_map.get(h["id"])
        if not c:
            continue
        out.append(
            RetrievedChunk(
                chunk_id=c.id,
                document_id=c.document_id,
                doc_title=c.doc_title,
                chunk_index=c.chunk_index,
                content=c.content,
                link=c.link,
                dense_rank=rank,
            )
        )
    return out


def _tok(text: str) -> list[str]:
    return [t for t in jieba.lcut(text.lower()) if t.strip()]


def bm25_retrieve(db: Session, query: str, pool: int | None = None) -> list[RetrievedChunk]:
    pool = pool or settings.retrieve_pool
    chunks = list(db.execute(select(Chunk)).scalars())
    if not chunks:
        return []
    corpus = [_tok(c.content) for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tok(query))
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    out = []
    for rank, (c, score) in enumerate(ranked[:pool], start=1):
        if score <= 0:
            break
        out.append(
            RetrievedChunk(
                chunk_id=c.id,
                document_id=c.document_id,
                doc_title=c.doc_title,
                chunk_index=c.chunk_index,
                content=c.content,
                link=c.link,
                bm25_rank=rank,
            )
        )
    return out
