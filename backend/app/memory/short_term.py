"""短期记忆 (Redis): 每会话最近 N 轮的快速缓存。"""
from __future__ import annotations

import json

from app.db.redis import redis_client

MAX_TURNS = 12


def _key(session_id: int) -> str:
    return f"session:{session_id}:turns"


def append_turn(session_id: int, role: str, content: str) -> None:
    redis_client.rpush(_key(session_id), json.dumps({"role": role, "content": content}))
    redis_client.ltrim(_key(session_id), -MAX_TURNS, -1)


def get_recent(session_id: int, n: int = 6) -> list[dict]:
    raw = redis_client.lrange(_key(session_id), -n, -1)
    return [json.loads(x) for x in raw]
