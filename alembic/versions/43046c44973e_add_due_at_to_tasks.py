"""add due_at to tasks

Revision ID: 43046c44973e
Revises: d1b5f0872ce7
Create Date: 2026-09-07 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43046c44973e"
down_revision: str | None = "d1b5f0872ce7"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tasks", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tasks", "due_at")
