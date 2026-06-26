"""Langfuse 客户端 (懒加载, 未配置则为 None)。"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import settings


@lru_cache
def get_langfuse() -> Any | None:
    if not settings.langfuse_enabled:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:  # noqa: BLE001
        return None
