"""Celery 入库任务: 文件 / 网页 → ingestion pipeline。"""
from __future__ import annotations

from app.db.engine import SessionLocal
from app.db.models import IndexAttempt
from app.ingestion.indexer import index_raw_docs
from app.ingestion.parser import parse_file, parse_url
from app.tasks.celery_app import celery_app


@celery_app.task(name="index_files")
def index_files_task(attempt_id: int, file_paths: list[str], titles: list[str]) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        raws = [parse_file(p, t) for p, t in zip(file_paths, titles)]
        attempt = index_raw_docs(db, raws, attempt, attempt.connector_id)
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()


@celery_app.task(name="index_web")
def index_web_task(attempt_id: int, url: str) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        raws = [parse_url(url)]
        attempt = index_raw_docs(db, raws, attempt, attempt.connector_id)
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()
