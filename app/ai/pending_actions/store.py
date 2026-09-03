from abc import ABC, abstractmethod

from app.ai.models import PendingAction


class PendingActionStore(ABC):
    @abstractmethod
    async def save(
        self,
        action: PendingAction,
    ) -> None:
        pass

    @abstractmethod
    async def get(
        self,
        action_id: str,
    ) -> PendingAction | None:
        pass

    @abstractmethod
    async def delete(
        self,
        action_id: str,
    ) -> None:
        pass
