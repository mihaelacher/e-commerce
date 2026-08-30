import httpx

from app.core.config import settings


class N8NClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.n8n_base_url).rstrip("/")

    def order_created(
        self,
        order_id: int,
        total: str,
    ) -> None:
        response = httpx.post(
            f"{self.base_url}/webhook/order-created",
            json={
                "id": order_id,
                "total": total,
            },
            timeout=5,
        )

        response.raise_for_status()


n8n_client = N8NClient()