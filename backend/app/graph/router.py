"""路由: clarification 走澄清, 其余进工具执行链。"""
from __future__ import annotations


def route_by_intent(state: dict) -> str:
    if state.get("intent") == "clarification":
        return "clarify"
    return "parallel_tool_calls"
