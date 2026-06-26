"""聊天 API: 跑 LangGraph Ops 工作流, SSE 推流程 + 工具 + 审批 + token。

SSE 事件: meta / node / tool / citations / approval / token / clarification / done
- token 仅来自 final_response 节点 (按 langgraph_node 过滤)
"""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.api.auth import rate_limit
from app.db.engine import SessionLocal, get_session
from app.db.models import ChatMessage, ChatSession, Persona
from app.graph.workflow import get_workflow
from app.observability.tracing import Tracer

router = APIRouter(tags=["chat"])

NODE_LABELS = {
    "load_memory": "加载记忆",
    "rewrite_query": "改写问题",
    "classify_intent": "意图识别",
    "plan_tasks": "任务规划",
    "parallel_tool_calls": "并行工具调用",
    "validate_result": "结果校验",
    "human_approval_if_needed": "审批判定",
    "execute_action": "执行动作",
    "final_response": "生成回答",
    "clarify": "请求澄清",
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


def _resolve_persona(db: Session, persona_id: int | None) -> str:
    if persona_id:
        p = db.get(Persona, persona_id)
        if p:
            return p.system_prompt
    return "你是 Nexora 电商运营助手 (Ops Agent)。"


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_session), _: None = Depends(rate_limit)):
    session = _get_or_create_session(db, req)
    system = _resolve_persona(db, req.persona_id or session.persona_id)
    sid = session.id
    db.add(ChatMessage(session_id=sid, role="user", content=req.message))
    db.commit()

    tracer = Tracer(req.message, sid)
    initial = {
        "session_id": sid,
        "trace_id": tracer.trace_id,
        "persona_system": system,
        "question": req.message,
    }

    def event_stream():
        yield {"event": "meta", "data": json.dumps({"session_id": sid, "trace_id": tracer.trace_id},
                                                    ensure_ascii=False)}
        last = time.monotonic()
        citations: list = []
        answer_parts: list[str] = []
        app_graph = get_workflow()

        for mode, data in app_graph.stream(initial, stream_mode=["updates", "messages"]):
            if mode == "messages":
                msg_chunk, meta = data
                if meta.get("langgraph_node") == "final_response":
                    tok = getattr(msg_chunk, "content", "") or ""
                    if tok:
                        answer_parts.append(tok)
                        yield {"event": "token", "data": tok}
                continue

            for node, update in data.items():
                now = time.monotonic()
                tracer.steps.append({"node": node, "ms": int((now - last) * 1000), "info": {}})
                last = now
                yield {"event": "node",
                       "data": json.dumps({"node": node, "label": NODE_LABELS.get(node, node)},
                                          ensure_ascii=False)}
                update = update or {}
                if node == "classify_intent":
                    tracer.intent = update.get("intent")
                if node == "parallel_tool_calls":
                    for tr in update.get("tool_results", []):
                        yield {"event": "tool", "data": json.dumps(
                            {"name": tr["tool"], "args": tr["args"], "result": tr["result"]},
                            ensure_ascii=False)}
                    if update.get("citations"):
                        citations = update["citations"]
                        yield {"event": "citations", "data": json.dumps(citations, ensure_ascii=False)}
                if node == "execute_action":
                    for ea in update.get("executed_actions", []):
                        yield {"event": "tool", "data": json.dumps(
                            {"name": ea["tool"], "args": ea["args"], "result": ea["result"],
                             "executed": True}, ensure_ascii=False)}
                if node == "human_approval_if_needed":
                    for ap in update.get("pending_approvals", []):
                        yield {"event": "approval", "data": json.dumps(ap, ensure_ascii=False)}
                if node == "clarify":
                    answer_parts.append(update.get("clarification") or "")
                    yield {"event": "clarification",
                           "data": json.dumps({"text": update.get("clarification")}, ensure_ascii=False)}

        answer = "".join(answer_parts)
        persist = SessionLocal()
        try:
            persist.add(ChatMessage(session_id=sid, role="assistant", content=answer,
                                    citations=citations,
                                    meta={"intent": tracer.intent, "trace_id": tracer.trace_id}))
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
    return [{"role": m.role, "content": m.content, "citations": m.citations, "meta": m.meta}
            for m in s.messages]
