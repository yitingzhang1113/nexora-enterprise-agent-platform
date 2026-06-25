# Nexora —— 仿 Onyx 的企业级 Agent / RAG 平台 (学习型, 医药 domain)

一个为「**边学边做**」设计的企业级 AI Agent / RAG 平台，参考开源项目
[Onyx (原 Danswer)](https://github.com/onyx-dot-app/onyx) 的架构，做了便于单机学习的简化。

> 领域示例选「医药」：上传药品资料 → 自动切块/嵌入/索引 → 中文问答，回答带**可溯源引用**。
> 所有示例药品资料均为**合成数据**，仅供学习，非医学建议。

## 它能做什么

- 📥 **导入资料**：上传 PDF/TXT/MD，或抓取网页 → 异步切块、嵌入、写入 OpenSearch
- 🔎 **混合检索**：OpenSearch kNN(向量) + BM25(关键词, `cjk` 中文分词) → RRF 融合
- 💬 **RAG 问答**：检索增强生成，流式输出，回答末尾标注 `[n]` 引用并可展开来源
- 🤖 **Agent 模式**：模型用 `search_docs` / `calculator` 工具检索与计算 (含工具调用时间线)
- 🧑‍⚕️ **多助手 (Persona)**：每个助手有自己的 system prompt 与可用工具
- 🖥️ **Onyx 风格 UI**：左侧栏(新建/历史/助手/后台) + 聊天 + 右侧来源面板 + Admin 后台，浅/深色
- ☸️ **两种部署**：本地 docker-compose；生产 Kubernetes (manifests + Helm)

> **v2 重构**：架构与 UI 进一步对齐 Onyx —— 向量库换 **OpenSearch**(走可插拔 `DocumentIndex` 接口)、
> 嵌入拆为独立 **model_server**、LLM 统一走 **LiteLLM**、后端按 Onyx 模块布局(`/api` 前缀、SearchTool 作为 RAG 核心)、
> 前端整套 Onyx 设计语言(Tailwind + Radix + Phosphor)。

## 技术栈

| 层 | 选型 | 对应 Onyx |
|---|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic (`nexora/` 模块布局, `/api` 前缀) | 同 |
| 异步 | Celery + Redis | 同 |
| 关系库 | PostgreSQL (仅元数据; chunk 不入库) | 同 |
| 向量/检索 | **OpenSearch** kNN + BM25 + RRF (`document_index` 可插拔接口) | Onyx 用 Vespa/OpenSearch |
| 嵌入 | 独立 **model_server** (代理 Ollama `bge-m3`) | 独立 model server |
| LLM | **LiteLLM** (`ollama/qwen2.5:3b`，可切 Claude/OpenAI) | LiteLLM 多 provider |
| 前端 | Next.js 15 + Tailwind + Radix + Phosphor + SWR + Zustand | 同 (Onyx 用私有 OPAL 设计系统) |
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

1. 进入 http://localhost:3000 ，左侧栏「助手」里选「医药知识助手」。
2. 问：**「二甲双胍的常用起始剂量是多少？」** → 观察流式回答 + 引用 chips，点引用展开右侧来源面板。
3. 开顶栏 **Agent 模式**，问：**「布洛芬和华法林一起用有什么风险？请查资料」**
   → 观察 `search_docs` 工具调用时间线。
4. 进「管理后台」→ 文档 / 连接器：上传 PDF/MD 或抓取网页，看索引任务状态变 `success`。
5. 直接调 `POST /api/search`(body `{"query":"二甲双胍的起始剂量"}`)体验混合检索的
   `vector_rank` / `keyword_rank`(中文关键词现在也会命中)。

## 本地实测说明 & 已知点

已在 macOS (Docker Desktop, 分配 7.7GB 内存) 完整跑通：上传/索引、混合检索、流式 RAG 问答(带引用)、Agent 工具调用。两点经验：

- **模型与内存**：llama3.1 (8B) 权重约 5GB，在 ~8GB 的 Docker 内存下会被 OOM 杀掉
  (`llama-server ... signal: killed`)。因此默认生成模型改为 **qwen2.5:3b**(中文强、~2GB)。
  Docker 内存 ≥12GB 时可在 `.env` 把 `GEN_MODEL` 换回 `llama3.1`。
- **中文关键词检索**：Postgres `simple` 分词器不切中文词，所以纯中文查询时「关键词」一路
  基本不命中(`keyword_rank=None`)，**向量检索**承担主要召回。要让中文 BM25 生效需装中文分词
  扩展 (如 `zhparser` / `pg_jieba`) —— 这是 §进阶方向之一。英文/术语/数字的关键词检索正常。

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
