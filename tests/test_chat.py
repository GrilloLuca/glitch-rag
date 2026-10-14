import pytest
from fastapi.testclient import TestClient

from app.llm import LLMTimeoutError, LLMUnavailableError
from app.main import app, get_llm

client = TestClient(app)

class FakeLLM:
    model = "fake-model"

    def __init__(self) -> None:
        self.answer = "Risposta finta"
        self.error: Exception | None = None
        self.last_message: str | None = None

    async def chat(self, message: str) -> str:
        self.last_message = message
        if self.error is not None:
            raise self.error
        return self.answer


@pytest.fixture
def fake_llm():
    fake = FakeLLM()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


def test_chat_returns_answer(fake_llm):
    response = client.post("/chat", json={"message": "Ciao"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Risposta finta", "model": "fake-model"}
    assert fake_llm.last_message == "Ciao"


def test_chat_empty_message_rejected(fake_llm):
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422
    assert fake_llm.last_message is None


def test_chat_whitespace_only_message_rejected(fake_llm):
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422
    assert fake_llm.last_message is None


def test_chat_llm_unavailable(fake_llm):
    fake_llm.error = LLMUnavailableError("down")
    response = client.post("/chat", json={"message": "Ciao"})
    assert response.status_code == 503


def test_chat_llm_timeout(fake_llm):
    fake_llm.error = LLMTimeoutError("slow")
    response = client.post("/chat", json={"message": "Ciao"})
    assert response.status_code == 504