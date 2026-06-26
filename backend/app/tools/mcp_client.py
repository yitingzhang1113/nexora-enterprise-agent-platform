"""MCP 客户端: 统一工具调用入口。

默认走内置 mock 工具 (registry); 若配置 MCP_SERVER_URL, 则以 MCP 风格
(JSON-RPC tools/call) 调用真实 MCP server。
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.tools import registry


def list_tools() -> list[dict]:
    # 真实 MCP server 也可在此拉取 tools/list; mock 直接返回本地 schema
    return registry.list_schemas()


def call(name: str, args: dict) -> str:
    if settings.mcp_server_url:
        return _call_remote(name, args)
    return registry.run_local(name, args)


def _call_remote(name: str, args: dict) -> str:
    url = settings.mcp_server_url.rstrip("/")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args or {}},
    }
    try:
        r = httpx.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        result = data.get("result", {})
        # MCP content 数组 → 文本
        if isinstance(result, dict) and "content" in result:
            parts = [c.get("text", "") for c in result["content"] if isinstance(c, dict)]
            return "\n".join(p for p in parts if p) or str(result)
        return str(result)
    except Exception as exc:  # noqa: BLE001
        return f"MCP 调用失败 ({name}): {exc}"
