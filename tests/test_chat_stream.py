import json

from fastapi.testclient import TestClient

from app.llm import LLMError, LLMUnavailableError
from app.main import app

client = TestClient(app)


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))
    return events


def test_stream_sends_tokens_then_done(fake_llm):
    response = client.post("/chat/stream", json={"message": "Ciao"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert parse_sse(response.text) == [
        ("token", {"text": "Ciao"}),
        ("token", {"text": " mondo"}),
        ("done", {"model": "fake-model"}),
    ]


def test_stream_token_with_newline_is_escaped(fake_llm):
    fake_llm.stream_tokens = ["riga 1\nriga 2"]
    response = client.post("/chat/stream", json={"message": "Ciao"})
    assert parse_sse(response.text)[0] == ("token", {"text": "riga 1\nriga 2"})


def test_stream_error_before_first_token_returns_503(fake_llm):
    fake_llm.error = LLMUnavailableError("down")
    response = client.post("/chat/stream", json={"message": "Ciao"})
    assert response.status_code == 503


def test_stream_error_mid_stream_sends_error_event(fake_llm):
    fake_llm.error = LLMError("boom")
    fake_llm.error_after_tokens = 1
    response = client.post("/chat/stream", json={"message": "Ciao"})
    assert response.status_code == 200
    events = parse_sse(response.text)
    assert events[0] == ("token", {"text": "Ciao"})
    assert events[-1] == ("error", {"detail": "LLM stream interrupted"})
    assert ("done", {"model": "fake-model"}) not in events


def test_stream_empty_message_rejected(fake_llm):
    response = client.post("/chat/stream", json={"message": "   "})
    assert response.status_code == 422
    assert fake_llm.last_message is None
