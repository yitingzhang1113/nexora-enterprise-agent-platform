"""意图规则树 (电商运营)。

意图: knowledge_qa(政策问答) | data_analysis | anomaly_detection | refund_decision
      | chitchat | clarification
工具路由主要靠规则 (关键词), 小模型只兜底 knowledge_qa/chitchat/clarification。
"""
from __future__ import annotations

import re

REFUND_KW = ["退款", "refund", "退钱", "能不能退", "可以退"]
ANOMALY_KW = ["异常", "风险", "anomaly", "表现异常", "有没有问题", "诊断"]
DATA_KW = ["退货率", "销量", "库存", "工单", "sales", "returns", "inventory", "stock", "断货", "缺货"]
CHITCHAT_KW = ["你好", "hi", "hello", "在吗", "谢谢", "再见", "你是谁"]


def rule_intent(query: str) -> str | None:
    q = query.strip().lower()
    if not q:
        return "clarification"
    # 问候优先于「过短→澄清」判断 (如「你好」只有 2 字)
    if any(k.lower() in q for k in CHITCHAT_KW) and len(q) <= 12:
        return "chitchat"
    if len(q) <= 3:
        return "clarification"
    if any(k.lower() in q for k in REFUND_KW):
        return "refund_decision"
    if any(k.lower() in q for k in ANOMALY_KW):
        return "anomaly_detection"
    if any(k.lower() in q for k in DATA_KW):
        return "data_analysis"
    return None


SKU_RE = re.compile(r"\bNX-[A-Z0-9-]+\b", re.I)
ORDER_RE = re.compile(r"(?:订单|order)\s*#?\s*(\d+)", re.I)
MONEY_RE = re.compile(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:美元|刀|usd|\$)?", re.I)


def extract_sku(query: str) -> str | None:
    m = SKU_RE.search(query)
    return m.group(0).upper() if m else None


def extract_order_id(query: str) -> int | None:
    m = ORDER_RE.search(query)
    return int(m.group(1)) if m else None


def extract_amount(query: str) -> float | None:
    # 优先带货币符号的数字
    m = re.search(r"\$\s*(\d+(?:\.\d+)?)", query) or re.search(r"(\d+(?:\.\d+)?)\s*(?:美元|刀|usd)", query, re.I)
    return float(m.group(1)) if m else None
