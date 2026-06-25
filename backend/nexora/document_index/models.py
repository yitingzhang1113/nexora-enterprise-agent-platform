"""向量库中的 chunk 数据模型 (对应 onyx/document_index/*models)。

三个阶段的 chunk:
- DocAwareChunk: 切块后、嵌入前 (带文档元信息)
- IndexChunk:    带 embedding, 准备写入向量库
- InferenceChunk: 检索回来的结果 (带分数/排名/引用信息)
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class DocAwareChunk(BaseModel):
    document_id: int
    chunk_index: int
    title: str
    content: str
    source: str
    link: str | None = None


class IndexChunk(DocAwareChunk):
    embedding: list[float]

    def to_os_doc(self, index_dim: int) -> dict:
        """转成 OpenSearch 文档体。"""
        return {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "link": self.link or "",
            "embedding": self.embedding,
        }


class InferenceChunk(BaseModel):
    chunk_id: str
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    link: str | None = None
    score: float = 0.0
    vector_rank: int | None = None
    keyword_rank: int | None = None
