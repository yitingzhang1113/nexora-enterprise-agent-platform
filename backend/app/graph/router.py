"""路由: 根据 intent 决定下一个节点 (LangGraph 条件边)。"""
from __future__ import annotations


def route_by_intent(state: dict) -> str:
    intent = state.get("intent", "knowledge_qa")
    if intent == "tool_call":
        return "call_tools"
    if intent == "clarification":
        return "clarify"
    if intent == "chitchat":
        return "build_prompt"
    return "retrieve_docs"  # knowledge_qa
