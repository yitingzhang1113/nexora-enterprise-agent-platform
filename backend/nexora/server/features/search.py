"""检索路由 (对应 onyx/server/features/search)。直接测混合检索。"""
from __future__ import annotations

from fastapi import APIRouter

from nexora.context.search.models import SearchRequest, SearchResponse
from nexora.context.search.retrieval import retrieve

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    chunks = retrieve(req.query, top_k=req.top_k)
    return SearchResponse(query=req.query, chunks=chunks)
