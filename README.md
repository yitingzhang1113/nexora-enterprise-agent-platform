# Nexora Ops Agent

**A production-style multi-tool AI agent platform for e-commerce operations** — built with
FastAPI, LangGraph, LangChain, MCP tools, Milvus, Redis, Postgres, Slack integration and Langfuse observability.

面向电商运营场景的企业级多工具 AI Agent 平台:结合知识库政策与订单/库存/退货/工单等业务数据,
自动**分析异常商品、判断退款、创建工单、Slack 通知**,并对高风险动作走**人工审批闭环**。

> 示例数据为合成数据,仅供学习/演示。

## 生产场景 (Production scenario)

运营人员可以直接问:
- 「分析最近 7 天表现异常的商品,风险高就建工单并通知 Slack」
- 「NX-AIR-FRYER-001 的退货率是多少?原因是什么?」
- 「订单 10086 退款 $300 能退吗?需要审批吗?」

Agent 自动规划并**并行调用工具**,校验结果,对高风险操作(退款 > $200、暂停广告)**挂起人工审批**,
通过后才执行并通知运营组。

## 架构 (Architecture)

```
React Chat / Admin
      ↓
FastAPI API Gateway  (SSE 流式 / Auth / Redis 限流)
      ↓
LangGraph Agent Workflow (10 节点):
  load_memory → rewrite_query → classify_intent → plan_tasks → route
    → parallel_tool_calls (asyncio.gather)
    → validate_result (风险标记)
    → human_approval_if_needed (高风险→审批队列)
    → execute_action (建工单/发 Slack)
    → final_response (LLM 汇总, 带引用)
    → save_trace (Langfuse) + save_memory (Redis/Postgres)
```

## 技术栈

| 层 | 选型 |
|---|---|
| API 网关 | FastAPI + SSE + Redis 限流 |
| Agent 编排 | **LangGraph** StateGraph (10 节点 + 条件路由) |
| LLM | **LangChain** chat models, llm_router 按任务选模型 (默认 Ollama `qwen2.5:3b`, 可切 Claude/OpenAI) + 熔断/健康检查 |
| 检索 | **Milvus** (dense, HNSW/COSINE) + **BM25/jieba** (中文关键词) → RRF 融合 |
| 工具 | **MCP** 客户端 + 10 个工具 (真实查 Postgres) + 内置 Slack mock(可接真 Webhook) |
| 记忆 | 短期 (Redis) + 滚动摘要 + 历史 (Postgres) |
| 可观测 | **Langfuse** 节点级 trace + 本地 trace 兜底 |
| 缓存 | Redis (query 嵌入 / 命中率统计) |
| 前端 | Next.js 15 + Tailwind + Radix + Phosphor + SWR + Zustand |
| 异步 | Celery + Redis |
| 部署 | docker-compose / K8s / Helm |

## MCP 工具 (10)

`query_sales_data · query_inventory · query_returns · query_support_tickets · retrieve_policy`(只读)
`create_ops_ticket · send_slack_message · pause_campaign · evaluate_refund · approve_refund_mock`(动作)

## 数据规模 (mock)

products 200 · customers 1000 · orders 5250 · order_items 10226 · returns 546 · support_tickets 800 · campaigns 50;
预置异常商品 **NX-AIR-FRYER-001**(退货率 18.8%、库存 12<安全线 30、销量↓~47%、broken handle 投诉)。
政策知识库 7 篇(退款/物流/库存/促销/客服/风控/供应商)。

## 实测指标 (本地, qwen2.5:3b)

| 指标 | 结果 |
|---|---|
| 单元/集成测试 | **18 passed** (`pytest`) |
| Intent Accuracy (eval) | **100%** (5/5) |
| Tool-call Hit (eval) | **100%** (2/2) |
| RAG Recall@3 (eval) | **100%** (3/3) |
| 重复查询检索 (Redis 嵌入缓存) | **2431ms → 18ms (~134×, 99%↓)** |
| 并行工具执行 | `asyncio.gather` 编排;收益随工具 I/O 延迟增大(本地 Postgres 查询为毫秒级,收益有限,远端 API/LLM 工具收益显著) |

