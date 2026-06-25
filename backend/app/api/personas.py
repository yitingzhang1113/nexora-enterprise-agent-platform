"""Persona (AI 助手) 的增删查。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Persona
from app.schemas import PersonaCreate, PersonaOut

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("", response_model=PersonaOut)
def create_persona(body: PersonaCreate, db: Session = Depends(get_db)) -> Persona:
    persona = Persona(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        tools=body.tools,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.get("", response_model=list[PersonaOut])
def list_personas(db: Session = Depends(get_db)) -> list[Persona]:
    return list(db.execute(select(Persona).order_by(Persona.id)).scalars())


@router.get("/{persona_id}", response_model=PersonaOut)
def get_persona(persona_id: int, db: Session = Depends(get_db)) -> Persona:
    persona = db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="未找到 persona")
    return persona
