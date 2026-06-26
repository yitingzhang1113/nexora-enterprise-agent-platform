"""运营工单 API。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.engine import get_session
from app.db.models import OpsTicket

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/tickets")
def list_tickets(db: Session = Depends(get_session)) -> list[dict]:
    rows = db.execute(select(OpsTicket).order_by(OpsTicket.id.desc()).limit(100)).scalars()
    return [
        {"id": t.id, "title": t.title, "sku": t.sku, "severity": t.severity,
         "status": t.status, "body": t.body,
         "created_at": t.created_at.isoformat() if t.created_at else None}
        for t in rows
    ]
