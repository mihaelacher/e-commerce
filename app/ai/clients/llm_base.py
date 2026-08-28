from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def chat(self, message: str) -> str:
        pass