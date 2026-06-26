"""Admin API: persona / 模型状态 / trace / 系统设置。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import milvus
from app.db.engine import get_session
from app.db.models import Persona, Trace
from app.models.health_check import check_model_server, check_ollama
from app.models.llm_router import router_status
from app.observability import metrics

router = APIRouter(prefix="/admin", tags=["admin"])


class PersonaCreate(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str
    tools: list[str] = []


class PersonaOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_prompt: str
    tools: list[str] = []

    class Config:
        from_attributes = True


@router.post("/personas", response_model=PersonaOut)
def create_persona(body: PersonaCreate, db: Session = Depends(get_session)) -> Persona:
    p = Persona(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        tools=body.tools,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/personas", response_model=list[PersonaOut])
def list_personas(db: Session = Depends(get_session)) -> list[Persona]:
    return list(db.execute(select(Persona).order_by(Persona.id)).scalars())


@router.get("/traces")
def list_traces(db: Session = Depends(get_session)) -> list[dict]:
    rows = db.execute(select(Trace).order_by(Trace.id.desc()).limit(50)).scalars()
    return [
        {
            "trace_id": t.trace_id,
            "question": t.question,
            "intent": t.intent,
            "steps": t.steps,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in rows
    ]


@router.get("/status")
def system_status() -> dict:
    return {
        "llm_router": router_status(),
        "ollama": check_ollama(),
        "model_server": check_model_server(),
        "vector_db": {
            "backend": "milvus",
            "collection": settings.milvus_collection,
            "count": milvus.count(),
        },
        "langfuse_enabled": settings.langfuse_enabled,
        "metrics": metrics.snapshot(),
    }
