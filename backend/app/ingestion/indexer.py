"""入库 pipeline: parse→clean→split→embed→写 Postgres(chunks) + Milvus(vectors)。

chunk 的主键 id 在 Postgres 生成, Milvus 用同一 id, 保证两库对齐。
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.db import milvus
from app.db.models import Chunk, Document, IndexAttempt, IndexStatus
from app.ingestion.cleaner import clean
from app.ingestion.embedder import embed_texts
from app.ingestion.parser import RawDoc
from app.ingestion.splitter import split


def index_raw_docs(
    db: Session, raw_docs: Iterable[RawDoc], attempt: IndexAttempt, connector_id: int | None
) -> IndexAttempt:
    milvus.ensure_collection()
    attempt.status = IndexStatus.running
    db.commit()

    num_docs = 0
    num_chunks = 0
    try:
        for raw in raw_docs:
            text = clean(raw.text)
            pieces = split(text)
            if not pieces:
                continue

            doc = Document(
                connector_id=connector_id,
                source=raw.source,
                title=raw.title,
                link=raw.link,
                doc_metadata=raw.metadata,
            )
            db.add(doc)
            db.flush()

            chunk_rows = [
                Chunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=piece,
                    doc_title=raw.title,
                    source=raw.source.value,
                    link=raw.link,
                )
                for i, piece in enumerate(pieces)
            ]
            db.add_all(chunk_rows)
            db.flush()  # 拿到 chunk ids

            vectors = embed_texts(pieces)
            milvus.insert_embeddings(
                [
                    {
                        "id": c.id,
                        "embedding": vec,
                        "document_id": doc.id,
                        "chunk_index": c.chunk_index,
                    }
                    for c, vec in zip(chunk_rows, vectors)
                ]
            )
            doc.num_chunks = len(chunk_rows)
            num_docs += 1
            num_chunks += len(chunk_rows)

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
