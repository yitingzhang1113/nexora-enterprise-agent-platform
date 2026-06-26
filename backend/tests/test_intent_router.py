"""意图规则树 + 实体抽取 单测 (纯逻辑, 无需服务)。"""
from app.intent.intent_tree import (
    extract_amount,
    extract_order_id,
    extract_sku,
    rule_intent,
)


def test_refund_intent():
    assert rule_intent("订单 10086 能不能退款") == "refund_decision"


def test_anomaly_intent():
    assert rule_intent("分析最近7天表现异常的商品") == "anomaly_detection"


def test_data_intent():
    assert rule_intent("哪个 SKU 退货率最高") == "data_analysis"


def test_chitchat_intent():
    assert rule_intent("你好") == "chitchat"


def test_clarification_intent():
    assert rule_intent("?") == "clarification"


def test_knowledge_fallthrough():
    # 政策类问题规则不直接命中 → None (交给 LLM 兜底 knowledge_qa)
    assert rule_intent("公司的促销折扣上限是多少") is None


def test_extractors():
    assert extract_sku("看看 NX-AIR-FRYER-001 的数据") == "NX-AIR-FRYER-001"
    assert extract_order_id("订单 10086 退款") == 10086
    assert extract_amount("退款 $300 美元") == 300.0
