"""Tool Registry API: 列出 MCP 工具 schema + 调用计数。"""
from __future__ import annotations

from fastapi import APIRouter

from app.observability import metrics
from app.tools.registry import ACTION_TOOLS, list_schemas

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
def list_tools() -> list[dict]:
    snap = metrics.snapshot()
    out = []
    for s in list_schemas():
        name = s["name"]
        out.append({
            "name": name,
            "description": s["description"],
            "parameters": s["parameters"],
            "is_action": name in ACTION_TOOLS,
            "call_count": snap.get(f"tool.{name}", 0),
        })
    return out
