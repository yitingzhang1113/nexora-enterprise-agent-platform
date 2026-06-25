"""文档切块。

为什么要切块：嵌入模型有上下文上限，且检索希望命中「相关片段」而非整篇文档。
策略：按字符长度滑窗 + 重叠 (overlap)，尽量在段落/句子边界切分。
对应 Onyx 的 chunking 逻辑 (它更精细，按 token 与 section)。
"""
from __future__ import annotations

import re

from app.config import settings

# 优先在这些边界断开 (段落 > 换行 > 句号)
_SPLIT_RE = re.compile(r"(\n\n+|\n|。|！|？|\.|!|\?)")


def _split_sentences(text: str) -> list[str]:
    parts = _SPLIT_RE.split(text)
    # split 会把分隔符单独成项，重新拼回到前一句
    out: list[str] = []
    buf = ""
    for p in parts:
        if p is None:
            continue
        buf += p
        if _SPLIT_RE.fullmatch(p):
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return [s for s in out if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """把长文本切成带重叠的块。"""
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) <= chunk_size:
            current += sent
        else:
            if current.strip():
                chunks.append(current.strip())
            # 从上一块尾部取 overlap 个字符做衔接，保留上下文
            tail = current[-overlap:] if overlap and current else ""
            current = tail + sent
            # 单句超长时硬切
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size].strip())
                current = current[chunk_size - overlap :]
    if current.strip():
        chunks.append(current.strip())
    return chunks
