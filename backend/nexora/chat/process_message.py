"""聊天编排入口 (对应 onyx/chat/process_message.py)。

统一产出 packet 流 (dict), 由 router 转成 SSE。两种模式:
- 普通 RAG: SearchTool 取数 → 拼 context → 流式生成
- Agent:    llm_loop 让模型自主调用工具
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from nexora.chat.llm_loop import run_agent_stream
from nexora.chat.models import citation_from_chunk
from nexora.llm.factory import get_default_llm
from nexora.tools.tool import Tool
from nexora.tools.tool_implementations.search.search_tool import SearchTool, format_context

DEFAULT_SYSTEM = (
    "你是一个严谨的知识助手。请只依据提供的【参考资料】回答用户问题, "
    "并在句末用 [n] 标注引用的资料编号。若资料中没有答案, 请明确说明你不知道, 不要编造。"
)


def stream_chat(
    message: str,
    system: str,
    use_agent: bool,
    tools: list[Tool],
    history: list[dict] | None = None,
) -> Iterator[dict[str, Any]]:
    if use_agent:
        yield from _agent_packets(message, system, tools, history)
    else:
        yield from _rag_packets(message, system, history)


def _rag_packets(
    message: str, system: str, history: list[dict] | None
) -> Iterator[dict[str, Any]]:
    search = SearchTool()
    result = search.run(query=message)
    chunks = result.chunks
    citations = [citation_from_chunk(i, c) for i, c in enumerate(chunks, start=1)]
    yield {"type": "citations", "data": citations}

    context = format_context(chunks)
    user_content = (
        f"【参考资料】\n{context}\n\n【问题】\n{message}\n\n"
        "请基于参考资料作答, 并标注引用编号 [n]。"
    )
    messages = [*(history or []), {"role": "user", "content": user_content}]
    for token in get_default_llm().stream(messages, system=system):
        yield {"type": "token", "data": token}


def _agent_packets(
    message: str, system: str, tools: list[Tool], history: list[dict] | None
) -> Iterator[dict[str, Any]]:
    for ev in run_agent_stream(message, system, tools, history):
        if ev["type"] == "tool":
            yield {"type": "tool", "data": {"name": ev["name"], "arguments": ev["arguments"]}}
        elif ev["type"] == "citations":
            citations = [
                citation_from_chunk(i, c) for i, c in enumerate(ev["chunks"], start=1)
            ]
            yield {"type": "citations", "data": citations}
        elif ev["type"] == "token":
            yield {"type": "token", "data": ev["text"]}
