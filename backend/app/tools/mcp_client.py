"""MCP 客户端: 统一工具调用 (同步 + 异步)。

默认走内置工具 (registry); 配 MCP_SERVER_URL 则按 MCP 风格 (JSON-RPC tools/call) 调远端。
异步 call_async 用 asyncio.to_thread 把同步 DB 工具并行化 (供 parallel_tool_calls)。
"""
from __future__ import annotations

import asyncio

import httpx

from app.config import settings
from app.tools import registry


def list_tools() -> list[dict]:
    return registry.list_schemas()


def call(name: str, args: dict) -> dict:
    if settings.mcp_server_url:
        return _call_remote(name, args)
    return registry.run_local(name, args)


async def call_async(name: str, args: dict) -> dict:
    return await asyncio.to_thread(call, name, args)


def _call_remote(name: str, args: dict) -> dict:
    url = settings.mcp_server_url.rstrip("/")
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args or {}}}
    try:
        r = httpx.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json().get("result", {})
    except Exception as exc:  # noqa: BLE001
        return {"error": f"MCP 调用失败 ({name}): {exc}"}
