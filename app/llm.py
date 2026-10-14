
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

class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key.get_secret_value(),
            timeout=settings.llm_timeout_seconds,
            max_retries=1
        )

    @property
    def model(self) -> str:
        return self._model

    async def chat(self, message: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0.3,
            )
        except APITimeoutError as e:
            raise LLMTimeoutError("Il modello non ha risposto in tempo") from e
        except APIConnectionError as e:
            raise LLMUnavailableError("Impossibile raggiungere il modello") from e
        except APIStatusError as e:
            raise LLMError(f"Errore dal provider: HTTP {e.status_code}") from e
        return response.choices[0].message.content or ""


    async def close(self) -> None:
        await self._client.close()
