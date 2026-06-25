"""Agent 循环：模型 ↔ 工具 多轮，直到给出最终答案。

流程 (ReAct 简化版):
  1. 把工具 schema 给模型
  2. 模型要么直接答，要么请求调用工具
  3. 执行工具，把结果作为 tool 消息回灌
  4. 回到 2，直至模型不再请求工具或达到上限
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.agent.tools import TOOL_SCHEMAS, make_tool_registry
from app.llm import get_llm

MAX_STEPS = 5


def run_agent(
    db: Session,
    query: str,
    system: str,
    history: list[dict] | None = None,
    allowed_tools: list[str] | None = None,
) -> dict:
    """返回 {"content": str, "citations": list, "steps": list[str]}。"""
    llm = get_llm()
    registry = make_tool_registry(db)
    collected_citations: list[dict] = []

    # 过滤 persona 允许的工具
    if allowed_tools is not None:
        tools = [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed_tools]
    else:
        tools = TOOL_SCHEMAS

    messages: list[dict] = [*(history or []), {"role": "user", "content": query}]
    trace: list[str] = []

    for _ in range(MAX_STEPS):
        result = llm.chat_with_tools(messages, tools=tools, system=system)
        tool_calls = result.get("tool_calls") or []
        if not tool_calls:
            # 模型给出最终答案
            citations = _renumber(collected_citations)
            return {
                "content": result.get("content", ""),
                "citations": citations,
                "steps": trace,
            }

        # 记录 assistant 的工具请求
        messages.append(
            {
                "role": "assistant",
                "content": result.get("content", ""),
                "tool_calls": [
                    {"function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in tool_calls
                ],
            }
        )
        # 逐个执行工具
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("arguments", {}) or {}
            trace.append(f"调用工具 {name}({json.dumps(args, ensure_ascii=False)})")
            fn = registry.get(name)
            if fn is None:
                output = f"未知工具: {name}"
            elif name == "search_docs":
                output = fn(_collected=collected_citations, **args)
            else:
                output = fn(**args)
            messages.append({"role": "tool", "name": name, "content": str(output)})

    # 达到步数上限：再让模型基于已有信息收尾
    final = llm.chat(messages, system=system)
    return {
        "content": final,
        "citations": _renumber(collected_citations),
        "steps": trace,
    }


def _renumber(citations: list[dict]) -> list[dict]:
    """跨多次 search_docs 调用去重 + 重新编号。"""
    seen: dict[int, dict] = {}
    for c in citations:
        seen.setdefault(c["chunk_id"], c)
    out = []
    for i, c in enumerate(seen.values(), start=1):
        out.append({**c, "n": i})
    return out
