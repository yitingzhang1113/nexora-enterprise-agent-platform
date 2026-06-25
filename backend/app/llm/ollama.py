"""Ollama provider —— 本地生成 (默认)。

使用 Ollama 的 /api/chat 接口。tool calling 依赖模型支持
(llama3.1 / qwen2.5 等支持 function calling)。
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

from app.config import settings


class OllamaProvider:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.gen_model

    def _build_messages(
        self, messages: list[dict[str, Any]], system: str | None
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if system:
            out.append({"role": "system", "content": system})
        out.extend(messages)
        return out

    def stream_chat(
        self, messages: list[dict[str, Any]], system: str | None = None
    ) -> Iterator[str]:
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "stream": True,
        }
        with httpx.stream(
            "POST", f"{self.base_url}/api/chat", json=payload, timeout=None
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break

    def chat(self, messages: list[dict[str, Any]], system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "stream": False,
        }
        resp = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=None)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "tools": tools,
            "stream": False,
        }
        resp = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=None)
        resp.raise_for_status()
        msg = resp.json().get("message", {})
        tool_calls = []
        for tc in msg.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append({"name": fn.get("name"), "arguments": args})
        return {"content": msg.get("content", ""), "tool_calls": tool_calls}
