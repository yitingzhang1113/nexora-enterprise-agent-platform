# 架构讲解

> **v3 更新 (当前)**:已转向「Python 版 Ragent AI」—— 后端核心是 **LangGraph Agent 工作流**
> (`backend/app/graph`),技术栈 FastAPI + LangGraph + LangChain + Milvus + MCP + Langfuse,领域改为**通用**。
> 流程:`load_memory → rewrite_query → classify_intent → route(知识RAG / MCP工具 / 澄清) → rerank → build_prompt → generate → save_trace+save_memory`。
> 检索 = Milvus dense + BM25(jieba) RRF;LLM 走 LangChain(llm_router 选模型 + 熔断);
> 可观测 = Langfuse 节点级 trace。后端目录:`api/graph/rag/intent/models/tools/memory/ingestion/observability/db`。
> 下方 v1/v2 内容作为演进对照保留(原理相通:写入侧索引、读取侧检索+生成的骨架不变)。

---

# (历史) 架构讲解 (Onyx ↔ Nexora)

> **v2 更新**：为更贴近真实 Onyx，已做以下重构(本文下方部分小节仍以 v1 视角描述原理，但实际实现以此处为准)：
> - 后端包从 `app/` 重排为 **`nexora/`** 模块布局，业务路由统一挂 **`/api`** 前缀(对齐 `onyx/server`)。
> - 向量库由 pgvector 换成 **OpenSearch**(kNN + BM25 + 应用层 RRF)，走可插拔 **`document_index` 接口 + factory**；
>   `content`/`title` 用 `cjk` 分析器，**中文关键词检索可用**(修复 v1 痛点)。chunk **不再入 Postgres**(只存 OpenSearch)。
> - 嵌入拆为**独立 `model_server`**(FastAPI，默认代理 Ollama `bge-m3`)，对齐 Onyx 的 model server 边界。
> - LLM 统一走 **LiteLLM**(`ollama/qwen2.5:3b` / `anthropic/...` / `openai/...`)。
> - RAG 核心是 **`SearchTool`**；Agent 走工具循环(`chat/llm_loop.py`)。
> - 前端整套 **Onyx 设计语言**：左侧栏 + 聊天 + 右侧来源面板 + Admin 后台，Tailwind + Radix + Phosphor + 浅/深色。
>
> 下面的对照表与 §3 用于理解「为什么这样选」，pgvector 一节作为历史对照保留。



本文把 Onyx 的真实架构与本项目逐组件对照，并解释「我们为什么这样简化」。
目标是让你既能跑通 MVP，又能理解将来做真正企业级平台时该如何取舍。

## 1. 全局数据流

```
                    ┌─────────────┐
   上传/抓取  ──────▶│  Connector  │  (file_upload / web)
                    └──────┬──────┘
                           ▼
                 ┌───────────────────┐     Celery 任务 (异步)
                 │   索引管线 pipeline │ ◀── worker 进程执行
                 │  切块→嵌入→写库     │
                 └─────────┬─────────┘
                           ▼
        ┌──────────────────────────────────┐
        │ Postgres: documents / chunks       │
        │  chunks.embedding (pgvector)       │  ← 向量检索
        │  chunks.tsv (tsvector, GIN)        │  ← 关键词检索
        └──────────────────┬─────────────────┘
                           ▼
   提问 ──▶ 混合检索 (vector + keyword → RRF) ──▶ 拼 context
                           ▼
        ┌─────────── 两种生成路径 ───────────┐
        │ RAG:   检索→prompt→LLM 流式 (SSE)   │
        │ Agent: LLM 自主调用 search_docs/... │
        └────────────────┬───────────────────┘
                         ▼
                 回答 + 引用 [n]  →  前端渲染
```

写入侧 (索引) 与读取侧 (检索/生成) 解耦，是所有 RAG 系统的通用骨架。

## 2. 逐组件对照

| 子系统 | Onyx 真实做法 | 本项目 (Nexora) | 关键取舍 |
|---|---|---|---|
| API | FastAPI | `backend/app/main.py` + `app/api/*` | 一致 |
| ORM/迁移 | SQLAlchemy + Alembic | `app/models`, `alembic/` | 一致 |
| 向量+全文 | **Vespa** (或 OpenSearch) | **pgvector + tsvector + RRF** (`app/search/`) | 见 §3 |
| 嵌入服务 | 独立 model server | Ollama `/api/embeddings` (`app/indexing/embedding.py`) | 解耦但更轻 |
| 生成 LLM | 多 provider 抽象 | `app/llm/` (ollama 默认 / anthropic 占位) | 接口一致 |
| 异步任务 | Celery + Redis (多 worker 池) | Celery + Redis (单池) (`app/tasks/`) | 概念一致 |
| 连接器 | 50+ | `BaseConnector` + file_upload + web | 抽象一致 |
| 助手 | Persona/Assistant | `Persona` 表 (`app/models`) | 一致 |
| Agent | Agentic RAG + tool use | `app/agent/` (ReAct 简化) | 概念一致 |
| Blob | MinIO | 本地卷 (compose) / emptyDir (k8s) | MVP 简化 |
| 前端 | Next.js | Next.js (`frontend/`) | 一致 |

