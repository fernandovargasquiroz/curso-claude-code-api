"""create states catalog

Revision ID: 94f759f184a1
Revises:
Create Date: 2026-08-31 18:57:49.305677

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "94f759f184a1"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

STATES = [
    {"code": "PENDIENTE", "sort_order": 1},
    {"code": "EN_CURSO", "sort_order": 2},
    {"code": "BLOQUEADA", "sort_order": 3},
    {"code": "HECHA", "sort_order": 4},
]


def upgrade() -> None:
    """Upgrade schema."""
    states = op.create_table(
        "states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.bulk_insert(states, STATES)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("states")
