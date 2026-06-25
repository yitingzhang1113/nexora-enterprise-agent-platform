"""chat 路由 (对应 onyx/server/query_and_chat/chat_backend.py)。

POST /chat        -> SSE 流式 (meta/tool/citations/token/done)
GET  /chat-sessions          -> 会话列表
GET  /chat-sessions/{id}/messages -> 某会话消息
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from nexora.auth.users import CurrentUser, current_user
from nexora.chat.process_message import DEFAULT_SYSTEM, stream_chat
from nexora.db.engine import SessionLocal, get_session
from nexora.db.models import ChatMessage, ChatSession, Persona
from nexora.server.query_and_chat.models import (
    ChatMessageOut,
    ChatRequest,
    ChatSessionOut,
)
from nexora.tools.tool_runner import get_tools

router = APIRouter(tags=["chat"])

MAX_HISTORY = 6


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


def _load_history(db: Session, session_id: int) -> list[dict]:
    s = db.get(ChatSession, session_id)
    if not s:
        return []
    msgs = [m for m in s.messages if m.role in ("user", "assistant")]
    return [{"role": m.role, "content": m.content} for m in msgs[-MAX_HISTORY:]]


def _resolve_persona(db: Session, persona_id: int | None) -> tuple[str, list[str] | None]:
    if persona_id:
        p = db.get(Persona, persona_id)
        if p:
            return p.system_prompt, list(p.tools or [])
    return DEFAULT_SYSTEM, None


@router.post("/chat")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_session),
    user: CurrentUser = Depends(current_user),
):
    session = _get_or_create_session(db, req)
    system, tool_names = _resolve_persona(db, req.persona_id or session.persona_id)
    history = _load_history(db, session.id)
    tools = get_tools(tool_names)

    db.add(ChatMessage(session_id=session.id, role="user", content=req.message))
    db.commit()
    sid = session.id  # 取成普通变量, 避免 SSE 生成器里 DetachedInstanceError

    def event_stream():
        yield {"event": "meta", "data": json.dumps({"session_id": sid}, ensure_ascii=False)}
        answer_parts: list[str] = []
        citations: list = []
        for pkt in stream_chat(req.message, system, req.use_agent, tools, history):
            ptype = pkt["type"]
            if ptype == "tool":
                yield {"event": "tool", "data": json.dumps(pkt["data"], ensure_ascii=False)}
            elif ptype == "citations":
                citations = pkt["data"]
                yield {"event": "citations", "data": json.dumps(citations, ensure_ascii=False)}
            elif ptype == "token":
                answer_parts.append(pkt["data"])
                yield {"event": "token", "data": pkt["data"]}

        # 持久化 assistant 消息 (独立 session)
        persist = SessionLocal()
        try:
            persist.add(
                ChatMessage(
                    session_id=sid,
                    role="assistant",
                    content="".join(answer_parts),
                    citations=citations,
                )
            )
            persist.commit()
        finally:
            persist.close()
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_stream())


@router.get("/chat-sessions", response_model=list[ChatSessionOut])
def list_sessions(db: Session = Depends(get_session)) -> list[ChatSession]:
    return list(
        db.execute(select(ChatSession).order_by(ChatSession.id.desc())).scalars()
    )


@router.get("/chat-sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def session_messages(session_id: int, db: Session = Depends(get_session)) -> list[ChatMessage]:
    s = db.get(ChatSession, session_id)
    return list(s.messages) if s else []
