"""add query indexes

Revision ID: b4c8f2d1a6e7
Revises: 6fb5c83e3b0a
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b4c8f2d1a6e7"
down_revision: str | Sequence[str] | None = "6fb5c83e3b0a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_orders_status_created_at",
        "orders",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_payments_order_id_status",
        "payments",
        ["order_id", "status"],
    )
    op.create_index(
        "ix_products_embedding_cosine",
        "products",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_products_without_embedding",
        "products",
        ["id"],
        postgresql_where=sa.text("embedding IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_products_without_embedding", table_name="products")
    op.drop_index("ix_products_embedding_cosine", table_name="products")
    op.drop_index("ix_payments_order_id_status", table_name="payments")
    op.drop_index("ix_orders_status_created_at", table_name="orders")
