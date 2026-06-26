"""极简指标计数 (内存)。"""
from __future__ import annotations

from collections import Counter

_counters: Counter = Counter()


def incr(name: str, n: int = 1) -> None:
    _counters[name] += n


def snapshot() -> dict:
    return dict(_counters)
