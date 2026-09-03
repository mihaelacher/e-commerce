"""add content to knowledge documents

Revision ID: 7e2a9c4d1b6f
Revises: 4d4c3ea59309
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7e2a9c4d1b6f"
down_revision: str | Sequence[str] | None = "4d4c3ea59309"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_documents",
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            server_default=sa.text("''"),
        ),
    )
    op.alter_column(
        "knowledge_documents",
        "content",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("knowledge_documents", "content")
