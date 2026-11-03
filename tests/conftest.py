import pytest

from app.main import app, get_llm


class FakeLLM:
    model = "fake-model"

    def __init__(self) -> None:
        self.answer = "Risposta finta"
        self.json_answer = "{}"
        self.error: Exception | None = None
        self.last_message: str | None = None
        self.stream_tokens = ["Ciao", " mondo"]
        self.error_after_tokens = 0

    async def chat(self, message: str) -> str:
        self.last_message = message
        if self.error is not None:
            raise self.error
        return self.answer

    async def complete_json(
        self, system_prompt: str, user_content: str, schema_name: str, schema: dict
    ) -> str:
        self.last_message = user_content
        if self.error is not None:
            raise self.error
        return self.json_answer

    async def chat_stream(self, message: str):
        self.last_message = message
        for i, token in enumerate(self.stream_tokens):
            if self.error is not None and i == self.error_after_tokens:
                raise self.error
            yield token


@pytest.fixture
def fake_llm():
    fake = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.clear()
