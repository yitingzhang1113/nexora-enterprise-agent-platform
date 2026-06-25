"""Agentic 工具循环 (对应 onyx/chat/llm_loop.py)。

模型决定调用 search_docs / calculator, 执行后用工具结果作为 context 生成最终答案。

为什么不纯靠模型多轮 tool-message 自洽? 小模型 (qwen2.5:3b) 经 LiteLLM+Ollama 时
对 tool 结果回灌的理解不稳, 容易重复调用同一工具。这里采用更稳健的两阶段:
  1) 让模型选一轮工具 (可多个), 去重执行, 收集结果与引用;
  2) 把工具结果作为 context, 流式生成最终答案 (不再传 tools)。
仍保留工具调用时间线事件, 体现 agentic 行为。
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from nexora.document_index.models import InferenceChunk
from nexora.llm.factory import get_default_llm
from nexora.tools.tool import Tool
from nexora.tools.tool_runner import run_tool

MAX_TOOL_ROUNDS = 2


def run_agent_stream(
    message: str,
    system: str,
    tools: list[Tool],
    history: list[dict] | None = None,
) -> Iterator[dict[str, Any]]:
    llm = get_default_llm()
    tool_defs = [t.definition() for t in tools]
    messages: list[dict] = [*(history or []), {"role": "user", "content": message}]

    collected_chunks: list[InferenceChunk] = []
    tool_outputs: list[str] = []
    executed: set[str] = set()  # 去重 (name+args)

    for _ in range(MAX_TOOL_ROUNDS):
        if not tool_defs:
            break
        result = llm.complete_with_tools(messages, tool_defs, system=system)
        tool_calls = result.get("tool_calls") or []
        if not tool_calls:
            # 模型直接给答案且不需要工具
            if not tool_outputs and result.get("content"):
                yield {"type": "token", "text": result["content"]}
                return
            break

        new_calls = 0
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("arguments") or {}
            key = f"{name}:{json.dumps(args, sort_keys=True, ensure_ascii=False)}"
            if key in executed:
                continue
            executed.add(key)
            new_calls += 1
            yield {"type": "tool", "name": name, "arguments": args}
            tr = run_tool(name, args)
            collected_chunks.extend(tr.chunks)
            tool_outputs.append(f"[{name}] 结果:\n{tr.llm_content}")
        if new_calls == 0:
            break  # 全是重复调用, 停止

    # ---- 最终答案: 用工具结果作为 context 流式生成 ----
    if collected_chunks:
        yield {"type": "citations", "chunks": _dedup(collected_chunks)}

    if tool_outputs:
        context = "\n\n".join(tool_outputs)
        final_user = (
            f"【工具结果】\n{context}\n\n【问题】\n{message}\n\n"
            "请基于工具结果作答; 涉及资料时用 [n] 标注引用编号。"
        )
        final_messages = [*(history or []), {"role": "user", "content": final_user}]
    else:
        final_messages = messages

    for token in llm.stream(final_messages, system=system):
        yield {"type": "token", "text": token}


def _dedup(chunks: list[InferenceChunk]) -> list[InferenceChunk]:
    seen: dict[str, InferenceChunk] = {}
    for c in chunks:
        seen.setdefault(c.chunk_id, c)
    return list(seen.values())
