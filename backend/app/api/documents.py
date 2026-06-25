"""文档上传与列表。"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models import Chunk, Connector, Document, IndexAttempt, SourceType
from app.schemas import DocumentOut, IndexAttemptOut
from app.tasks.indexing_tasks import index_files_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=IndexAttemptOut)
def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> IndexAttempt:
    """上传一个或多个文件 → 落盘 → 创建索引任务 (Celery 异步)。"""
    os.makedirs(settings.upload_dir, exist_ok=True)

    connector = Connector(
        name=f"upload-{uuid.uuid4().hex[:8]}",
        source=SourceType.file_upload,
        config={"filenames": [f.filename for f in files]},
    )
    db.add(connector)
    db.flush()

    saved_paths: list[str] = []
    titles: list[str] = []
    for f in files:
        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        dest = os.path.join(settings.upload_dir, safe_name)
        with open(dest, "wb") as out:
            out.write(f.file.read())
        saved_paths.append(dest)
        titles.append(f.filename or safe_name)

    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # 异步索引 (worker 执行)。若无 worker，可走 /documents/upload?sync=1 的同步版本。
    index_files_task.delay(attempt.id, saved_paths, titles)
    return attempt


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentOut]:
    chunk_count = (
        select(Chunk.document_id, func.count(Chunk.id).label("cnt"))
        .group_by(Chunk.document_id)
        .subquery()
    )
    rows = db.execute(
        select(Document, func.coalesce(chunk_count.c.cnt, 0))
        .outerjoin(chunk_count, Document.id == chunk_count.c.document_id)
        .order_by(Document.id.desc())
    ).all()
    out: list[DocumentOut] = []
    for doc, cnt in rows:
        out.append(
            DocumentOut(
                id=doc.id,
                title=doc.title,
                source=doc.source.value,
                link=doc.link,
                num_chunks=int(cnt),
                created_at=doc.created_at,
            )
        )
    return out
