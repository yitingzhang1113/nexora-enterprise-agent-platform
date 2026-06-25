"""文档上传与列表 (对应 onyx/server/documents)。"""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexora.configs.app_configs import settings
from nexora.db.engine import get_session
from nexora.db.models import Connector, Document, IndexAttempt, SourceType
from nexora.tasks.indexing_tasks import index_files_task


class DocumentOut(BaseModel):
    id: int
    title: str
    source: str
    link: str | None = None
    num_chunks: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class IndexAttemptOut(BaseModel):
    id: int
    connector_id: int
    status: str
    num_docs: int
    num_chunks: int
    error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=IndexAttemptOut)
def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_session),
) -> IndexAttempt:
    os.makedirs(settings.upload_dir, exist_ok=True)
    connector = Connector(
        name=f"upload-{uuid.uuid4().hex[:8]}",
        source=SourceType.file_upload,
        config={"filenames": [f.filename for f in files]},
    )
    db.add(connector)
    db.flush()

    saved_paths, titles = [], []
    for f in files:
        safe = f"{uuid.uuid4().hex}_{f.filename}"
        dest = os.path.join(settings.upload_dir, safe)
        with open(dest, "wb") as out:
            out.write(f.file.read())
        saved_paths.append(dest)
        titles.append(f.filename or safe)

    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    index_files_task.delay(attempt.id, saved_paths, titles)
    return attempt


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_session)) -> list[Document]:
    return list(db.execute(select(Document).order_by(Document.id.desc())).scalars())
