from google import genai
from google.genai import types

from app.ai.clients.llm_base import LLMClient
from app.ai.gemini_helper import with_retry
from app.core.config import settings


class GeminiClient(LLMClient):
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def chat(self, message: str) -> str:
        def request():
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an assistant for an e-commerce application. "
                        "Answer clearly and concisely."
                    )
                ),
            )

            return response.text

        return with_retry(request)