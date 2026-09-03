from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ProductModel(Base):
    __tablename__ = "products"

    __table_args__ = (
        Index(
            "ix_products_embedding_cosine",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_products_without_embedding",
            "id",
            postgresql_where="embedding IS NULL",
        ),
        CheckConstraint(
            "price > 0",
            name="ck_product_price_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    stock: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        VECTOR(768),
        nullable=True,
    )
