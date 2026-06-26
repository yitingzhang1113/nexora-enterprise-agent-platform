"""业务数据概览 + 看板聚合 API。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.engine import get_session
from app.db.models import (
    Campaign,
    Customer,
    Inventory,
    Order,
    OrderItem,
    Product,
    Return,
    SupportTicket,
)

router = APIRouter(prefix="/data", tags=["data"])

ANOMALY_SKU = "NX-AIR-FRYER-001"


@router.get("/overview")
def overview(db: Session = Depends(get_session)) -> dict:
    def count(model) -> int:
        return int(db.execute(select(func.count()).select_from(model)).scalar() or 0)

    return {
        "products": count(Product),
        "customers": count(Customer),
        "orders": count(Order),
        "order_items": count(OrderItem),
        "returns": count(Return),
        "support_tickets": count(SupportTicket),
        "campaigns": count(Campaign),
    }


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_session)) -> dict:
    """看板聚合: 销量趋势 / 退货率 Top / 库存水位 / KPI。"""
    now = datetime.now(timezone.utc)
    start14 = now - timedelta(days=14)
    day = func.date_trunc("day", Order.created_at)

    # 1) 近 14 天每日销量 (整体 + 异常 SKU)
    overall_rows = db.execute(
        select(day.label("d"), func.coalesce(func.sum(OrderItem.qty), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= start14)
        .group_by(day).order_by(day)
    ).all()
    anomaly_rows = db.execute(
        select(day.label("d"), func.coalesce(func.sum(OrderItem.qty), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= start14, OrderItem.sku == ANOMALY_SKU)
        .group_by(day).order_by(day)
    ).all()
    amap = {r[0].date().isoformat(): int(r[1]) for r in anomaly_rows}
    sales_trend = [
        {"date": r[0].date().isoformat()[5:], "units": int(r[1]),
         "anomaly": amap.get(r[0].date().isoformat(), 0)}
        for r in overall_rows
    ]

    # 2) 退货率 Top (按退货数取前 6 SKU, 计算 退货/订单 比)
    top_ret = db.execute(
        select(Return.sku, func.count(Return.id).label("rc"))
        .group_by(Return.sku).order_by(func.count(Return.id).desc()).limit(6)
    ).all()
    return_rate = []
    for sku, rc in top_ret:
        orders = int(
            db.execute(select(func.count(OrderItem.id)).where(OrderItem.sku == sku)).scalar() or 0
        )
        rate = round(int(rc) / orders * 100, 1) if orders else 0.0
        return_rate.append({"sku": sku, "rate": rate, "returns": int(rc)})

    # 3) 库存水位 (最低的 8 个 SKU)
    inv_rows = db.execute(
        select(Inventory.sku, Inventory.stock, Inventory.safety_stock)
        .order_by(Inventory.stock).limit(8)
    ).all()
    inventory = [
        {"sku": s, "stock": int(st), "safety": int(ss),
         "below": int(st) < int(ss)}
        for s, st, ss in inv_rows
    ]

    # 4) KPI
    total_orders = int(db.execute(select(func.count(Order.id))).scalar() or 0)
    total_returns = int(db.execute(select(func.count(Return.id))).scalar() or 0)
    total_items = int(db.execute(select(func.count(OrderItem.id))).scalar() or 0)
    low_stock = int(
        db.execute(
            select(func.count(Inventory.id)).where(Inventory.stock < Inventory.safety_stock)
        ).scalar() or 0
    )
    kpis = {
        "total_orders": total_orders,
        "total_returns": total_returns,
        "overall_return_rate": round(total_returns / total_items * 100, 1) if total_items else 0.0,
        "low_stock_skus": low_stock,
    }
    return {"sales_trend": sales_trend, "return_rate": return_rate,
            "inventory": inventory, "kpis": kpis}
