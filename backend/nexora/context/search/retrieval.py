"""检索服务: 嵌入 query + 混合检索 (对应 onyx 的 search pipeline 精简版)。"""
from __future__ import annotations

from nexora.configs.app_configs import settings
from nexora.document_index.factory import get_default_document_index
from nexora.document_index.models import InferenceChunk
from nexora.indexing.embedder import embed_query


def retrieve(query: str, top_k: int | None = None) -> list[InferenceChunk]:
    top_k = top_k or settings.top_k
    index = get_default_document_index()
    qvec = embed_query(query)
    return index.hybrid_retrieval(query, qvec, top_k)
