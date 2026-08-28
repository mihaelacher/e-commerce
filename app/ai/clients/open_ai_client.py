from openai import OpenAI

from app.ai.clients.llm_base import LLMClient
from app.core.config import settings


class OpenAIClient(LLMClient):
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )

    def chat(self, message: str) -> str:
        response = self.client.responses.create(
            model="gpt-5-mini",
            instructions=(
                "You are an assistant for an e-commerce application. "
                "Answer clearly and concisely."
            ),
            input=message,
        )

        return response.output_text