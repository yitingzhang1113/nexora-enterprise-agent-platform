"""Celery 应用 (对应 onyx/background/celery)。broker/backend = Redis。"""
from celery import Celery

from nexora.configs.app_configs import settings

celery_app = Celery(
    "nexora",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["nexora.tasks.indexing_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
