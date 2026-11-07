from typing import Any, ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools.schemas import CancelOrderInput
from app.services.order import cancel_order_async


class CancelOrderTool:
    name = "cancel_order"
    input_model = CancelOrderInput
    requires_confirmation = True

    definition: ClassVar[dict[str, Any]] = {
        "name": name,
        "description": (
            "Request cancellation of an existing order only when the customer "
            "clearly asks to cancel it and provides the order ID. Do not use for "
            "questions about whether cancellation is possible or allowed; use "
            "policy search for those. The application requires customer "
            "confirmation before executing cancellation."
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
        order = await cancel_order_async(
            db=self.db,
            order_id=order_id,
        )

        return {
            "success": True,
            "order_id": order.id,
            "status": order.status,
        }
