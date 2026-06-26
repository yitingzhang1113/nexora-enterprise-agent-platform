"""文档解析: 文件 (pdf/txt/md) 与网页 → 原始文本。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.db.models import SourceType


@dataclass
class RawDoc:
    title: str
    text: str
    source: SourceType
    link: str | None = None
    metadata: dict = field(default_factory=dict)


def parse_file(path: str, title: str | None = None) -> RawDoc:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(p))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = p.read_text(encoding="utf-8", errors="ignore")
    return RawDoc(
        title=title or p.name,
        text=text,
        source=SourceType.file_upload,
        link=p.name,
        metadata={"filename": p.name, "filetype": suffix},
    )


def parse_url(url: str) -> RawDoc:
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string if soup.title else url) or url
    text = "\n".join(
        line.strip() for line in soup.get_text("\n").splitlines() if line.strip()
    )
    return RawDoc(
        title=title.strip()[:512],
        text=text,
        source=SourceType.web,
        link=url,
        metadata={"url": url},
    )
