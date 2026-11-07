from typing import Any, ClassVar

from app.ai.tools.schemas import GetOrderStatusInput
from app.repositories.order.async_order import AsyncOrderRepository as OrderRepository


class GetOrderStatusTool:
    name: ClassVar[str] = "get_order_status"
    input_model = GetOrderStatusInput
    requires_confirmation = False

    definition: ClassVar[dict[str, Any]] = {
        "name": name,
        "description": (
            "Retrieve the current status of a specific order when the customer "
            "asks for its status or asks whether that order is eligible for an "
            "action. Requires the order ID. For policy-dependent eligibility, "
            "combine this with search_knowledge; order status alone does not "
            "determine the policy."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order.",
                },
            },
            "required": ["order_id"],
        },
    }

    def __init__(
        self,
        order_repository: OrderRepository,
    ):
        self.order_repository = order_repository

    async def execute(self, order_id: int) -> dict:
        order = await self.order_repository.get(order_id)

        if not order:
            return {
                "order_id": order_id,
                "found": False,
            }

        return {
            "order_id": order.id,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
        }
