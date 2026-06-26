"""LangGraph 规划/路由 单测 (纯逻辑)。"""
from app.graph.nodes import plan_tasks
from app.graph.router import route_by_intent


def test_plan_anomaly_has_all_tools():
    state = {"intent": "anomaly_detection", "question": "分析 NX-AIR-FRYER-001",
             "rewritten_query": "分析 NX-AIR-FRYER-001", "sku": "NX-AIR-FRYER-001"}
    plan = plan_tasks(state)["plan"]
    tools = {p["tool"] for p in plan}
    assert {"query_sales_data", "query_returns", "query_inventory",
            "query_support_tickets", "retrieve_policy"} <= tools


def test_plan_refund():
    state = {"intent": "refund_decision", "question": "订单 10086 退款 $300",
             "order_id": 10086, "amount": 300.0}
    plan = plan_tasks(state)["plan"]
    tools = [p["tool"] for p in plan]
    assert "evaluate_refund" in tools and "retrieve_policy" in tools


def test_route_clarify():
    assert route_by_intent({"intent": "clarification"}) == "clarify"
    assert route_by_intent({"intent": "anomaly_detection"}) == "parallel_tool_calls"
