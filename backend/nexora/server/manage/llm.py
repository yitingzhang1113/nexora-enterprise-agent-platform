"""LLM 配置查看 (对应 onyx/server/manage/llm)。

学习版只读: 展示当前 LiteLLM 模型与可用 provider。Onyx 在此可增删 provider/key。
"""
from __future__ import annotations

from fastapi import APIRouter

from nexora.configs.app_configs import settings

router = APIRouter(prefix="/manage", tags=["llm"])


@router.get("/llm/current")
def current_llm() -> dict:
    provider = settings.llm_model.split("/", 1)[0] if "/" in settings.llm_model else "unknown"
    return {
        "model": settings.llm_model,
        "provider": provider,
        "embed_model": settings.embed_model,
        "embed_dim": settings.embed_dim,
    }
