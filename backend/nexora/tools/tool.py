"""Tool 抽象 (对应 onyx/tools/tool.py)。

每个工具暴露:
- name: 工具名
- definition(): 给 LLM 的 function-calling schema
- run(**kwargs): 执行, 返回 ToolResult
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from nexora.document_index.models import InferenceChunk


@dataclass
class ToolResult:
    # 给 LLM 看的文本结果
    llm_content: str
    # 附带的引用 chunk (search 工具会填充)
    chunks: list[InferenceChunk] = field(default_factory=list)


class Tool(ABC):
    name: str

    @abstractmethod
    def definition(self) -> dict[str, Any]:
        """function-calling schema (OpenAI/LiteLLM 格式)。"""

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        ...
