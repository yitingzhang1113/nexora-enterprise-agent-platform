"""搜索/向量库设置查看 (对应 onyx/server/manage/search_settings)。"""
from __future__ import annotations

from fastapi import APIRouter

from nexora.configs.app_configs import settings
from nexora.document_index.factory import get_default_document_index

router = APIRouter(prefix="/manage", tags=["search_settings"])


@router.get("/search-settings")
def search_settings() -> dict:
    index = get_default_document_index()
    try:
        chunk_count = index.count()
    except Exception:  # noqa: BLE001
        chunk_count = -1
    return {
        "backend": "opensearch",
        "index_name": settings.opensearch_index,
        "embed_model": settings.embed_model,
        "embed_dim": settings.embed_dim,
        "chunk_count": chunk_count,
        "top_k": settings.top_k,
    }
