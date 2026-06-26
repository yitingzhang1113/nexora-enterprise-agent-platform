"""本地工具注册表 (MCP 风格 schema + executor)。"""
from __future__ import annotations

from typing import Callable

from app.tools import sales_tool, ticket_tool, weather_tool

# name -> (schema, executor)
_TOOLS: dict[str, tuple[dict, Callable[..., str]]] = {
    weather_tool.SCHEMA["name"]: (weather_tool.SCHEMA, weather_tool.run),
    ticket_tool.SCHEMA["name"]: (ticket_tool.SCHEMA, ticket_tool.run),
    sales_tool.SCHEMA["name"]: (sales_tool.SCHEMA, sales_tool.run),
}


def list_schemas() -> list[dict]:
    return [s for s, _ in _TOOLS.values()]


def run_local(name: str, args: dict) -> str:
    entry = _TOOLS.get(name)
    if not entry:
        return f"未知工具: {name}"
    _, fn = entry
    return fn(**(args or {}))