## 3. 为什么用 pgvector 而不是 Vespa？

Onyx 用 Vespa 是因为要支撑**大规模**文档、**复杂排序信号** (BM25 + 向量 + 自定义 rank profile)、
以及租户隔离。代价是 Vespa 运维复杂、资源重。

学习阶段我们用 **一个 Postgres** 同时承担：关系数据 + 向量 (pgvector) + 全文 (tsvector)。
好处：

- 单一依赖，`docker compose up` 即可，无需额外搜索引擎
- 「混合检索」原理可完整复现：我们手写 **RRF (Reciprocal Rank Fusion)** 把
  向量排名与关键词排名融合 (`app/search/hybrid.py`)，这正是 Vespa 内部混合排序的思想

什么时候该上 Vespa/OpenSearch/专用向量库 (Qdrant/Weaviate)？
当数据量到千万级 chunk、需要分片/副本、或需要复杂的多信号排序与过滤时。
本项目的 `app/search/` 是干净的抽象层，将来替换检索后端只改这一层。

## 4. 混合检索与 RRF

- **向量检索** (`vector.py`)：`embedding <=> query_vec` 余弦距离，越小越相似 (HNSW 索引)。
- **关键词检索** (`keyword.py`)：`to_tsvector @@ plainto_tsquery` + `ts_rank` (GIN 索引)。
- **融合** (`hybrid.py`)：对每个 chunk，`score = Σ 1/(k + rank_i)`。
  RRF 只看排名不看分数量纲，因此能公平合并两种不可比的分数。

为什么要混合？向量擅长语义近似 (同义改写)，关键词擅长精确术语 (药名、剂量数字)。
医药场景两者都重要 —— 这也是企业搜索普遍采用混合检索的原因。

> **中文 FTS 注意**：Postgres `simple` 分词器按空格/标点切词，不切中文，
> 故纯中文查询时关键词一路常常不命中 (`keyword_rank=None`)，向量路承担主要召回。
> 生产中文场景应安装中文分词扩展 (`zhparser` / `pg_jieba`) 再建 tsvector。

## 5. LLM provider 抽象

`app/llm/base.py` 定义最小接口 (`stream_chat` / `chat` / `chat_with_tools`)。
`get_llm()` 工厂按 `LLM_PROVIDER` 返回实现。换厂商 = 新增一个适配类 + 改配置，
业务代码 (rag/agent) 完全不变。这就是 Onyx 支持几十种模型的方式。

## 6. 同步 → 异步 (为什么要 Celery)

索引一篇文档要「解析 + 切块 + 逐块嵌入」，嵌入是网络/算力密集、可能很慢。
若在 HTTP 请求里同步做，用户上传时会长时间卡住、易超时。

解决：上传接口只负责**落盘 + 建 IndexAttempt + 投递任务**，立即返回；
真正的索引在 **Celery worker** 进程里跑 (`app/tasks/indexing_tasks.py`)，
前端轮询 `IndexAttempt.status` 看进度。注意：worker 里调用的
`run_indexing()` 与同步版**完全是同一段逻辑** —— 异步化只是换了执行进程。

## 7. Agent 循环 (Agentic RAG)

普通 RAG 是「先检索后生成」；Agent 让模型自己决定**何时**检索、检索**什么**、检索**几次**。
`app/agent/loop.py` 实现一个 ReAct 简化循环：

1. 把工具 schema 给模型
2. 模型要么直接答，要么请求调用工具 (`search_docs` / `calculator`)
3. 执行工具，结果作为 `tool` 消息回灌
4. 回到 2，直到模型给出最终答案或达步数上限

`search_docs` 把每次命中的引用累加，最后统一去重编号。

## 8. Kubernetes {#kubernetes}

`deploy/k8s/` (kustomize) 体现「有状态 vs 无状态」工作负载划分：

- **StatefulSet + PVC**：`postgres` (数据)、`ollama` (模型缓存) —— 需要稳定存储
- **Deployment**：`backend`、`worker`、`frontend`、`redis` —— 可随意重启/扩缩
- **ConfigMap / Secret**：配置与镜像解耦 (同一镜像多环境)
- **Job**：`migrate-seed` (Alembic + 种子)、`ollama-pull` (拉模型) —— 一次性运维动作
- **探针**：liveness/readiness 指向 `/health`
- **Ingress**：`nexora.local` → 前端，`api.nexora.local` → 后端 (SSE 需关 proxy buffering)

已知简化点 (生产需改)：
- 文件上传用 `emptyDir`，backend 与 worker **不共享** 上传文件 → 生产应用 RWX PVC 或
  对象存储 (对应 Onyx 的 MinIO)。**web connector 与 seed 不受影响**，可正常演示。
- 单副本、无 HPA、无 NetworkPolicy、密码明文写在 Secret 的 stringData。

`deploy/helm/` 是应用层 chart (backend/worker/frontend + config/ingress + migrate Job)，
数据存储假定由 `deploy/k8s` 或外部提供 —— 体现「应用 chart 与基础设施分离」的实践。
