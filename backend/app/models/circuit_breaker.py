"""简单熔断器: 连续失败达阈值则打开, 冷却后半开。"""
from __future__ import annotations

import time


class CircuitBreaker:
    def __init__(self, threshold: int = 5, cooldown_s: int = 30) -> None:
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.failures = 0
        self.opened_at: float | None = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.monotonic() - self.opened_at > self.cooldown_s:
            # 冷却结束, 半开 (允许一次尝试)
            self.opened_at = None
            self.failures = 0
            return False
        return True

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.monotonic()

    def state(self) -> str:
        return "open" if self.is_open() else ("half_open" if self.failures else "closed")


# 全局 (按 provider 共用一个即可, 学习版简化)
llm_breaker = CircuitBreaker()
