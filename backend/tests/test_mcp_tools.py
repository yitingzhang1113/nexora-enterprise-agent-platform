"""MCP 工具集成测试 (需 Postgres + 已 seed 数据, 缺则跳过)。"""
import pytest

ANOMALY = "NX-AIR-FRYER-001"


def _db_ok() -> bool:
    try:
        from app.db.engine import SessionLocal
        from app.db.models import Product

        db = SessionLocal()
        try:
            return db.query(Product).count() > 0
        finally:
            db.close()
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(not _db_ok(), reason="DB 未就绪或未 seed")


def test_sales_drop():
    from app.tools.data_tools import query_sales_data

    r = query_sales_data(ANOMALY, days=7)
    assert r["last_window_units"] < r["prev_window_units"]  # 销量下降
    assert r["pct_change"] <= -20


def test_inventory_below_safety():
    from app.tools.data_tools import query_inventory

    r = query_inventory(ANOMALY)
    assert r["found"] and r["below_safety"]


def test_returns_high():
    from app.tools.data_tools import query_returns

    r = query_returns(ANOMALY, days=30)
    assert r["return_rate_pct"] >= 10


def test_evaluate_refund_needs_approval():
    from app.tools.refund_tools import evaluate_refund

    r = evaluate_refund(order_id=10086, amount=300, reason="defective")
    assert r["needs_approval"] is True


def test_create_ops_ticket_and_slack():
    from app.tools.action_tools import create_ops_ticket, send_slack_message

    t = create_ops_ticket(title="test", sku=ANOMALY, severity="high", body="x")
    assert t["ticket_id"] > 0
    s = send_slack_message(channel="#ops-alerts", text="test")
    assert s["ok"] is True
