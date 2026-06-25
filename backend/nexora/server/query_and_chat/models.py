"""chat API 的 DTO。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    persona_id: int | None = None
    use_agent: bool = False


class ChatSessionOut(BaseModel):
    id: int
    persona_id: int | None = None
    title: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    citations: list = []
    created_at: datetime

    class Config:
        from_attributes = True
