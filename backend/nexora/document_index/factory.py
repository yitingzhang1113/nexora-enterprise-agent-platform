"""DocumentIndex 工厂 (对应 onyx/document_index/factory.py)。

当前只接 OpenSearch。要加 Vespa/Qdrant: 在此按配置返回不同实现即可。
"""
from __future__ import annotations

from nexora.document_index.interfaces import DocumentIndex
from nexora.document_index.opensearch.index import OpenSearchDocumentIndex


def get_default_document_index() -> DocumentIndex:
    return OpenSearchDocumentIndex()
