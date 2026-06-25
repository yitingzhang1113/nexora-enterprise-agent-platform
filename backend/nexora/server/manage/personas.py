"""Persona (AI 助手) 管理。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexora.db.engine import get_session
from nexora.db.models import Persona


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
    created_at: datetime

    class Config:
        from_attributes = True


router = APIRouter(tags=["personas"])


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


@router.get("/personas/{persona_id}", response_model=PersonaOut)
def get_persona(persona_id: int, db: Session = Depends(get_session)) -> Persona:
    p = db.get(Persona, persona_id)
    if not p:
        raise HTTPException(status_code=404, detail="未找到 persona")
    return p
