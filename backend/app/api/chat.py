"""聊天 API: 跑 LangGraph 工作流, 以 SSE 把节点流程 + token 推给前端。

SSE 事件: meta / node / tool / citations / token / clarification / done
- node:  每个 LangGraph 节点完成时推一条 (前端画流程时间线)
- token: 仅 generate 节点的 LLM token (按 langgraph_node 过滤)
"""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.api.auth import rate_limit
from app.db.engine import SessionLocal, get_session
from app.db.models import ChatMessage, ChatSession, Persona
from app.graph.workflow import get_workflow
from app.observability.tracing import Tracer
from app.rag.prompt_builder import DEFAULT_SYSTEM

router = APIRouter(tags=["chat"])

NODE_LABELS = {
    "load_memory": "加载记忆",
    "rewrite_query": "改写问题",
    "classify_intent": "意图识别",
    "retrieve_docs": "知识检索",
    "rerank": "重排",
    "call_tools": "工具调用",
    "clarify": "请求澄清",
    "build_prompt": "组装 Prompt",
    "generate": "生成回答",
    "save_memory": "保存记忆",
}


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    persona_id: int | None = None


class ChatSessionOut(BaseModel):
    id: int
    persona_id: int | None = None
    title: str | None = None

    class Config:
        from_attributes = True


def _get_or_create_session(db: Session, req: ChatRequest) -> ChatSession:
    if req.session_id:
        s = db.get(ChatSession, req.session_id)
        if s:
            return s
    s = ChatSession(persona_id=req.persona_id, title=req.message[:80])
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _resolve_persona(db: Session, persona_id: int | None) -> tuple[str, list[str]]:
    if persona_id:
        p = db.get(Persona, persona_id)
        if p:
            return p.system_prompt, list(p.tools or [])
    return DEFAULT_SYSTEM, []


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_session), _: None = Depends(rate_limit)):
    session = _get_or_create_session(db, req)
    system, tools = _resolve_persona(db, req.persona_id or session.persona_id)
    sid = session.id

    db.add(ChatMessage(session_id=sid, role="user", content=req.message))
    db.commit()

    initial = {
        "session_id": sid,
        "persona_system": system,
        "persona_tools": tools,
        "question": req.message,
    }

    def event_stream():
        yield {"event": "meta", "data": json.dumps({"session_id": sid}, ensure_ascii=False)}
        tracer = Tracer(req.message, sid)
        last = time.monotonic()
        citations: list = []
        answer_parts: list[str] = []
        clarification = None
        app_graph = get_workflow()

        for mode, data in app_graph.stream(initial, stream_mode=["updates", "messages"]):
            if mode == "messages":
                msg_chunk, meta = data
                if meta.get("langgraph_node") == "generate":
                    tok = getattr(msg_chunk, "content", "") or ""
                    if tok:
                        answer_parts.append(tok)
                        yield {"event": "token", "data": tok}
                continue

            # mode == "updates": {node_name: update_dict}
            for node, update in data.items():
                now = time.monotonic()
                tracer.steps.append({"node": node, "ms": int((now - last) * 1000), "info": {}})
                last = now
                yield {
                    "event": "node",
                    "data": json.dumps(
                        {"node": node, "label": NODE_LABELS.get(node, node)},
                        ensure_ascii=False,
                    ),
                }
                if node == "classify_intent":
                    tracer.intent = (update or {}).get("intent")
                if node == "rerank":
                    citations = (update or {}).get("citations") or []
                    yield {"event": "citations", "data": json.dumps(citations, ensure_ascii=False)}
                if node == "call_tools":
                    for tr in (update or {}).get("tool_results") or []:
                        yield {"event": "tool", "data": json.dumps(tr, ensure_ascii=False)}
                if node == "clarify":
                    clarification = (update or {}).get("clarification")
                    answer_parts.append(clarification or "")
                    yield {
                        "event": "clarification",
                        "data": json.dumps({"text": clarification}, ensure_ascii=False),
                    }

        answer = "".join(answer_parts)
        # 持久化 + trace
        persist = SessionLocal()
        try:
            persist.add(
                ChatMessage(
                    session_id=sid,
                    role="assistant",
                    content=answer,
                    citations=citations,
                    meta={"intent": tracer.intent, "trace_id": tracer.trace_id},
                )
            )
            persist.commit()
        finally:
            persist.close()
        tracer.finish(answer)
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_stream())


@router.get("/chat-sessions", response_model=list[ChatSessionOut])
def list_sessions(db: Session = Depends(get_session)) -> list[ChatSession]:
    return list(db.execute(select(ChatSession).order_by(ChatSession.id.desc())).scalars())


@router.get("/chat-sessions/{session_id}/messages")
def session_messages(session_id: int, db: Session = Depends(get_session)) -> list[dict]:
    s = db.get(ChatSession, session_id)
    if not s:
        return []
    return [
        {"role": m.role, "content": m.content, "citations": m.citations, "meta": m.meta}
        for m in s.messages
    ]
