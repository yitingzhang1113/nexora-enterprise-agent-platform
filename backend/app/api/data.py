"""业务数据概览 API。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.engine import get_session
from app.db.models import (
    Campaign,
    Customer,
    Order,
    OrderItem,
    Product,
    Return,
    SupportTicket,
)

router = APIRouter(prefix="/data", tags=["data"])


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
