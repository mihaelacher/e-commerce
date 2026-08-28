from google import genai
from google.genai import types

from app.ai.clients.embedding_base import EmbeddingClient
from app.ai.gemini_helper import with_retry
from app.core.config import settings


class GeminiEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def embed(self, text: str) -> list[float]:
        def request():
            response = self.client.models.embed_content(
                model="gemini-embedding-2",
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                ),
            )

            return response.embeddings[0].values

        return with_retry(request)