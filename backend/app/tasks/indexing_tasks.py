"""Celery 索引任务：把同步管线包成异步任务。

注意逻辑与 app/indexing/pipeline.py 完全一致 —— 这正是「先同步后异步」
教学设计的目的：异步化只是把同一段逻辑搬到 worker 进程执行。
"""
from __future__ import annotations

from app.connectors.file_upload import FileUploadConnector
from app.connectors.web import WebConnector
from app.db.base import SessionLocal
from app.indexing.pipeline import run_indexing
from app.models import IndexAttempt, IndexStatus
from app.tasks.celery_app import celery_app


@celery_app.task(name="index_files")
def index_files_task(attempt_id: int, file_paths: list[str], titles: list[str]) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        connector = FileUploadConnector(file_paths=file_paths, titles=titles)
        attempt = run_indexing(
            db, connector, connector_id=attempt.connector_id, attempt=attempt
        )
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()


@celery_app.task(name="index_web")
def index_web_task(attempt_id: int, url: str) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        connector = WebConnector(urls=[url])
        attempt = run_indexing(
            db, connector, connector_id=attempt.connector_id, attempt=attempt
        )
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()
