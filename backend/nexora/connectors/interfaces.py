"""Connector 抽象 (对应 onyx/connectors)。新增数据源 = 实现 load()。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

from nexora.db.models import SourceType


@dataclass
class RawDocument:
    title: str
    text: str
    source: SourceType
    link: str | None = None
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    source: SourceType

    @abstractmethod
    def load(self) -> Iterator[RawDocument]:
        raise NotImplementedError
