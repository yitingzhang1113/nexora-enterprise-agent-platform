"""Connector 抽象基类。

Onyx 的精髓之一：所有数据源 (50+) 都实现统一接口，索引管线只认接口。
新增数据源 = 写一个 `BaseConnector` 子类，实现 `load()`。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field

from app.models import SourceType


@dataclass
class RawDocument:
    """连接器产出的「原始文档」(尚未切块/嵌入)。"""

    title: str
    text: str
    source: SourceType
    link: str | None = None
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    source: SourceType

    @abstractmethod
    def load(self) -> Iterator[RawDocument]:
        """产出一批 RawDocument。"""
        raise NotImplementedError
