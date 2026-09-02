"""add payment pending order status

Revision ID: c7a4e9f2b1d6
Revises: cb16e1182ad7
Create Date: 2026-08-21

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c7a4e9f2b1d6"
down_revision: str | Sequence[str] | None = "cb16e1182ad7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'PAYMENT_PENDING'")


def downgrade() -> None:
    pass
