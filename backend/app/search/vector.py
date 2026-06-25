"""向量检索 (pgvector 余弦相似度)。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.indexing.embedding import embed_text
from app.models import Chunk


def vector_search(db: Session, query: str, limit: int = 20) -> list[tuple[Chunk, float]]:
    """返回 [(chunk, distance)]，distance 越小越相似 (余弦距离)。"""
    qvec = embed_text(query)
    distance = Chunk.embedding.cosine_distance(qvec).label("distance")
    rows = db.execute(
        select(Chunk, distance).order_by(distance).limit(limit)
    ).all()
    return [(row[0], float(row[1])) for row in rows]
