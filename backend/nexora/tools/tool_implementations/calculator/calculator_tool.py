"""CalculatorTool —— 安全的数学表达式计算 (医药剂量换算等)。"""
from __future__ import annotations

import ast
import operator
from typing import Any

from nexora.tools.tool import Tool, ToolResult

_OPS = {
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
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("不支持的表达式")


class CalculatorTool(Tool):
    name = "calculator"

    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": "计算数学表达式, 例如剂量换算 (如 '500*3/1000')。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "纯数学表达式"}
                    },
                    "required": ["expression"],
                },
            },
        }

    def run(self, expression: str = "", **_: Any) -> ToolResult:
        try:
            result = str(_safe_eval(ast.parse(expression, mode="eval")))
        except Exception as exc:  # noqa: BLE001
            result = f"计算错误: {exc}"
        return ToolResult(llm_content=result)
