"""FastAPI 入口 (对应 onyx/main.py)。

模仿 Onyx: 用 `include_router_with_global_prefix_prepended` 给所有业务路由
统一加 `/api` 前缀, 再单独挂健康检查在根路径。
"""
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nexora import __version__
from nexora.configs.app_configs import settings
from nexora.server.documents.api import router as documents_router
from nexora.server.features.search import router as search_router
from nexora.server.health import router as health_router
from nexora.server.manage.connectors import router as connectors_router
from nexora.server.manage.llm import router as llm_router
from nexora.server.manage.personas import router as personas_router
from nexora.server.manage.search_settings import router as search_settings_router
from nexora.server.query_and_chat.chat_backend import router as chat_router


def include_router_with_global_prefix_prepended(app: FastAPI, router: APIRouter) -> None:
    """给 router 现有 prefix 再叠加全局 /api 前缀 (对齐 Onyx 行为)。"""
    app.include_router(router, prefix=settings.app_api_prefix.rstrip("/"))


def get_application() -> FastAPI:
    app = FastAPI(
        title="Nexora v2 —— 企业级 Agent / RAG 平台 (仿 Onyx, 医药 domain)",
        version=__version__,
        description="FastAPI + OpenSearch + LiteLLM + model_server + Celery。",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 健康检查挂根路径 (K8s 探针用), 不加 /api 前缀
    app.include_router(health_router)

    # 业务路由统一 /api 前缀
    for r in (
        chat_router,
        search_router,
        documents_router,
        connectors_router,
        personas_router,
        llm_router,
        search_settings_router,
    ):
        include_router_with_global_prefix_prepended(app, r)

    @app.get("/")
    def root() -> dict:
        return {"name": "nexora", "version": __version__, "docs": "/docs"}

    return app


app = get_application()
