"""FastAPI 入口 (v3) —— API Gateway。

健康检查挂根路径; 业务路由统一 /api 前缀。
对应架构图: React → FastAPI API Gateway → SSE/Auth/RateLimit → LangGraph Workflow。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import admin, auth, chat, health, knowledge
from app.config import settings


def get_application() -> FastAPI:
    app = FastAPI(
        title="Nexora v3 —— Python 版 Ragent AI (LangGraph)",
        version=__version__,
        description="FastAPI + LangGraph + LangChain + Milvus + MCP + Langfuse。",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)  # 根路径

    prefix = settings.app_api_prefix.rstrip("/")
    for r in (auth.router, chat.router, knowledge.router, admin.router):
        app.include_router(r, prefix=prefix)

    @app.get("/")
    def root() -> dict:
        return {"name": "nexora", "version": __version__, "docs": "/docs"}

    return app


app = get_application()
