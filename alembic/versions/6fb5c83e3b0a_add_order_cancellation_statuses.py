"""add order cancellation statuses

Revision ID: 6fb5c83e3b0a
Revises: 73e6f53fa82d
Create Date: 2026-09-02

"""

from collections.abc import Sequence

from alembic import op

revision: str = "6fb5c83e3b0a"
down_revision: str | Sequence[str] | None = "73e6f53fa82d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'CANCELLATION_PENDING'")
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'REFUND_PENDING'")


def downgrade() -> None:
    pass
