"""LangGraph 状态定义 (v4 Ops Agent)。"""
from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: int | None
    trace_id: str | None
    persona_system: str

    question: str
    history: list[dict[str, str]]
    summary: str | None
    rewritten_query: str
    intent: str

    # 实体抽取
    sku: str | None
    order_id: int | None
    amount: float | None

    # 规划与执行
    plan: list[dict]            # [{tool, args}] 只读工具
    tool_results: list[dict]    # [{tool, args, result}]
    citations: list[dict]
    risk: list[str]
    high_risk: bool
    auto_actions: list[dict]    # 立即执行的动作
    executed_actions: list[dict]
    pending_approvals: list[dict]
    parallel_ms: int

    clarification: str | None
    gen_messages: list[tuple[str, str]]
    answer: str
