"""数据查询类 MCP 工具 (真实查 Postgres): 销量 / 库存 / 退货 / 工单。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.engine import SessionLocal
from app.db.models import Inventory, Order, OrderItem, Return, SupportTicket


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- query_sales_data ----------
SALES_SCHEMA = {
    "name": "query_sales_data",
    "description": "查询某 SKU 最近 N 天的销量, 并与上一周期对比 (用于发现销量异常)。",
    "parameters": {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "days": {"type": "integer", "description": "窗口天数, 默认 7"},
        },
        "required": ["sku"],
    },
}


def query_sales_data(sku: str = "", days: int = 7, **_) -> dict:
    db = SessionLocal()
    try:
        now = _now()
        lo_last, lo_prev = now - timedelta(days=days), now - timedelta(days=2 * days)

        def units(start, end):
            q = (
                select(func.coalesce(func.sum(OrderItem.qty), 0))
                .select_from(OrderItem)
                .join(Order, Order.id == OrderItem.order_id)
                .where(OrderItem.sku == sku, Order.created_at >= start, Order.created_at < end)
            )
            return int(db.execute(q).scalar() or 0)

        last = units(lo_last, now)
        prev = units(lo_prev, lo_last)
        pct = round((last - prev) / prev * 100, 1) if prev else 0.0
        return {
            "sku": sku, "window_days": days,
            "last_window_units": last, "prev_window_units": prev,
            "pct_change": pct,
        }
    finally:
        db.close()


# ---------- query_inventory ----------
INVENTORY_SCHEMA = {
    "name": "query_inventory",
    "description": "查询某 SKU 当前库存与安全库存, 判断是否低于安全线。",
    "parameters": {
        "type": "object",
        "properties": {"sku": {"type": "string"}},
        "required": ["sku"],
    },
}


def query_inventory(sku: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        inv = db.execute(select(Inventory).where(Inventory.sku == sku)).scalar_one_or_none()
        if not inv:
            return {"sku": sku, "found": False}
        return {
            "sku": sku, "found": True, "stock": inv.stock,
            "safety_stock": inv.safety_stock, "below_safety": inv.stock < inv.safety_stock,
        }
    finally:
        db.close()


# ---------- query_returns ----------
RETURNS_SCHEMA = {
    "name": "query_returns",
    "description": "查询某 SKU 最近 N 天的退货率与主要原因 (退货率 = 退货数 / 订单数)。",
    "parameters": {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "days": {"type": "integer", "description": "窗口天数, 默认 30"},
        },
        "required": ["sku"],
    },
}


def query_returns(sku: str = "", days: int = 30, **_) -> dict:
    db = SessionLocal()
    try:
        now = _now()
        start = now - timedelta(days=days)
        orders = int(
            db.execute(
                select(func.count(OrderItem.id))
                .join(Order, Order.id == OrderItem.order_id)
                .where(OrderItem.sku == sku, Order.created_at >= start)
            ).scalar() or 0
        )
        rets = int(
            db.execute(
                select(func.count(Return.id)).where(Return.sku == sku, Return.created_at >= start)
            ).scalar() or 0
        )
        top = db.execute(
            select(Return.reason, func.count(Return.id).label("c"))
            .where(Return.sku == sku, Return.created_at >= start)
            .group_by(Return.reason).order_by(func.count(Return.id).desc()).limit(1)
        ).first()
        rate = round(rets / orders * 100, 1) if orders else 0.0
        return {
            "sku": sku, "window_days": days, "orders": orders, "returns": rets,
            "return_rate_pct": rate, "top_reason": top[0] if top else None,
        }
    finally:
        db.close()


# ---------- query_support_tickets ----------
TICKETS_SCHEMA = {
    "name": "query_support_tickets",
    "description": "查询某 SKU 最近 N 天的客服工单数量与主要主题。",
    "parameters": {
        "type": "object",
        "properties": {
            "sku": {"type": "string"},
            "days": {"type": "integer", "description": "窗口天数, 默认 30"},
        },
        "required": ["sku"],
    },
}


def query_support_tickets(sku: str = "", days: int = 30, **_) -> dict:
    db = SessionLocal()
    try:
        now = _now()
        start = now - timedelta(days=days)
        cnt = int(
            db.execute(
                select(func.count(SupportTicket.id))
                .where(SupportTicket.sku == sku, SupportTicket.created_at >= start)
            ).scalar() or 0
        )
        top = db.execute(
            select(SupportTicket.subject, func.count(SupportTicket.id).label("c"))
            .where(SupportTicket.sku == sku, SupportTicket.created_at >= start)
            .group_by(SupportTicket.subject).order_by(func.count(SupportTicket.id).desc()).limit(1)
        ).first()
        return {"sku": sku, "window_days": days, "count": cnt, "top_subject": top[0] if top else None}
    finally:
        db.close()
