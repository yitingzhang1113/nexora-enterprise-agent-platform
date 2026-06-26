"""意图分类: 规则树为主, LLM 兜底 (知识/闲聊/澄清)。"""
from __future__ import annotations

from app.intent.intent_tree import rule_intent

_LLM_LABELS = ["knowledge_qa", "chitchat", "clarification"]

_PROMPT = """把用户问题归入且仅归入以下三类之一, 只输出英文单词:
- knowledge_qa: 询问政策/规则/概念, 需查知识库
- chitchat: 寒暄闲聊
- clarification: 问题过于模糊, 需澄清

用户问题: {q}
类别:"""


def classify_intent(query: str, history: list[dict] | None = None) -> str:
    r = rule_intent(query)
    if r is not None:
        return r
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
