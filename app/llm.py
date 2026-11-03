from collections.abc import AsyncIterator
from contextlib import contextmanager

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.config import Settings

SYSTEM_PROMPT = (
    "Sei l'assistente di Glitch!, un'app Android di editing foto e video. "
    "Rispondi in modo conciso, nella lingua dell'utente. "
    "Se non conosci la risposta, dillo chiaramente."
)


class LLMError(Exception):
    """Errore generico del provider LLM."""


class LLMUnavailableError(LLMError):
    """Il provider non è raggiungibile."""


class LLMTimeoutError(LLMError):
    """Il provider non ha risposto in tempo."""


class LLMInvalidOutputError(LLMError):
    """Il modello ha risposto con un formato non valido."""


@contextmanager
def translate_errors():
    try:
        yield
    except APITimeoutError as e:
        raise LLMTimeoutError("Il modello non ha risposto in tempo") from e
    except APIConnectionError as e:
        raise LLMUnavailableError("Impossibile raggiungere il modello") from e
    except APIStatusError as e:
        raise LLMError(f"Errore dal provider: HTTP {e.status_code}") from e


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key.get_secret_value(),
            timeout=settings.llm_timeout_seconds,
            max_retries=1,
        )

    @property
    def model(self) -> str:
        return self._model

    async def _complete(self, messages: list[dict], **kwargs) -> str:
        with translate_errors():
            response = await self._client.chat.completions.create(
                model=self._model, messages=messages, **kwargs
            )
        return response.choices[0].message.content or ""

    async def complete_json(
        self, system_prompt: str, user_content: str, schema_name: str, schema: dict
    ) -> str:
        return await self._complete(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            },
        )

    async def chat(self, message: str) -> str:
        return await self._complete(self._chat_messages(message), temperature=0.3)

    def _chat_messages(self, message: str) -> list[dict]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        with translate_errors():
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=self._chat_messages(message),
                temperature=0.3,
                stream=True,
            )
            try:
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            finally:
                await stream.close()

    async def close(self) -> None:
        await self._client.close()
