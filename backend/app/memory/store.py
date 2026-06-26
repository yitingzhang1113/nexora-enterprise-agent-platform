"""长期记忆 (Postgres): 历史消息 + 滚动摘要。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, MemorySummary


def load_db_history(db: Session, session_id: int, limit: int = 6) -> list[dict]:
    rows = list(
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id, ChatMessage.role.in_(("user", "assistant")))
            .order_by(ChatMessage.id.desc())
            .limit(limit)
        ).scalars()
    )
    rows.reverse()
    return [{"role": m.role, "content": m.content} for m in rows]


def get_summary(db: Session, session_id: int) -> str | None:
    row = db.execute(
        select(MemorySummary).where(MemorySummary.session_id == session_id)
    ).scalar_one_or_none()
    return row.summary if row else None


def save_summary(db: Session, session_id: int, summary: str) -> None:
    row = db.execute(
        select(MemorySummary).where(MemorySummary.session_id == session_id)
    ).scalar_one_or_none()
    if row:
        row.summary = summary
    else:
        db.add(MemorySummary(session_id=session_id, summary=summary))
    db.commit()
