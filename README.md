# Nexora —— Python 版 Ragent AI (LangGraph Agent 平台)

一个为「**边学边做**」设计的通用企业级 AI Agent 平台。后端用 **FastAPI + LangGraph + LangChain**
编排 Agent 工作流,向量库用 **Milvus**,工具走 **MCP**,可观测用 **Langfuse**,前端是 Onyx 风格的 React UI。

> 通用领域(企业知识 + 业务工具),示例数据为合成资料,仅供学习。

## 核心架构

```
React Chat / Admin
      ↓
FastAPI API Gateway  (SSE 流式 / Auth / Rate Limit)
      ↓
LangGraph Agent Workflow:
  load_memory → rewrite_query → classify_intent → route
     ├─ knowledge_qa → retrieve_docs(Milvus dense + BM25 → RRF) → rerank → build_prompt → generate
     ├─ tool_call    → call_tools(MCP) → build_prompt → generate
     ├─ chitchat     → build_prompt → generate
     └─ clarification→ clarify (反问用户)
  → save_trace(Langfuse) + save_memory(Redis/Postgres)
```

## 技术栈

| 层 | 选型 |
|---|---|
| API 网关 | FastAPI + SSE + Redis 限流 |
| Agent 编排 | **LangGraph**(StateGraph 多节点 + 条件路由) |
| LLM | **LangChain** chat models,llm_router 按任务选模型(默认 Ollama `qwen2.5:3b`,可切 Claude/OpenAI),含熔断/健康检查 |
| 向量库 | **Milvus**(HNSW/COSINE dense 检索) |
| 关键词召回 | **BM25 + jieba**(中文友好),与 dense 做 **RRF** 融合 |
| 重排 | LLM 列表式 rerank(可关) |
| 嵌入 | 独立 **model_server**(代理 Ollama `bge-m3`) |
| 工具 | **MCP client** + 内置 mock(天气/工单/销售),可接真实 MCP server |
| 记忆 | 短期(Redis)+ 滚动摘要 + 历史(Postgres) |
| 可观测 | **Langfuse**(节点级 trace)+ 本地 trace 兜底 |
| 前端 | Next.js 15 + Tailwind + Radix + Phosphor + SWR + Zustand |
| 异步 | Celery + Redis |
| 部署 | docker-compose / K8s / Helm |

后端目录(`backend/app/`):`api / graph / rag / intent / models / tools / memory / ingestion / observability / db / tasks`。

## 快速开始

> 内存提示:Milvus + Langfuse + Ollama 较吃内存,建议 Docker 分配 **≥ 10GB**。

```bash
cp .env.example .env
docker compose up -d
docker compose logs -f ollama-pull          # 等模型拉好 (qwen2.5:3b + bge-m3)
docker compose run --rm backend python -m app.seed.seed   # 通用种子数据
```

打开:
- 前端:http://localhost:3000
- 后端 Swagger:http://localhost:8000/docs
- Langfuse:http://localhost:3001 (admin@nexora.local / nexora123)

### 演示脚本(看 LangGraph 自动路由)

1. **知识问答**:「年假有多少天？」→ 流程:改写→意图(knowledge_qa)→检索→重排→生成,回答带 `[1]` 引用。
2. **工具调用**:「查一下北京的天气」→ 意图(tool_call)→ MCP `get_weather` → 回答(显示工具结果)。
3. **请求澄清**:「那个东西怎么弄」→ 意图(clarification)→ 反问澄清。
4. 后台「Trace」页看每次请求的节点级链路;「系统状态」页看模型路由/熔断/Milvus 计数。
5. `POST /api/knowledge/search` 看 `dense_rank` / `bm25_rank` 双路召回(中文也命中)。

## 切换 LLM 到 Claude / OpenAI

`.env`:
```
LLM_PROVIDER=anthropic        # 或 openai
LLM_MODEL_MAIN=claude-sonnet-4-6
LLM_MODEL_FAST=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=sk-ant-...
```
嵌入仍走 model_server(Ollama bge-m3)。

## Kubernetes

`deploy/k8s`(kustomize):postgres / redis / milvus(etcd+minio+standalone)/ ollama / model-server /
backend / worker / frontend / langfuse + migrate-seed Job + Ingress。

```bash
docker build -t nexora/backend:latest ./backend
docker build -t nexora/frontend:latest --build-arg NEXT_PUBLIC_API_BASE=http://api.nexora.local ./frontend
kubectl apply -k deploy/k8s/
```

## 演进历史

- v1:FastAPI + pgvector + 自写 RAG/agent(已存 git 历史)
- v2:OpenSearch + LiteLLM + Onyx 风格 UI
- **v3(当前)**:LangGraph 工作流 + Milvus + MCP + Langfuse,通用领域

## 已实测

macOS Docker(7.7GB,建议调到 10GB+)完整跑通:三种意图路由(知识/工具/澄清)、Milvus+BM25 混合检索
(中文关键词命中)、节点级流程时间线、Langfuse trace。详见 `docs/ARCHITECTURE.md` 与 `docs/LEARNING_ROADMAP.md`。
