from app.analysis import build_analysis_prompt
from app.config import Settings
from app.llm import LLMClient
from app.rag import build_rag_prompt

DESCRIPTION = "PhotoFix, an Android app for retouching photos"


def test_prompts_use_the_configured_app_description():
    for prompt in (build_analysis_prompt(DESCRIPTION), build_rag_prompt(DESCRIPTION)):
        assert DESCRIPTION in prompt
        assert "Glitch" not in prompt
        assert "{" not in prompt


def test_chat_prompt_comes_from_settings():
    settings = Settings(llm_api_key="x", app_description=DESCRIPTION, _env_file=None)
    client = LLMClient(settings)
    system_message = client._chat_messages("Ciao")[0]
    assert system_message["role"] == "system"
    assert DESCRIPTION in system_message["content"]
    assert client.app_description == DESCRIPTION
