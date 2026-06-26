"""Slack 通知 API (mock 写库的消息列表)。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.engine import get_session
from app.db.models import SlackMessage

router = APIRouter(prefix="/slack", tags=["slack"])


@router.get("/messages")
def list_messages(db: Session = Depends(get_session)) -> list[dict]:
    rows = db.execute(select(SlackMessage).order_by(SlackMessage.id.desc()).limit(100)).scalars()
    return [
        {"id": m.id, "channel": m.channel, "text": m.text, "sent_real": m.sent_real,
         "created_at": m.created_at.isoformat() if m.created_at else None}
        for m in rows
    ]
