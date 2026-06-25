"""DocumentIndex 抽象接口 (对应 onyx/document_index/interfaces_new.py)。

Onyx 通过这个接口屏蔽具体向量库 (Vespa / OpenSearch)。
我们提供 OpenSearch 实现。将来要换 Vespa/Qdrant, 只需新增一个实现 + 改 factory。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from nexora.document_index.models import IndexChunk, InferenceChunk


class DocumentIndex(ABC):
    @abstractmethod
    def ensure_setup(self) -> None:
        """确保索引 (mapping/schema) 已创建。"""

    @abstractmethod
    def index(self, chunks: list[IndexChunk]) -> int:
        """写入一批 chunk, 返回写入数量。"""

    @abstractmethod
    def delete_document(self, document_id: int) -> None:
        """删除某文档的所有 chunk。"""

    @abstractmethod
    def hybrid_retrieval(
        self, query: str, query_embedding: list[float], top_k: int
    ) -> list[InferenceChunk]:
        """向量 + 关键词混合检索, 返回融合排序后的 chunk。"""

    @abstractmethod
    def count(self) -> int:
        """chunk 总数 (调试用)。"""
