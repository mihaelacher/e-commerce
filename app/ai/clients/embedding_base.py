from abc import ABC, abstractmethod


class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass

    @abstractmethod
    async def embed_async(
        self,
        text: str,
    ) -> list[float]:
        pass
