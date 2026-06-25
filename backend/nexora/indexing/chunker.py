"""文档切块 (对应 onyx/indexing/chunker.py)。

按字符长度滑窗 + 重叠, 尽量在段落/句子边界切分。
"""
from __future__ import annotations

import re

from nexora.configs.app_configs import settings

_SPLIT_RE = re.compile(r"(\n\n+|\n|。|！|？|\.|!|\?)")


def _split_sentences(text: str) -> list[str]:
    parts = _SPLIT_RE.split(text)
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
    text: str, chunk_size: int | None = None, overlap: int | None = None
) -> list[str]:
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
            tail = current[-overlap:] if overlap and current else ""
            current = tail + sent
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size].strip())
                current = current[chunk_size - overlap :]
    if current.strip():
        chunks.append(current.strip())
    return chunks
