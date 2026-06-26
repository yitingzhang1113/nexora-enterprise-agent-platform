"""重排 (rerank)。默认用便宜模型做列表式打分; rerank_mode=none 则跳过。"""
from __future__ import annotations

import re

from app.config import settings
from app.rag.retrievers import RetrievedChunk


def rerank(query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    if settings.rerank_mode == "none" or len(chunks) <= 1:
        return chunks

    from app.models.llm_router import get_fast_llm

    snippets = "\n".join(
        f"[{i}] {c.content[:200]}" for i, c in enumerate(chunks)
    )
    prompt = (
        "下面是若干候选资料片段, 请按与【问题】的相关性从高到低排序, "
        "只输出编号, 用逗号分隔 (例如 2,0,1)。\n\n"
        f"【问题】{query}\n\n【候选】\n{snippets}\n\n排序:"
    )
    try:
        resp = get_fast_llm().invoke(prompt)
        text = getattr(resp, "content", "") or ""
    except Exception:  # noqa: BLE001
        return chunks

    order = [int(x) for x in re.findall(r"\d+", text) if int(x) < len(chunks)]
    seen: set[int] = set()
    out: list[RetrievedChunk] = []
    for idx in order:
        if idx not in seen:
            seen.add(idx)
            out.append(chunks[idx])
    for i, c in enumerate(chunks):
        if i not in seen:
            out.append(c)
    return out
