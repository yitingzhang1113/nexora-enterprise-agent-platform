"""v4 电商业务表 (products/orders/.../approvals)

Revision ID: 0002_business
Revises: 0001_initial
Create Date: 2026-06-25

create_all 只创建缺失的表 (checkfirst), 因此对已有 v3 库只新增业务表。
"""
from alembic import op

from app.db.engine import Base

import app.db.models  # noqa: F401

revision = "0002_business"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    pass
