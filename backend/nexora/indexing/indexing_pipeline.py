"""索引管线 (对应 onyx/indexing/indexing_pipeline.py)。

connector.load() → 写 Document 元数据(Postgres) → 切块 → 嵌入(model_server)
→ 写入向量库(OpenSearch)。chunk 内容只进 OpenSearch, 不进 Postgres。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from nexora.connectors.interfaces import BaseConnector
from nexora.document_index.factory import get_default_document_index
from nexora.document_index.models import IndexChunk
from nexora.indexing.chunker import chunk_text
from nexora.indexing.embedder import embed_texts
from nexora.db.models import Document, IndexAttempt, IndexStatus


def run_indexing(
    db: Session,
    connector: BaseConnector,
    connector_id: int | None,
    attempt: IndexAttempt,
) -> IndexAttempt:
    index = get_default_document_index()
    index.ensure_setup()

    attempt.status = IndexStatus.running
    db.commit()

    num_docs = 0
    num_chunks = 0
    try:
        for raw in connector.load():
            doc = Document(
                connector_id=connector_id,
                source=raw.source,
                title=raw.title,
                link=raw.link,
                doc_metadata=raw.metadata,
            )
            db.add(doc)
            db.flush()  # 拿 doc.id

            pieces = chunk_text(raw.text)
            if not pieces:
                continue
            vectors = embed_texts(pieces)
            index_chunks = [
                IndexChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    title=raw.title,
                    content=piece,
                    source=raw.source.value,
                    link=raw.link,
                    embedding=vec,
                )
                for i, (piece, vec) in enumerate(zip(pieces, vectors))
            ]
            index.index(index_chunks)
            doc.num_chunks = len(index_chunks)
            num_docs += 1
            num_chunks += len(index_chunks)

        attempt.status = IndexStatus.success
        attempt.num_docs = num_docs
        attempt.num_chunks = num_chunks
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        attempt.status = IndexStatus.failed
        attempt.error = str(exc)[:2000]
        attempt.num_docs = num_docs
        attempt.num_chunks = num_chunks
        db.commit()
    return attempt
