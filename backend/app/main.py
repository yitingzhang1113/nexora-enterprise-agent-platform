"""FastAPI 入口：装配路由 + CORS。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import chat, connectors, documents, health, personas, search
from app.config import settings

app = FastAPI(
    title="Nexora —— 企业级 Agent / RAG 平台 (学习型, 医药 domain)",
    version=__version__,
    description="仿 Onyx 架构: FastAPI + Postgres/pgvector + Celery + Ollama。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(connectors.router)
app.include_router(search.router)
app.include_router(personas.router)
app.include_router(chat.router)


@app.get("/")
def root() -> dict:
    return {"name": "nexora", "version": __version__, "docs": "/docs"}
