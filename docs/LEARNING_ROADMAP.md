# 学习路线 (按阶段读代码)

建议按顺序读 + 跑。每阶段给出「核心问题、读哪些文件、动手验证」。
配合 `docs/ARCHITECTURE.md` 的对照表一起看。

---

## 阶段 1 · 后端骨架 + 数据层
**核心问题**：一个 RAG 平台需要哪些表？怎么用 SQLAlchemy + Alembic 管理？

- 读：`app/config.py`（配置如何集中注入）、`app/db/base.py`（engine/session）、
  `app/models/__init__.py`（全部表 + pgvector 列 + 全文列 + 索引）
- 重点：`Chunk.embedding`(Vector) 与 `Chunk.tsv`(generated tsvector) 两列，是检索的基石
- 验证：`alembic upgrade head` 后看 `chunks` 表结构与 HNSW/GIN 索引

## 阶段 2 · 索引管线
**核心问题**：文档怎么变成「可检索的向量」？为什么要切块？

- 读：`app/connectors/base.py`（统一接口）、`connectors/file_upload.py`、
  `app/indexing/chunking.py`（切块 + 重叠）、`embedding.py`（Ollama 嵌入）、`pipeline.py`
- 重点：切块的 size/overlap 取舍；嵌入维度必须等于 `EMBED_DIM`
- 验证：`POST /documents/upload` 上传一个 md，看 `documents`/`chunks` 行数

## 阶段 3 · 混合检索
**核心问题**：向量检索 vs 关键词检索各擅长什么？如何融合？

- 读：`app/search/vector.py`、`keyword.py`、`hybrid.py`（RRF）
- 重点：RRF 为什么只用 rank 不用原始分；`vector_rank`/`keyword_rank` 的含义
- 验证：`POST /search` 用一个语义词和一个精确术语，对比两路命中差异

## 阶段 4 · RAG 聊天 (流式 + 引用)
**核心问题**：怎么把检索结果喂给 LLM 并让回答可溯源？

- 读：`app/chat/rag.py`（context 拼装 + 引用编号）、`app/api/chat.py`（SSE 流式）、
  `app/llm/ollama.py`（stream_chat）
- 重点：system prompt 要求「只依据资料 + 标注 [n]」；SSE 的 meta/token/done 事件
- 验证：前端 `/chat` 普通模式提问，观察流式与引用卡片

## 阶段 5 · Agent 层 + Persona
**核心问题**：让模型自己决定检索/计算，与「先检索后生成」有何不同？

- 读：`app/agent/tools.py`（工具 schema + executor，含安全的 calculator）、
  `app/agent/loop.py`（ReAct 循环）、`app/api/personas.py`
- 重点：tool-calling 消息格式；引用跨多次工具调用的合并去重
- 验证：前端勾选「Agent 模式」，问需要计算的剂量问题，看工具调用轨迹

## 阶段 6 · 异步索引 (Celery)
**核心问题**：为什么索引要放后台？同步逻辑如何平滑搬到 worker？

- 读：`app/tasks/celery_app.py`、`indexing_tasks.py`（对比它与 `pipeline.run_indexing` 是同一逻辑）
- 重点：上传接口立即返回 + `IndexAttempt` 状态轮询；web connector 抓取
- 验证：上传大文件或抓网页，前端「文档」页看状态 pending→running→success

## 阶段 7 · 前端
**核心问题**：如何在浏览器消费 SSE (POST) 并增量渲染？

- 读：`frontend/src/lib/api.ts`（手写 SSE 解析）、`app/chat/page.tsx`、
  `documents/page.tsx`、`assistants/page.tsx`
- 重点：`chatStream` 用 fetch+ReadableStream 解析 SSE（EventSource 不支持 POST）
- 验证：三个页面都能正常交互

## 阶段 8 · 医药 domain 种子
**核心问题**：如何把通用平台「实例化」到一个领域？

- 读：`backend/seed/seed.py`、`seed/docs/*.md`
- 重点：领域化 = 专门的 system prompt (Persona) + 领域语料，不改平台代码
- 验证：`python -m seed.seed` 后用「医药知识助手」问答

## 阶段 9 · Kubernetes
**核心问题**：把这套东西可靠地跑在集群上要哪些资源对象？

- 读：`deploy/k8s/*.yaml`（按编号顺序）、`deploy/helm/`
- 重点：有状态(StatefulSet+PVC) vs 无状态(Deployment)；ConfigMap/Secret；Job 做迁移；探针
- 验证：`kubectl apply -k deploy/k8s/`，`kubectl -n nexora get pods` 全部 Ready

---

## 下一步 (做真正企业级平台时的进阶方向)

1. **检索后端**：pgvector → Vespa/OpenSearch/Qdrant，支持分片与多信号排序
2. **权限**：多用户 + 文档级 ACL (Onyx 的核心企业能力)
3. **更多连接器**：Google Drive / Confluence / Slack，含增量同步与去重
4. **对象存储**：MinIO/S3 存原文件，backend 与 worker 共享
5. **可观测性**：结构化日志、指标、索引/检索质量评估 (RAG eval)
6. **Agent 增强**：多步规划、子查询分解、引用校验 (anti-hallucination)
