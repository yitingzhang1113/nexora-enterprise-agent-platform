"""网页连接器：抓取 URL → 提取正文文本。"""
from __future__ import annotations

from collections.abc import Iterator

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, RawDocument
from app.models import SourceType


class WebConnector(BaseConnector):
    source = SourceType.web

    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    def load(self) -> Iterator[RawDocument]:
        for url in self.urls:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # 去掉脚本/样式
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            title = (soup.title.string if soup.title else url) or url
            text = "\n".join(
                line.strip()
                for line in soup.get_text("\n").splitlines()
                if line.strip()
            )
            if text.strip():
                yield RawDocument(
                    title=title.strip()[:512],
                    text=text,
                    source=self.source,
                    link=url,
                    metadata={"url": url},
                )
