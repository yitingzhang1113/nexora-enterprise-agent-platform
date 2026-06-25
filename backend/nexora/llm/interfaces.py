"""LLM 接口 (对应 onyx/llm/interfaces.py)。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


class LLM(ABC):
    @abstractmethod
    def stream(self, messages: list[dict[str, Any]], system: str | None = None) -> Iterator[str]:
        """流式生成纯文本。"""

    @abstractmethod
    def complete(self, messages: list[dict[str, Any]], system: str | None = None) -> str:
        """一次性返回文本。"""

    @abstractmethod
    def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str | None = None,
    ) -> dict[str, Any]:
        """带工具调用的一轮。返回 {content, tool_calls:[{id,name,arguments}]}。"""
