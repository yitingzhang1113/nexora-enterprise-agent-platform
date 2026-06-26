"""Redis 缓存 (intent / 工具结果 / 检索结果), 带命中率统计。"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from app.db.redis import redis_client
from app.observability import metrics

DEFAULT_TTL = 300


def _key(namespace: str, payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"cache:{namespace}:{h}"


def get(namespace: str, payload: Any) -> Any | None:
    try:
        v = redis_client.get(_key(namespace, payload))
    except Exception:  # noqa: BLE001
        return None
    if v is None:
        metrics.incr(f"cache.miss.{namespace}")
        return None
    metrics.incr(f"cache.hit.{namespace}")
    return json.loads(v)


def set(namespace: str, payload: Any, value: Any, ttl: int = DEFAULT_TTL) -> None:
    try:
        redis_client.setex(_key(namespace, payload), ttl, json.dumps(value, ensure_ascii=False))
    except Exception:  # noqa: BLE001
        pass


def cached(namespace: str, payload: Any, producer, ttl: int = DEFAULT_TTL):
    """读穿缓存: 命中返回, 否则调用 producer() 并写入。"""
    hit = get(namespace, payload)
    if hit is not None:
        return hit
    value = producer()
    set(namespace, payload, value, ttl)
    return value
