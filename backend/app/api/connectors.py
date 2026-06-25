"""连接器：网页索引 + 索引任务状态查询。"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Connector, IndexAttempt, SourceType
from app.schemas import IndexAttemptOut, WebIndexRequest
from app.tasks.indexing_tasks import index_web_task

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.post("/web", response_model=IndexAttemptOut)
def index_web(req: WebIndexRequest, db: Session = Depends(get_db)) -> IndexAttempt:
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


@router.get("/attempts", response_model=list[IndexAttemptOut])
def list_attempts(db: Session = Depends(get_db)) -> list[IndexAttempt]:
    return list(
        db.execute(select(IndexAttempt).order_by(IndexAttempt.id.desc())).scalars()
    )


@router.get("/attempts/{attempt_id}", response_model=IndexAttemptOut)
def get_attempt(attempt_id: int, db: Session = Depends(get_db)) -> IndexAttempt:
    attempt = db.get(IndexAttempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="未找到索引任务")
    return attempt
