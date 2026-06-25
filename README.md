# Nexora —— 仿 Onyx 的企业级 Agent / RAG 平台 (学习型, 医药 domain)

一个为「**边学边做**」设计的企业级 AI Agent / RAG 平台，参考开源项目
[Onyx (原 Danswer)](https://github.com/onyx-dot-app/onyx) 的架构，做了便于单机学习的简化。

> 领域示例选「医药」：上传药品资料 → 自动切块/嵌入/索引 → 中文问答，回答带**可溯源引用**。
> 所有示例药品资料均为**合成数据**，仅供学习，非医学建议。

## 它能做什么

- 📥 **导入资料**：上传 PDF/TXT/MD，或抓取网页 → 异步切块、嵌入、写入向量库
- 🔎 **混合检索**：pgvector 向量召回 + Postgres 全文召回 → RRF 融合排序
- 💬 **RAG 问答**：检索增强生成，流式输出，回答末尾标注 `[n]` 引用并可展开来源
- 🤖 **Agent 模式**：模型用 `search_docs` / `calculator` 工具自主检索与计算
- 🧑‍⚕️ **多助手 (Persona)**：每个助手有自己的 system prompt 与可用工具
- ☸️ **两种部署**：本地 docker-compose；生产 Kubernetes (manifests + Helm)

## 技术栈

| 层 | 选型 | 对应 Onyx |
|---|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic | 同 |
| 异步 | Celery + Redis | 同 |
| 关系库 | PostgreSQL | 同 |
| 向量/全文 | **pgvector + tsvector + RRF** | Onyx 用 Vespa |
| LLM/嵌入 | **Ollama** (可切 Claude) | 多 provider |
| 前端 | Next.js 15 + React | 同 |
| 部署 | docker-compose / K8s / Helm | 同 |

详见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) 的逐组件对照与取舍。

## 快速开始 (本地 docker-compose)

```bash
cp .env.example .env
docker compose up -d            # 启动 postgres/redis/ollama/backend/worker/frontend
# 等待 ollama-pull 容器把模型拉好 (首次较慢, 约数 GB):
docker compose logs -f ollama-pull
# 写入医药种子数据 (persona + 示例药品资料):
docker compose run --rm backend python -m seed.seed
```

打开：
- 前端：http://localhost:3000
- 后端 Swagger：http://localhost:8000/docs

### 演示脚本

1. 进入 http://localhost:3000/chat ，助手选「医药知识助手」。
2. 问：**「二甲双胍的常用起始剂量是多少？」** → 观察流式回答 + 引用卡片。
3. 勾选 **Agent 模式**，问：**「我每天吃 3 次，每次 0.5 克二甲双胍，一天总共多少毫克？」**
   → 观察模型调用 `calculator` 工具 (会显示调用轨迹)。
4. 在「文档」页上传你自己的 PDF/MD，或抓取一个网页，看索引任务状态变为 `success`。
5. 在 http://localhost:8000/docs 直接调 `POST /search` 体验混合检索的 `vector_rank` / `keyword_rank`。

## 切换到 Claude

`.env` 里设置：
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
生成即走 Claude (见 `backend/app/llm/anthropic.py`)。嵌入仍用 Ollama。

## Kubernetes 部署

见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#kubernetes) 与 `deploy/`：

```bash
# 1) 构建镜像 (本地集群如 kind 需 load 进去)
docker build -t nexora/backend:latest ./backend
docker build -t nexora/frontend:latest --build-arg NEXT_PUBLIC_API_BASE=http://api.nexora.local ./frontend
# kind load docker-image nexora/backend:latest nexora/frontend:latest

# 2) 部署 (kustomize)
kubectl apply -k deploy/k8s/
# 触发模型拉取与迁移种子的 Job 会自动跑
kubectl -n nexora get pods

# 或用 Helm (datastores 假定已由 deploy/k8s 提供)
# helm install nexora deploy/helm -n nexora --create-namespace
```

`/etc/hosts` 添加：`127.0.0.1 nexora.local api.nexora.local`，前端访问 http://nexora.local 。

## 学习路线

强烈建议按 [`docs/LEARNING_ROADMAP.md`](docs/LEARNING_ROADMAP.md) 的阶段顺序读代码 ——
每个阶段对应一个 RAG/Agent/平台的核心概念，并指明「读哪个文件、学什么」。

## 目录结构

```
backend/   FastAPI + 索引/检索/agent/celery + alembic + seed
frontend/  Next.js (chat / documents / assistants)
deploy/    k8s manifests + helm chart
docs/      架构讲解 + 学习路线
```
