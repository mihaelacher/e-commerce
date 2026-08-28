from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.ai import ProductSearchQuery


class ProductQueryParser:
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def parse(self, message: str) -> ProductSearchQuery:
        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Extract product search criteria from the customer request. "
                    "search_query should contain the semantic product request "
                    "without price constraints."
                ),
                response_mime_type="application/json",
                response_schema=ProductSearchQuery,
            ),
        )

        return ProductSearchQuery.model_validate_json(
            response.text
        )