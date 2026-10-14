from idlelib.iomenu import errors

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


def test_log_level_verbose_rejected():
    with pytest.raises(ValidationError) as exc_info:
        Settings(llm_api_key="x", log_level="VERBOSE", _env_file=None)

    print("----------- LOG ERROR -----------")
    _errors = exc_info.value.errors()
    print(_errors)
    assert _errors[0]["loc"] == ("log_level",)


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR"])
def test_log_level_accepts_valid_values(level):
    settings = Settings(llm_api_key="x", log_level=level, _env_file=None)
    assert settings.log_level == level
