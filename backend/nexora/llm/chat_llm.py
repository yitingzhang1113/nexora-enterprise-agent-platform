"""LiteLLM 实现 (对应 onyx/llm/chat_llm.py / multi_llm.py)。

LiteLLM 用统一接口对接 100+ provider。模型由 LLM_MODEL 决定:
  ollama/qwen2.5:3b | anthropic/claude-sonnet-4-6 | openai/gpt-4o ...
换 provider 只改配置, 无需改业务代码 —— 这正是 Onyx 的多 provider 思路。
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import litellm

from nexora.configs.app_configs import settings
from nexora.llm.interfaces import LLM

# 安静一点
litellm.drop_params = True
litellm.suppress_debug_info = True


class LiteLLMChat(LLM):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.llm_model

    def _kwargs(self) -> dict[str, Any]:
        kw: dict[str, Any] = {}
        if self.model.startswith("ollama/"):
            kw["api_base"] = settings.ollama_base_url
        if self.model.startswith("anthropic/") and settings.anthropic_api_key:
            kw["api_key"] = settings.anthropic_api_key
        if self.model.startswith("openai/") and settings.openai_api_key:
            kw["api_key"] = settings.openai_api_key
        return kw

    @staticmethod
    def _with_system(messages: list[dict], system: str | None) -> list[dict]:
        if system:
            return [{"role": "system", "content": system}, *messages]
        return messages

    def stream(self, messages: list[dict[str, Any]], system: str | None = None) -> Iterator[str]:
        resp = litellm.completion(
            model=self.model,
            messages=self._with_system(messages, system),
            stream=True,
            **self._kwargs(),
        )
        for chunk in resp:
            delta = chunk["choices"][0]["delta"]
            token = delta.get("content") or ""
            if token:
                yield token

    def complete(self, messages: list[dict[str, Any]], system: str | None = None) -> str:
        resp = litellm.completion(
            model=self.model,
            messages=self._with_system(messages, system),
            **self._kwargs(),
        )
        return resp["choices"][0]["message"].get("content") or ""

    def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str | None = None,
    ) -> dict[str, Any]:
        resp = litellm.completion(
            model=self.model,
            messages=self._with_system(messages, system),
            tools=tools,
            **self._kwargs(),
        )
        msg = resp["choices"][0]["message"]
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc["function"]
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({"id": tc.get("id", ""), "name": fn["name"], "arguments": args})
        return {"content": msg.get("content") or "", "tool_calls": tool_calls}
