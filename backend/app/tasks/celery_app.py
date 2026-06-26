"""Celery 应用 (broker/backend = Redis)。"""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "nexora",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.ingestion_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
