"""Redis 客户端 (短期记忆 + 限流)。"""
from __future__ import annotations

import redis

from app.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
