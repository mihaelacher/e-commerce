from datetime import datetime
from decimal import Decimal

from alembic.environment import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.enums.payment_provider import PaymentProvider
from app.enums.payment_status import PaymentStatus

if TYPE_CHECKING:
    from app.models.order import OrderModel


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_payment_amount_positive",
        ),
         UniqueConstraint(
            "order_id",
            "idempotency_key",
            name="uq_payment_order_idempotency_key",
        ),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        unique=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider),
        nullable=False,
    )

    transaction_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    order: Mapped["OrderModel"] = relationship(
        back_populates="payment",
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )