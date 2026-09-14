from langchain_openai import ChatOpenAI

from app.core.config import settings



class LangChainClient:
    def __init__(self):
        self.client = ChatOpenAI(
            model="gpt-5",
            api_key=settings.openai_api_key,
            temperature=0,
        )

    def get_client(self) -> ChatOpenAI:
        return self.client