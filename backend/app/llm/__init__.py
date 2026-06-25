"""LLM provider 抽象层。

通过 `get_llm()` 工厂返回具体实现，调用方不关心是 Ollama 还是 Anthropic。
这正是 Onyx 多 provider 支持的核心思想：把「生成」与「具体厂商」解耦。
"""
from app.config import settings
from app.llm.base import LLMProvider


def get_llm() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        from app.llm.anthropic import AnthropicProvider

        return AnthropicProvider()
    # 默认本地 Ollama
    from app.llm.ollama import OllamaProvider

    return OllamaProvider()
