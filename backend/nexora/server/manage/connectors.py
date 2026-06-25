"""连接器管理 (对应 onyx/server/manage)。网页索引 + 索引任务状态。"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexora.db.engine import get_session
from nexora.db.models import Connector, IndexAttempt, SourceType
from nexora.tasks.indexing_tasks import index_web_task


class WebIndexRequest(BaseModel):
    url: str
    name: str | None = None


class IndexAttemptOut(BaseModel):
    id: int
    connector_id: int
    status: str
    num_docs: int
    num_chunks: int
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


router = APIRouter(prefix="/manage", tags=["connectors"])


@router.post("/connectors/web", response_model=IndexAttemptOut)
def index_web(req: WebIndexRequest, db: Session = Depends(get_session)) -> IndexAttempt:
    connector = Connector(
        name=req.name or f"web-{uuid.uuid4().hex[:8]}",
        source=SourceType.web,
        config={"url": req.url},
    )
    db.add(connector)
    db.flush()
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    index_web_task.delay(attempt.id, req.url)
    return attempt


@router.get("/connectors", response_model=list[dict])
def list_connectors(db: Session = Depends(get_session)) -> list[dict]:
    rows = db.execute(select(Connector).order_by(Connector.id.desc())).scalars()
    return [
        {"id": c.id, "name": c.name, "source": c.source.value, "config": c.config}
        for c in rows
    ]


@router.get("/index-attempts", response_model=list[IndexAttemptOut])
def list_attempts(db: Session = Depends(get_session)) -> list[IndexAttempt]:
    return list(db.execute(select(IndexAttempt).order_by(IndexAttempt.id.desc())).scalars())


@router.get("/index-attempts/{attempt_id}", response_model=IndexAttemptOut)
def get_attempt(attempt_id: int, db: Session = Depends(get_session)) -> IndexAttempt:
    a = db.get(IndexAttempt, attempt_id)
    if not a:
        raise HTTPException(status_code=404, detail="未找到索引任务")
    return a
