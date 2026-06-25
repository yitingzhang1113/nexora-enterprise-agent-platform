"""initial schema v2 (Postgres 仅元数据; chunk 在 OpenSearch)

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-25

v2 不再用 pgvector: chunk 移到 OpenSearch。这里用 create_all 一次性建出全部元数据表。
"""
from alembic import op

from nexora.db.engine import Base

import nexora.db.models  # noqa: F401  触发模型注册

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
