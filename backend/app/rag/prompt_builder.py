"""Prompt 组装 (system + context + history + query) + 引用结构。"""
from __future__ import annotations

from app.rag.retrievers import RetrievedChunk

DEFAULT_SYSTEM = (
    "你是一个严谨的企业知识助手。请只依据【参考资料】回答用户问题, "
    "并在句末用 [n] 标注引用的资料编号。若资料中没有答案, 请如实说明你不知道, 不要编造。"
)


def build_context(chunks: list[RetrievedChunk]) -> tuple[str, list[dict]]:
    citations: list[dict] = []
    blocks: list[str] = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (来源: {c.doc_title})\n{c.content}")
        citations.append(
            {
                "n": i,
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_title": c.doc_title,
                "content": c.content,
                "link": c.link,
            }
        )
    return "\n\n".join(blocks), citations


def build_messages(query: str, context: str, history: list[dict] | None = None) -> list[dict]:
    history = history or []
    user = (
        f"【参考资料】\n{context}\n\n【问题】\n{query}\n\n"
        "请基于参考资料作答, 并标注引用编号 [n]。"
    )
    return [*history, {"role": "user", "content": user}]
