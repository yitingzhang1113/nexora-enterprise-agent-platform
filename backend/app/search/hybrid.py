"""混合检索 = 向量召回 + 关键词召回 → RRF 融合。

RRF (Reciprocal Rank Fusion): score = Σ 1/(k + rank_i)。
它只看「排名」不看「分数量纲」，因此能把余弦距离与 ts_rank 这两种
不可比的分数公平地合并。Onyx 用 Vespa 内置的混合排序；我们手写 RRF 复现原理。
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk
from app.search.keyword import keyword_search
from app.search.vector import vector_search

RRF_K = 60  # RRF 常数，经验值


@dataclass
class FusedHit:
    chunk: Chunk
    score: float
    vector_rank: int | None
    keyword_rank: int | None


def hybrid_search(db: Session, query: str, top_k: int | None = None) -> list[FusedHit]:
    top_k = top_k or settings.top_k
    pool = max(top_k * 4, 20)

    vec_results = vector_search(db, query, limit=pool)
    kw_results = keyword_search(db, query, limit=pool)

    vec_rank = {chunk.id: i + 1 for i, (chunk, _) in enumerate(vec_results)}
    kw_rank = {chunk.id: i + 1 for i, (chunk, _) in enumerate(kw_results)}

    chunks_by_id: dict[int, Chunk] = {}
    for chunk, _ in vec_results:
        chunks_by_id[chunk.id] = chunk
    for chunk, _ in kw_results:
        chunks_by_id[chunk.id] = chunk

    fused: list[FusedHit] = []
    for cid, chunk in chunks_by_id.items():
        score = 0.0
        vr = vec_rank.get(cid)
        kr = kw_rank.get(cid)
        if vr:
            score += 1.0 / (RRF_K + vr)
        if kr:
            score += 1.0 / (RRF_K + kr)
        fused.append(FusedHit(chunk=chunk, score=score, vector_rank=vr, keyword_rank=kr))

    fused.sort(key=lambda h: h.score, reverse=True)
    return fused[:top_k]
