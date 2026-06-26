"""LangChain chat model 工厂 (多 provider)。"""
from __future__ import annotations

from typing import Any

from app.config import settings


def build_chat_model(model: str, provider: str | None = None, **kwargs: Any):
    provider = (provider or settings.llm_provider).lower()
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key, **kwargs)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=settings.openai_api_key, **kwargs)
    # 默认 Ollama
    from langchain_ollama import ChatOllama

    return ChatOllama(model=model, base_url=settings.ollama_base_url, **kwargs)
