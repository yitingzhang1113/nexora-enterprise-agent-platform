"""Anthropic (Claude) provider —— 占位实现。

默认走 Ollama；把 LLM_PROVIDER=anthropic 并填 ANTHROPIC_API_KEY 即可切换到 Claude。
这演示了「provider 抽象」如何让换厂商只是改配置 + 一个适配类。
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.config import settings

# 默认模型 id (参考 Anthropic 最新 Claude 系列)
DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider:
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic 但未设置 ANTHROPIC_API_KEY"
            )
        # 延迟导入，避免未用到时强依赖
        from anthropic import Anthropic

        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = DEFAULT_MODEL

    def stream_chat(
        self, messages: list[dict[str, Any]], system: str | None = None
    ) -> Iterator[str]:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=2048,
            system=system or "",
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def chat(self, messages: list[dict[str, Any]], system: str | None = None) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system or "",
            messages=messages,
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str | None = None,
    ) -> dict[str, Any]:
        # 把 Ollama 风格的 tool schema 转成 Anthropic 风格
        anthropic_tools = [
            {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "input_schema": t["function"].get("parameters", {}),
            }
            for t in tools
        ]
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system or "",
            messages=messages,
            tools=anthropic_tools,
        )
        content = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({"name": block.name, "arguments": block.input})
        return {"content": content, "tool_calls": tool_calls}
