"""切块算法 (按句/段边界滑窗 + 重叠)。"""
from __future__ import annotations

import re

from app.config import settings

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


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    size = size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    sentences = _split_sentences(text)
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        if len(cur) + len(s) <= size:
            cur += s
        else:
            if cur.strip():
                chunks.append(cur.strip())
            tail = cur[-overlap:] if overlap and cur else ""
            cur = tail + s
            while len(cur) > size:
                chunks.append(cur[:size].strip())
                cur = cur[size - overlap :]
    if cur.strip():
        chunks.append(cur.strip())
    return chunks
