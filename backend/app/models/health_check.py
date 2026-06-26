"""LLM/嵌入服务健康探活 (供 admin 展示)。"""
from __future__ import annotations

import httpx

from app.config import settings


def check_ollama() -> dict:
    try:
        r = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {"ok": True, "models": models}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def check_model_server() -> dict:
    try:
        r = httpx.get(f"{settings.model_server_url.rstrip('/')}/health", timeout=5)
        r.raise_for_status()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
