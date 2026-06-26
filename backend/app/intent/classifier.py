"""意图分类: 规则树判 tool_call, LLM 在 知识/闲聊/澄清 三类里选。

为什么 tool_call 只靠规则: 内置业务工具 (天气/工单/销售) 是关键词可精确识别的,
而小模型容易把普通知识问题误判为 tool_call。把工具路由交给规则, 其余交给 LLM,
在 3B 本地模型下更稳健。
"""
from __future__ import annotations

from app.intent.intent_tree import rule_intent

_LLM_LABELS = ["knowledge_qa", "chitchat", "clarification"]

_PROMPT = """把用户问题归入且仅归入以下三类之一, 只输出类别英文单词:
- knowledge_qa: 需要查企业知识库回答的问题 (制度/产品/概念等)
- chitchat: 寒暄闲聊, 无需检索
- clarification: 问题过于模糊, 需要先向用户澄清

示例:
"年假有多少天" -> knowledge_qa
"你好" -> chitchat
"那个怎么弄" -> clarification

用户问题: {q}
类别:"""


def classify_intent(query: str, history: list[dict] | None = None) -> str:
    # 1) 规则: 命中工具关键词 → tool_call; 过短 → clarification
    r = rule_intent(query)
    if r == "tool_call":
        return "tool_call"
    if r == "clarification":
        return "clarification"
    if r == "chitchat":
        return "chitchat"
    # 2) LLM 在三类里选 (不含 tool_call)
    try:
        from app.models.llm_router import get_fast_llm

        resp = get_fast_llm().invoke(_PROMPT.format(q=query))
        text = (getattr(resp, "content", "") or "").strip().lower()
        for label in _LLM_LABELS:
            if label in text:
                return label
    except Exception:  # noqa: BLE001
        pass
    return "knowledge_qa"
