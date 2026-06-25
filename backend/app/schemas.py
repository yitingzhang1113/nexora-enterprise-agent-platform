"""Pydantic 请求/响应模型 (API 层 DTO)。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ---------- Documents ----------
class DocumentOut(BaseModel):
    id: int
    title: str
    source: str
    link: str | None = None
    num_chunks: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Search ----------
class SearchRequest(BaseModel):
    query: str
    top_k: int | None = None


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    score: float
    vector_rank: int | None = None
    keyword_rank: int | None = None


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


# ---------- Personas ----------
class PersonaCreate(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str
    tools: list[str] = []


class PersonaOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_prompt: str
    tools: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    persona_id: int | None = None
    use_agent: bool = False


class Citation(BaseModel):
    n: int
    chunk_id: int
    document_id: int
    document_title: str
    content: str


# ---------- Connectors / Index ----------
class IndexAttemptOut(BaseModel):
    id: int
    connector_id: int
    status: str
    num_docs: int
    num_chunks: int
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebIndexRequest(BaseModel):
    url: str
    name: str | None = None
