"""工具注册与执行 (对应 onyx/tools/tool_runner.py)。"""
from __future__ import annotations

from nexora.tools.tool import Tool, ToolResult
from nexora.tools.tool_implementations.calculator.calculator_tool import CalculatorTool
from nexora.tools.tool_implementations.search.search_tool import SearchTool

# 内置工具注册表
_BUILTIN: dict[str, Tool] = {
    SearchTool.name: SearchTool(),
    CalculatorTool.name: CalculatorTool(),
}


def get_tools(allowed: list[str] | None = None) -> list[Tool]:
    if allowed is None:
        return list(_BUILTIN.values())
    return [_BUILTIN[name] for name in allowed if name in _BUILTIN]


def run_tool(name: str, arguments: dict) -> ToolResult:
    tool = _BUILTIN.get(name)
    if tool is None:
        return ToolResult(llm_content=f"未知工具: {name}")
    return tool.run(**(arguments or {}))
