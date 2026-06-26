"""链路追踪: 记录 LangGraph 节点级步骤, 落 Postgres + 上报 Langfuse。"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager

from app.db.engine import SessionLocal
from app.db.models import Trace
from app.observability import metrics
from app.observability.langfuse import get_langfuse


class Tracer:
    def __init__(self, question: str, session_id: int | None) -> None:
        self.trace_id = uuid.uuid4().hex
        self.question = question
        self.session_id = session_id
        self.steps: list[dict] = []
        self.intent: str | None = None
        self._start = time.monotonic()

    @contextmanager
    def step(self, node: str):
        t0 = time.monotonic()
        info: dict = {}
        try:
            yield info
        finally:
            ms = int((time.monotonic() - t0) * 1000)
            self.steps.append({"node": node, "ms": ms, "info": info})
            metrics.incr(f"node.{node}")

    def finish(self, answer: str = "") -> None:
        latency_ms = int((time.monotonic() - self._start) * 1000)
        # 1) 本地兜底
        db = SessionLocal()
        try:
            db.add(
                Trace(
                    session_id=self.session_id,
                    trace_id=self.trace_id,
                    question=self.question,
                    intent=self.intent,
                    steps=self.steps,
                    latency_ms=latency_ms,
                )
            )
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        finally:
            db.close()

        # 2) Langfuse
        lf = get_langfuse()
        if lf is not None:
            try:
                trace = lf.trace(
                    id=self.trace_id,
                    name="ragent_workflow",
                    input=self.question,
                    output=answer,
                    metadata={"intent": self.intent, "latency_ms": latency_ms},
                )
                for s in self.steps:
                    trace.span(name=s["node"], metadata=s).end()
                lf.flush()
            except Exception:  # noqa: BLE001
                pass
