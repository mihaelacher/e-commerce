from app.repositories.order import OrderRepository


class GetOrderStatusTool:
    name = "get_order_status"

    definition = {
        "name": name,
        "description": "Get the current status of an order.",
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

    def execute(self, order_id: int) -> dict:
        order = self.order_repository.get(order_id)

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