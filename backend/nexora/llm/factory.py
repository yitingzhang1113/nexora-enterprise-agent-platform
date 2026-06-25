"""LLM 工厂 (对应 onyx/llm/factory.py)。"""
from __future__ import annotations

from nexora.llm.chat_llm import LiteLLMChat
from nexora.llm.interfaces import LLM


def get_default_llm() -> LLM:
    return LiteLLMChat()
