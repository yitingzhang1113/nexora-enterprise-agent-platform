"""鉴权占位 (对应 onyx/auth/users.py, 但本学习版不启用登录)。

Onyx 用 fastapi-users 做 JWT/OAuth/SAML。这里提供一个 no-op 的 `current_user`
依赖, 让 router 的签名与 Onyx 一致 —— 将来替换为真实鉴权时只改这一个文件。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CurrentUser:
    id: int = 0
    email: str = "demo@nexora.local"
    is_admin: bool = True


def current_user() -> CurrentUser:
    """FastAPI 依赖: 始终返回演示用户 (无登录)。"""
    return CurrentUser()
