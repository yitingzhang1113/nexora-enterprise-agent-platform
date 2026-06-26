"""Locust 压测脚本 (只交付脚本; 本地 7.7GB 不建议跑满负载)。

用法:
    pip install locust
    locust -f loadtest/locustfile.py --host http://localhost:8000
    # 然后浏览器 http://localhost:8089 设置并发 (如 100 users) 观察 p50/p95/p99。

指标关注:
- /api/knowledge/search 的 p50/p95/p99 延迟
- /api/chat SSE 首 token 延迟 (本脚本测整段耗时)
"""
from __future__ import annotations

import json
import time

from locust import HttpUser, between, task

SEARCH_QUERIES = [
    "退款超过200美元需要审批吗",
    "安全库存是多少",
    "退货率超过多少要暂停广告",
]


class OpsAgentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search(self):
        q = SEARCH_QUERIES[int(time.time()) % len(SEARCH_QUERIES)]
        self.client.post("/api/knowledge/search", json={"query": q, "top_k": 3}, name="search")

    @task(1)
    def chat_first_token(self):
        """测 SSE 首 token 延迟。"""
        t0 = time.time()
        with self.client.post(
            "/api/chat",
            json={"message": "安全库存是多少"},
            stream=True,
            name="chat_first_token",
            catch_response=True,
        ) as resp:
            first = None
            for raw in resp.iter_lines():
                if raw and raw.decode("utf-8", "ignore").startswith("event: token"):
                    first = time.time() - t0
                    break
            if first is not None:
                resp.success()
