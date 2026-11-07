from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.order import OrderStatus
from app.models.order import OrderModel
from app.models.order_item import OrderItemModel
from app.models.product import ProductModel


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_sales_data(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        stmt = (
            select(
                OrderModel.id.label("order_id"),
                OrderModel.created_at,
                OrderItemModel.product_id,
                ProductModel.name.label("product_name"),
                OrderItemModel.quantity,
                OrderItemModel.total_price,
            )
            .select_from(OrderModel)
            .join(
                OrderItemModel,
                OrderItemModel.order_id == OrderModel.id,
            )
            .join(
                ProductModel,
                ProductModel.id == OrderItemModel.product_id,
            )
            .where(
                OrderModel.status.in_((OrderStatus.PAID, OrderStatus.COMPLETED)),
            )
        )

        if from_date:
            stmt = stmt.where(OrderModel.created_at >= from_date)

        if to_date:
            stmt = stmt.where(OrderModel.created_at < to_date)

        return self.db.execute(stmt).mappings().all()