> 诚实说明:本地 Postgres 工具是毫秒级,**并行的收益主要体现在 I/O/LLM 密集型工具**;真正可量化的优化是**嵌入缓存**(>100×)。

## 快速开始

> 内存提示:Milvus + Langfuse + Ollama 较吃内存,建议 Docker 分配 **≥ 10GB**。

```bash
cp .env.example .env
docker compose up -d
docker compose logs -f ollama-pull                      # 等模型 (qwen2.5:3b + bge-m3)
docker compose run --rm backend python -m app.seed.seed # 灌电商数据 + 政策知识库
```

入口:前端 http://localhost:3000 · Swagger http://localhost:8000/docs · Langfuse http://localhost:3001 (admin@nexora.local / nexora123)

### 演示脚本

1. **异常分析闭环**:聊天问「分析最近 7 天表现异常的商品,风险高就建工单并通知 Slack」
   → 看流程时间线(规划→并行工具→校验→审批→执行)→ Admin「运营工单」「Slack 通知」出现记录,「审批队列」出现待审批(暂停广告)。
2. **退款审批闭环**:问「订单 10086 退款 $300,理由 broken handle,能退吗?」
   → 识别 >$200 需审批 → Admin「审批队列」点「通过」→ 自动执行退款 + Slack 通知。
3. Admin:「工具注册表」「Trace」「系统状态」(模型路由/熔断/缓存命中)「业务数据」。

## 用真实数据测 (可选)

- **知识库**:直接上传你自己的真实文档 (PDF/MD),或在「知识库」抓取真实网页 (web connector 带浏览器 UA)。
- **交易数据**:导入 **UCI Online Retail II** 真实零售交易 (含真实退货/日期/客户),日期会自动重定基到"现在":
  ```bash
  docker compose exec backend python -m app.seed.import_uci
  ```
  导入后业务表为真实数据 (~3000 商品 / 4000 订单 / 10万+ 明细 / 2000+ 退货);
  库存/广告/工单按规则合成;并保留演示用异常 SKU `NX-AIR-FRYER-001` 与订单 `10086`。
  看板、异常检测、退款判定即跑在真实交易数据上。

## 测试 / Eval / 压测

```bash
docker compose exec backend python -m pytest tests/ -q   # 单元+集成
docker compose exec backend python -m eval.run_eval      # Intent/Tool/Recall 指标
locust -f loadtest/locustfile.py --host http://localhost:8000   # 压测 (本地按需)
```

## Resume bullets (English)

- Built a production-style e-commerce **ops AI agent** (FastAPI + **LangGraph** + LangChain + **Milvus** + **MCP** + **Langfuse**) orchestrating a **10-node workflow**: memory → query-rewrite → intent → **plan** → **parallel tools** → validate → **human approval** → execute → respond.
- Implemented **multi-retriever RAG** (Milvus dense + BM25/jieba with **RRF** fusion) with inline citations — **100% Recall@3** on the eval set.
- Added **Redis-cached query embeddings**, cutting repeated-retrieval latency **~134× (2.4s → 18ms)**.
- Designed an **async human-in-the-loop approval queue** gating high-risk actions (refunds > $200, ad pauses) with execute-on-approve + Slack notification.
- Exposed **10 MCP tools** over real Postgres business data; per-node tracing to Langfuse; pluggable LLM router with circuit breaker.

## 演进历史

v1 pgvector → v2 OpenSearch + Onyx 风格 UI → v3 LangGraph + Milvus + MCP + Langfuse → **v4 (当前) 电商运营 Ops Agent (规划/并行/校验/审批/执行闭环)**。

## Kubernetes

`deploy/k8s` (kustomize) + `deploy/helm`:postgres / redis / milvus(etcd+minio) / ollama / model-server /
backend / worker / frontend / langfuse + migrate-seed Job + Ingress。
