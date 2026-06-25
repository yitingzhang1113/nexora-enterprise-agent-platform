"""Celery 索引任务 (对应 onyx/background/celery/tasks/docprocessing)。

逻辑与同步管线一致, 只是搬到 worker 进程执行。
"""
from __future__ import annotations

from nexora.connectors.file_upload.connector import FileUploadConnector
from nexora.connectors.web.connector import WebConnector
from nexora.db.engine import SessionLocal
from nexora.db.models import IndexAttempt
from nexora.indexing.indexing_pipeline import run_indexing
from nexora.tasks.celery_app import celery_app


@celery_app.task(name="index_files")
def index_files_task(attempt_id: int, file_paths: list[str], titles: list[str]) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        conn = FileUploadConnector(file_paths=file_paths, titles=titles)
        attempt = run_indexing(db, conn, attempt.connector_id, attempt)
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()


@celery_app.task(name="index_web")
def index_web_task(attempt_id: int, url: str) -> dict:
    db = SessionLocal()
    try:
        attempt = db.get(IndexAttempt, attempt_id)
        conn = WebConnector(urls=[url])
        attempt = run_indexing(db, conn, attempt.connector_id, attempt)
        return {"status": attempt.status.value, "num_chunks": attempt.num_chunks}
    finally:
        db.close()
