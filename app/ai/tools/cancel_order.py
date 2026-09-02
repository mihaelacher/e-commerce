from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools.schemas import CancelOrderInput
from app.services.order import cancel_order


class CancelOrderTool:
    name = "cancel_order"
    input_model = CancelOrderInput
    requires_confirmation = True

    definition: ClassVar[dict] = {
        "name": name,
        "description": (
            "Cancel an existing customer order. "
            "Use this tool when the customer explicitly requests "
            "cancellation of an order."
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

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(
        self,
        order_id: int,
    ) -> dict:
        order = await cancel_order(
            db=self.db,
            order_id=order_id,
        )

        return {
            "success": True,
            "order_id": order.id,
            "status": order.status,
        }
