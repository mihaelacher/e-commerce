from typing import ClassVar

from sqlalchemy.orm import Session

from app.ai.tools.schemas import CancelOrderInput
from app.services.order import cancel_order


class CancelOrderTool:
    name = "cancel_order"
    input_model = CancelOrderInput
    requires_confirmation = True

    definition: ClassVar[dict] = {
        "name": name,
        "description": (
            "Cancel an existing order when explicitly requested "
            "by the customer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to cancel.",
                },
            },
            "required": ["order_id"],
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def execute(
        self,
        order_id: int,
    ) -> dict:
        order = cancel_order(
            db=self.db,
            order_id=order_id,
        )

        return {
            "success": True,
            "order_id": order.id,
            "status": order.status,
        }