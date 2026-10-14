import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def test_missing_api_key_fails(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_negative_timeout_fails():
    with pytest.raises(ValidationError):
        Settings(llm_api_key="x", llm_timeout_seconds=-5, _env_file=None)


def test_info_does_not_expose_api_key():
    app.dependency_overrides[get_settings] = lambda: Settings(
        llm_api_key="super-secret-test-key", _env_file=None
    )
    try:
        response = client.get("/info")
        assert response.status_code == 200
        assert "super-secret-test-key" not in response.text
    finally:
        app.dependency_overrides.clear()
