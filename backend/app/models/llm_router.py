"""LLM Router: 按任务返回合适的 LangChain chat model。

- get_main_llm(): 生成主力 (流式回答)
- get_fast_llm(): 改写 / 意图 / 重排等轻任务 (便宜档)
配合 circuit_breaker 记录失败, health_check 探活 (admin 展示)。
"""
from __future__ import annotations

from app.config import settings
from app.models.circuit_breaker import llm_breaker
from app.models.providers import build_chat_model


def get_main_llm(streaming: bool = False):
    return build_chat_model(settings.llm_model_main, streaming=streaming)


def get_fast_llm():
    return build_chat_model(settings.llm_model_fast)


def record_success() -> None:
    llm_breaker.record_success()


def record_failure() -> None:
    llm_breaker.record_failure()


def router_status() -> dict:
    return {
        "provider": settings.llm_provider,
        "main_model": settings.llm_model_main,
        "fast_model": settings.llm_model_fast,
        "breaker": llm_breaker.state(),
    }
