"""检索接口 (直接测混合检索)。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas import SearchHit, SearchRequest, SearchResponse
from app.search.hybrid import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(req: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    hits = hybrid_search(db, req.query, top_k=req.top_k)
    out = []
    for h in hits:
        doc = h.chunk.document
        out.append(
            SearchHit(
                chunk_id=h.chunk.id,
                document_id=h.chunk.document_id,
                document_title=doc.title if doc else "",
                chunk_index=h.chunk.chunk_index,
                content=h.chunk.content,
                score=round(h.score, 6),
                vector_rank=h.vector_rank,
                keyword_rank=h.keyword_rank,
            )
        )
    return SearchResponse(query=req.query, hits=out)
