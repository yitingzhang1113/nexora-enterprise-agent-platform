"""ORM 模型。

为了让学习时一眼看全数据模型，这里把所有表集中在一个文件里
(Onyx 在 `backend/onyx/db/models.py` 也是单文件集中定义)。

数据流概览:
    Connector --(一次抓取)--> IndexAttempt
    Connector --(产出)--> Document --(切块)--> Chunk(embedding + tsv)
    Persona  --(配置助手)
    ChatSession --> ChatMessage(citations 指向 Chunk)
"""
from __future__ import annotations

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.db.base import Base


class SourceType(str, enum.Enum):
    file_upload = "file_upload"
    web = "web"


class IndexStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = _now()


class Connector(Base):
    """一个数据源配置 (文件上传 / 网页 / 未来更多)。对应 Onyx 的 Connector。"""

    __tablename__ = "connectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    source: Mapped[SourceType] = mapped_column(Enum(SourceType))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _now()

    index_attempts: Mapped[list[IndexAttempt]] = relationship(
        back_populates="connector", cascade="all, delete-orphan"
    )
    documents: Mapped[list[Document]] = relationship(back_populates="connector")


class IndexAttempt(Base):
    """一次索引任务的可观测记录 (状态/计数/错误)。对应 Onyx 的 IndexAttempt。"""

    __tablename__ = "index_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id", ondelete="CASCADE"))
    status: Mapped[IndexStatus] = mapped_column(Enum(IndexStatus), default=IndexStatus.pending)
    num_docs: Mapped[int] = mapped_column(Integer, default=0)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    connector: Mapped[Connector] = relationship(back_populates="index_attempts")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    connector_id: Mapped[int | None] = mapped_column(
        ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[SourceType] = mapped_column(Enum(SourceType))
    title: Mapped[str] = mapped_column(String(512))
    link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    doc_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _now()

    connector: Mapped[Connector | None] = relationship(back_populates="documents")
    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    """文档切块 + 向量 + 全文索引列。检索的最小单位。"""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    # pgvector 列：余弦相似度检索
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dim))
    # Postgres 全文检索列 (generated)，用于关键词召回
    tsv: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', content)", persisted=True)
    )
    created_at: Mapped[datetime] = _now()

    document: Mapped[Document] = relationship(back_populates="chunks")


# 关键词检索: tsv 上的 GIN 索引
Index("ix_chunks_tsv_gin", Chunk.tsv, postgresql_using="gin")

# 向量检索: embedding 上的 HNSW 索引 (余弦)
Index(
    "ix_chunks_embedding_hnsw",
    Chunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)


class Persona(Base):
    """AI 助手配置：system prompt + 可用工具。对应 Onyx 的 Persona/Assistant。"""

    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    tools: Mapped[list] = mapped_column(JSONB, default=list)  # e.g. ["search_docs","calculator"]
    created_at: Mapped[datetime] = _now()


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("personas.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = _now()

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32))  # user | assistant | tool
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _now()

    session: Mapped[ChatSession] = relationship(back_populates="messages")
