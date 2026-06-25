"""索引管线：connector → 切块 → 嵌入 → 写库。

这是 RAG 的「写入侧」。Onyx 在 Celery worker 里跑这条管线；
我们阶段2先做成同步函数，阶段6再包成 Celery task (逻辑不变)。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector
from app.indexing.chunking import chunk_text
from app.indexing.embedding import embed_texts
from app.models import Chunk, Document, IndexAttempt, IndexStatus


def run_indexing(
    db: Session,
    connector: BaseConnector,
    connector_id: int | None = None,
    attempt: IndexAttempt | None = None,
) -> IndexAttempt:
    """执行一次索引，返回 IndexAttempt (含状态/计数)。"""
    if attempt is None:
        attempt = IndexAttempt(connector_id=connector_id or 0, status=IndexStatus.running)
        db.add(attempt)
        db.flush()
    else:
        attempt.status = IndexStatus.running
        db.flush()

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
            db.flush()  # 拿到 doc.id

            pieces = chunk_text(raw.text)
            if not pieces:
                continue
            vectors = embed_texts(pieces)
            for idx, (piece, vec) in enumerate(zip(pieces, vectors)):
                db.add(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        content=piece,
                        embedding=vec,
                    )
                )
            num_docs += 1
            num_chunks += len(pieces)

        attempt.status = IndexStatus.success
        attempt.num_docs = num_docs
        attempt.num_chunks = num_chunks
        db.commit()
    except Exception as exc:  # noqa: BLE001 —— 索引失败要记录而非崩溃
        db.rollback()
        attempt.status = IndexStatus.failed
        attempt.error = str(exc)[:2000]
        attempt.num_docs = num_docs
        attempt.num_chunks = num_chunks
        db.commit()
    return attempt
