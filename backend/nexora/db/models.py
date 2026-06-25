"""ORM 模型 (对应 onyx/db/models.py)。

与 Onyx 一致的关键点: **chunk 不在 Postgres**, 只存在向量库 (OpenSearch)。
Postgres 只保存元数据: 用户 / 连接器 / 文档 / 助手 / 会话 / 索引任务 / 搜索设置。
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nexora.db.engine import Base


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


class SearchSettings(Base):
    """向量库/嵌入配置 (对应 Onyx 的 search_settings)。单行有效配置。"""

    __tablename__ = "search_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    index_name: Mapped[str] = mapped_column(String(255))
    embed_model: Mapped[str] = mapped_column(String(255))
    embed_dim: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = _now()


class Connector(Base):
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
    """文档元数据。chunk 内容在 OpenSearch, 通过 document_id 关联。"""

    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    connector_id: Mapped[int | None] = mapped_column(
        ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[SourceType] = mapped_column(Enum(SourceType))
    title: Mapped[str] = mapped_column(String(512))
    link: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    doc_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _now()
    connector: Mapped[Connector | None] = relationship(back_populates="documents")


class Persona(Base):
    __tablename__ = "personas"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    tools: Mapped[list] = mapped_column(JSONB, default=list)
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
