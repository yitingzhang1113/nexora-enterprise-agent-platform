"""聊天流式 Packet 模型 (对应 onyx 的 packet 流, 精简)。

后端把回答拆成一串 packet 推给前端:
- tool:      触发了某工具 (Agent 模式时间线)
- citations: 本次回答引用的来源 chunk
- token:     回答文本片段 (流式)
- done:      结束
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class Packet(BaseModel):
    type: Literal["meta", "tool", "citations", "token", "done"]
    data: Any = None


def citation_from_chunk(n: int, chunk) -> dict:
    """把 InferenceChunk 转成前端引用结构。"""
    return {
        "n": n,
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "content": chunk.content,
        "link": chunk.link,
    }
