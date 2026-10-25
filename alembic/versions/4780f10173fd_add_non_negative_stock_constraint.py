"""add non-negative stock constraint

Revision ID: 4780f10173fd
Revises: 7e2a9c4d1b6f
Create Date: 2026-10-25 11:30:25.484319

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4780f10173fd"
down_revision: str | Sequence[str] | None = "7e2a9c4d1b6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_products_stock_non_negative",
        "products",
        "stock >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_products_stock_non_negative",
        "products",
        type_="check",
    )
