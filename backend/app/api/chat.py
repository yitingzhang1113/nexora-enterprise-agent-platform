"""聊天接口。

两种模式:
- 普通 RAG (默认): 先检索 → 拼 prompt → SSE 流式生成。返回 citations + 流式 token。
- Agent (use_agent=true): 模型用工具自行检索/计算，返回完整 JSON (非流式)。
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.agent.loop import run_agent
from app.chat.rag import (
    DEFAULT_SYSTEM,
    build_rag_messages,
    format_context,
    retrieve,
)
from app.db.base import SessionLocal, get_db
from app.llm import get_llm
from app.models import ChatMessage, ChatSession, Persona
from app.schemas import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_HISTORY = 6


def _get_or_create_session(db: Session, req: ChatRequest) -> ChatSession:
    if req.session_id:
        session = db.get(ChatSession, req.session_id)
        if session:
            return session
    session = ChatSession(persona_id=req.persona_id, title=req.message[:80])
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _load_history(db: Session, session_id: int) -> list[dict]:
    session = db.get(ChatSession, session_id)
    if not session:
        return []
    msgs = [m for m in session.messages if m.role in ("user", "assistant")]
    history = [{"role": m.role, "content": m.content} for m in msgs[-MAX_HISTORY:]]
    return history


def _resolve_persona(db: Session, persona_id: int | None) -> tuple[str, list[str] | None]:
    if persona_id:
        persona = db.get(Persona, persona_id)
        if persona:
            return persona.system_prompt, list(persona.tools or [])
    return DEFAULT_SYSTEM, None


@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    session = _get_or_create_session(db, req)
    system, tools = _resolve_persona(db, req.persona_id or session.persona_id)
    history = _load_history(db, session.id)

    # 保存用户消息
    db.add(ChatMessage(session_id=session.id, role="user", content=req.message))
    db.commit()

    # ---------- Agent 模式 (非流式) ----------
    if req.use_agent:
        result = run_agent(
            db, req.message, system=system, history=history, allowed_tools=tools
        )
        db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=result["content"],
                citations=result["citations"],
            )
        )
        db.commit()
        return {
            "session_id": session.id,
            "content": result["content"],
            "citations": result["citations"],
            "steps": result["steps"],
            "mode": "agent",
        }

    # ---------- 普通 RAG 模式 (SSE 流式) ----------
    hits = retrieve(db, req.message)
    context, citations = format_context(hits)
    messages = build_rag_messages(req.message, context, history)

    # 关键: 在进入生成器前把需要的值取成普通变量。
    # 因为 SSE 生成器在请求级 DB session 关闭后才执行, 此时 ORM 实例已 detached,
    # 再访问 session.id 会触发 DetachedInstanceError。
    sid = session.id

    def event_stream():
        yield {
            "event": "meta",
            "data": json.dumps(
                {"session_id": sid, "citations": citations}, ensure_ascii=False
            ),
        }
        llm = get_llm()
        collected = []
        for token in llm.stream_chat(messages, system=system):
            collected.append(token)
            yield {"event": "token", "data": token}

        # 流结束后持久化 assistant 消息 (用独立 session 避免请求级 session 已关闭)
        answer = "".join(collected)
        persist_db = SessionLocal()
        try:
            persist_db.add(
                ChatMessage(
                    session_id=sid,
                    role="assistant",
                    content=answer,
                    citations=citations,
                )
            )
            persist_db.commit()
        finally:
            persist_db.close()
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_stream())
