import json

import pytest
from fastapi.testclient import TestClient

from app.analysis import parse_analysis
from app.llm import LLMInvalidOutputError
from app.main import app

client = TestClient(app)

VALID = {
    "sentiment": "negative",
    "topic": "export",
    "is_bug_report": True,
    "summary": "L'app si chiude durante l'esportazione.",
}


def test_parse_valid_output():
    analysis = parse_analysis(json.dumps(VALID))
    assert analysis.topic == "export"
    assert analysis.is_bug_report is True


@pytest.mark.parametrize(
    "raw",
    [
        "non è JSON",
        json.dumps({**VALID, "sentiment": "angry"}),
        json.dumps({**VALID, "extra_field": 1}),
        json.dumps({k: v for k, v in VALID.items() if k != "topic"}),
        json.dumps({**VALID, "summary": "x" * 201}),
    ],
    ids=[
        "not_json",
        "invalid_enum",
        "extra_field",
        "missing_field",
        "summary_too_long",
    ],
)
def test_parse_invalid_output_raises(raw):
    with pytest.raises(LLMInvalidOutputError):
        parse_analysis(raw)


def test_analyze_endpoint_returns_analysis(fake_llm):
    fake_llm.json_answer = json.dumps(VALID)
    response = client.post("/reviews/analyze", json={"text": "Si chiude sempre"})
    assert response.status_code == 200
    assert response.json() == VALID


def test_analyze_wraps_review_in_tags(fake_llm):
    fake_llm.json_answer = json.dumps(VALID)
    client.post("/reviews/analyze", json={"text": "Si chiude sempre"})
    assert fake_llm.last_message == "<review>\nSi chiude sempre\n</review>"


def test_analyze_invalid_model_output_returns_502(fake_llm):
    fake_llm.json_answer = "non è JSON"
    response = client.post("/reviews/analyze", json={"text": "Si chiude sempre"})
    assert response.status_code == 502
    assert response.json() == {"detail": "LLM returned invalid output"}
