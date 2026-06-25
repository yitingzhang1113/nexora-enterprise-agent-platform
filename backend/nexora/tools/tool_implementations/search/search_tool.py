"""SearchTool —— RAG 核心 (对应 onyx/tools/tool_implementations/search/search_tool.py)。

在 Onyx 中, 普通问答与 Agent 都通过 SearchTool 从向量库取数。
本工具调用混合检索, 返回拼好的 context 文本 + 命中 chunk (供引用)。
"""
from __future__ import annotations

from typing import Any

from nexora.context.search.retrieval import retrieve
from nexora.document_index.models import InferenceChunk
from nexora.tools.tool import Tool, ToolResult


def format_context(chunks: list[InferenceChunk]) -> str:
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (来源: {c.document_title})\n{c.content}")
    return "\n\n".join(blocks)


class SearchTool(Tool):
    name = "search_docs"

    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "在知识库中检索与查询最相关的资料片段, 用于回答需要依据文档的问题。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "检索查询词"}
                    },
                    "required": ["query"],
                },
            },
        }

    def run(self, query: str = "", **_: Any) -> ToolResult:
        chunks = retrieve(query)
        return ToolResult(
            llm_content=format_context(chunks) or "未检索到相关资料。",
            chunks=chunks,
        )
