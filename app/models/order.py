from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.order import OrderStatus

if TYPE_CHECKING:
    from app.models.order_item import OrderItemModel
    from app.models.payment import PaymentModel


class OrderModel(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "subtotal >= 0",
            name="ck_order_subtotal_non_negative",
        ),
        CheckConstraint(
            "total >= 0",
            name="ck_order_total_non_negative",
        ),
        CheckConstraint(
            "tax >= 0",
            name="ck_order_tax_non_negative",
        ),
        CheckConstraint(
            "shipping >= 0",
            name="ck_order_shipping_non_negative",
        ),
        CheckConstraint(
            "discount >= 0",
            name="ck_order_discount_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    tax: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    shipping: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    payments: Mapped[list["PaymentModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
