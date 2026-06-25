"""关键词检索 (Postgres 全文检索 tsvector / ts_rank)。

对应传统 BM25。Chunk.tsv 是 generated 列 (见 models.py)，已建 GIN 索引。
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Chunk


def keyword_search(db: Session, query: str, limit: int = 20) -> list[tuple[Chunk, float]]:
    """返回 [(chunk, rank)]，rank 越大越相关。"""
    tsquery = func.plainto_tsquery("simple", query)
    rank = func.ts_rank(Chunk.tsv, tsquery).label("rank")
    rows = db.execute(
        select(Chunk, rank)
        .where(Chunk.tsv.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(limit)
    ).all()
    return [(row[0], float(row[1])) for row in rows]
