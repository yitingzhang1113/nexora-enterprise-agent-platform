"""LangGraph 状态定义。"""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: int | None
    persona_system: str
    persona_tools: list[str]

    question: str
    history: list[dict[str, str]]
    summary: str | None
    rewritten_query: str
    intent: str

    retrieved: list[Any]
    reranked: list[Any]
    citations: list[dict]
    context: str

    tool_results: list[dict]

    gen_messages: list[tuple[str, str]]
    clarification: str | None
    answer: str
