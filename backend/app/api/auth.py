"""鉴权占位 + Redis 简单限流 (对应 SSE Streaming / Auth / Rate Limit 层)。

学习版不做登录: current_user 返回演示用户。限流用 Redis 固定窗口。
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.db.redis import redis_client

router = APIRouter(tags=["auth"])


@dataclass
class CurrentUser:
    id: int = 0
    email: str = "demo@nexora.local"
    is_admin: bool = True


def current_user() -> CurrentUser:
    return CurrentUser()


def rate_limit(request: Request) -> None:
    """按客户端 IP 固定窗口限流 (每分钟 settings.rate_limit_per_min 次)。"""
    ip = request.client.host if request.client else "unknown"
    window = int(time.time() // 60)
    key = f"rl:{ip}:{window}"
    try:
        n = redis_client.incr(key)
        if n == 1:
            redis_client.expire(key, 70)
        if n > settings.rate_limit_per_min:
            raise HTTPException(status_code=429, detail="请求过于频繁, 请稍后再试")
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001 —— Redis 不可用时不阻断
        return


@router.get("/auth/me")
def me(user: CurrentUser = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}
