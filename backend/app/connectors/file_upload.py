"""文件上传连接器：解析 pdf / txt / md。"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from pypdf import PdfReader

from app.connectors.base import BaseConnector, RawDocument
from app.models import SourceType


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class FileUploadConnector(BaseConnector):
    source = SourceType.file_upload

    def __init__(self, file_paths: list[str], titles: list[str] | None = None) -> None:
        self.file_paths = [Path(p) for p in file_paths]
        self.titles = titles or [p.name for p in self.file_paths]

    def load(self) -> Iterator[RawDocument]:
        for path, title in zip(self.file_paths, self.titles):
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                text = _read_pdf(path)
            elif suffix in {".txt", ".md", ".markdown"}:
                text = _read_text(path)
            else:
                # 兜底当纯文本读
                text = _read_text(path)
            if text.strip():
                yield RawDocument(
                    title=title,
                    text=text,
                    source=self.source,
                    link=str(path.name),
                    metadata={"filename": path.name, "filetype": suffix},
                )
