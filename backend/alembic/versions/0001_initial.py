"""initial schema (pgvector extension + 所有表 + 索引)

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-24

教学说明: 为了让初学者一眼看全建表, 这里先 CREATE EXTENSION vector,
再用 Base.metadata.create_all 一次性建出全部表与索引 (含 HNSW / GIN)。
生产项目通常用 alembic autogenerate 增量管理, 原理相同。
"""
from alembic import op

from app.db.base import Base

# 触发模型注册
import app.models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
