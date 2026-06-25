"""Agent 可用的工具：schema (给模型看) + executor (实际执行)。

工具调用是 agentic RAG 的核心：模型不再被动接收检索结果，
而是自己决定何时调用 search_docs、调用几次、用什么 query。
"""
from __future__ import annotations

import ast
import operator
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.chat.rag import format_context, retrieve

# ---- 工具 schema (OpenAI / Ollama function-calling 格式) ----
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "在知识库中检索与查询最相关的资料片段，用于回答需要依据文档的问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询词"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，例如剂量换算 (如 '500*3/1000')。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "纯数学表达式"}
                },
                "required": ["expression"],
            },
        },
    },
]

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("不支持的表达式")


def _calculator(expression: str, **_: Any) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_safe_eval(tree))
    except Exception as exc:  # noqa: BLE001
        return f"计算错误: {exc}"


def make_tool_registry(db: Session) -> dict[str, Callable[..., str]]:
    """返回 工具名 -> executor。executor 返回给模型的字符串结果。

    search_docs 还会把命中的 citations 写入 collected_citations，
    供最终答案引用 (闭包共享列表)。
    """

    def _search_docs(query: str, _collected: list, **_: Any) -> str:
        hits = retrieve(db, query)
        context, citations = format_context(hits)
        # 记录引用 (跨多次调用累加，编号在 loop 里统一)
        _collected.extend(citations)
        return context or "未检索到相关资料。"

    return {
        "search_docs": _search_docs,
        "calculator": lambda **kw: _calculator(**kw),
    }
