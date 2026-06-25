# 架构讲解 (Onyx ↔ Nexora)

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
