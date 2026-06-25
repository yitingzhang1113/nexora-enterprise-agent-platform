"""LLM provider 接口定义。"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol


class LLMProvider(Protocol):
    """所有 provider 必须实现的最小接口。"""

    def stream_chat(
        self, messages: list[dict[str, Any]], system: str | None = None
    ) -> Iterator[str]:
        """流式生成，逐 token/片段 yield 文本。"""
        ...

    def chat(self, messages: list[dict[str, Any]], system: str | None = None) -> str:
        """一次性返回完整文本。"""
        ...

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str | None = None,
    ) -> dict[str, Any]:
        """带工具调用的一轮对话。

        返回 {"content": str, "tool_calls": [{"name": str, "arguments": dict}, ...]}
        若模型未请求工具，tool_calls 为空。
        """
        ...
