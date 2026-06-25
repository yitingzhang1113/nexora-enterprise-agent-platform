"""健康检查 (K8s 探针)。"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from nexora.db.engine import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/db")
def health_db(db: Session = Depends(get_session)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
