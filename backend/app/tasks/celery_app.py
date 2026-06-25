"""Celery 应用 (broker/backend 用 Redis)。

对应 Onyx 用 Celery + Redis 跑后台索引。把耗时的「抓取+嵌入」放到 worker，
API 请求立即返回，避免阻塞 HTTP。
"""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "nexora",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.indexing_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
