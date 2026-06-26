"""知识库 API: 检索 + 文档上传/网页抓取 + 索引任务状态。"""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.engine import get_session
from app.db.models import Connector, Document, IndexAttempt, SourceType
from app.rag.multi_retriever import multi_retrieve
from app.tasks.ingestion_tasks import index_files_task, index_web_task

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class SearchRequest(BaseModel):
    query: str
    top_k: int | None = None


class WebRequest(BaseModel):
    url: str
    name: str | None = None


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


@router.post("/search")
def search(req: SearchRequest, db: Session = Depends(get_session)) -> dict:
    chunks = multi_retrieve(db, req.query, top_k=req.top_k)
    return {
        "query": req.query,
        "hits": [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_title": c.doc_title,
                "content": c.content,
                "score": c.score,
                "dense_rank": c.dense_rank,
                "bm25_rank": c.bm25_rank,
            }
            for c in chunks
        ],
    }


@router.post("/upload", response_model=IndexAttemptOut)
def upload(files: list[UploadFile] = File(...), db: Session = Depends(get_session)) -> IndexAttempt:
    os.makedirs(settings.upload_dir, exist_ok=True)
    connector = Connector(
        name=f"upload-{uuid.uuid4().hex[:8]}",
        source=SourceType.file_upload,
        config={"filenames": [f.filename for f in files]},
    )
    db.add(connector)
    db.flush()
    saved, titles = [], []
    for f in files:
        safe = f"{uuid.uuid4().hex}_{f.filename}"
        dest = os.path.join(settings.upload_dir, safe)
        with open(dest, "wb") as out:
            out.write(f.file.read())
        saved.append(dest)
        titles.append(f.filename or safe)
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    index_files_task.delay(attempt.id, saved, titles)
    return attempt


@router.post("/web", response_model=IndexAttemptOut)
def index_web(req: WebRequest, db: Session = Depends(get_session)) -> IndexAttempt:
    connector = Connector(
        name=req.name or f"web-{uuid.uuid4().hex[:8]}",
        source=SourceType.web,
        config={"url": req.url},
    )
    db.add(connector)
    db.flush()
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    index_web_task.delay(attempt.id, req.url)
    return attempt


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_session)) -> list[Document]:
    return list(db.execute(select(Document).order_by(Document.id.desc())).scalars())


@router.get("/index-attempts", response_model=list[IndexAttemptOut])
def list_attempts(db: Session = Depends(get_session)) -> list[IndexAttempt]:
    return list(db.execute(select(IndexAttempt).order_by(IndexAttempt.id.desc())).scalars())
