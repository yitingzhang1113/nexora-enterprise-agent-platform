"""RAG 编排：检索 → 拼 context → 构造 prompt → (由调用方)生成。

把「检索」与「生成」分开，方便：
- 普通 RAG：先检索再一次性生成 (本文件)
- Agentic：让模型用 search_docs 工具自行决定检索 (见 app/agent/)
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.search.hybrid import FusedHit, hybrid_search

DEFAULT_SYSTEM = (
    "你是一个严谨的知识助手。请只依据提供的【参考资料】回答用户问题，"
    "并在句末用 [n] 标注引用的资料编号。若资料中没有答案，请明确说明你不知道，"
    "不要编造。"
)


def retrieve(db: Session, query: str, top_k: int | None = None) -> list[FusedHit]:
    return hybrid_search(db, query, top_k=top_k or settings.top_k)


def format_context(hits: list[FusedHit]) -> tuple[str, list[dict]]:
    """把检索结果拼成 context 文本 + 引用列表。"""
    citations: list[dict] = []
    blocks: list[str] = []
    for i, hit in enumerate(hits, start=1):
        chunk = hit.chunk
        title = chunk.document.title if chunk.document else "未知文档"
        blocks.append(f"[{i}] (来源: {title})\n{chunk.content}")
        citations.append(
            {
                "n": i,
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": title,
                "content": chunk.content,
            }
        )
    return "\n\n".join(blocks), citations


def build_rag_messages(
    query: str,
    context: str,
    history: list[dict] | None = None,
) -> list[dict]:
    """构造发给 LLM 的 messages (不含 system，由调用方传 system)。"""
    history = history or []
    user_content = (
        f"【参考资料】\n{context}\n\n"
        f"【问题】\n{query}\n\n"
        "请基于参考资料作答，并标注引用编号 [n]。"
    )
    return [*history, {"role": "user", "content": user_content}]
