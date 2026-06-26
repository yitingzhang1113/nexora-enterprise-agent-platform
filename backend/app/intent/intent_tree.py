"""意图规则树 (LLM 分类的兜底 / 加速)。

四类意图: knowledge_qa | tool_call | chitchat | clarification
"""
from __future__ import annotations

INTENTS = ["knowledge_qa", "tool_call", "chitchat", "clarification"]

# 命中关键词 → 倾向工具调用 (与 tools/registry 对应)
TOOL_KEYWORDS = [
    "天气", "weather", "气温", "下雨",
    "工单", "ticket", "报修", "故障单",
    "销售", "sales", "业绩", "订单金额", "营收",
]

CHITCHAT_KEYWORDS = ["你好", "hi", "hello", "在吗", "谢谢", "再见", "你是谁"]


def rule_intent(query: str) -> str | None:
    q = query.strip().lower()
    if not q:
        return "clarification"
    if any(k.lower() in q for k in TOOL_KEYWORDS):
        return "tool_call"
    if any(k.lower() in q for k in CHITCHAT_KEYWORDS) and len(q) <= 12:
        return "chitchat"
    # 过短且无信息量 → 需澄清
    if len(q) <= 3:
        return "clarification"
    return None
