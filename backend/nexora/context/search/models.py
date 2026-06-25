"""检索请求/结果模型 (对应 onyx/context/search/models.py)。"""
from __future__ import annotations

from pydantic import BaseModel

from nexora.document_index.models import InferenceChunk


class SearchRequest(BaseModel):
    query: str
    top_k: int | None = None


class SearchResponse(BaseModel):
    query: str
    chunks: list[InferenceChunk]
