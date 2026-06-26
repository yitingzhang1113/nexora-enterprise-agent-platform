"""initial schema v3

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-25
"""
from alembic import op

from app.db.engine import Base

import app.db.models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
