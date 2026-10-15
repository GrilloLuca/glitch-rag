from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.analysis import ReviewAnalysis, analyze_review
from app.config import Settings, get_settings
from app.llm import (
    LLMClient,
    LLMError,
    LLMInvalidOutputError,
    LLMTimeoutError,
    LLMUnavailableError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.llm = LLMClient(settings)
    yield
    await app.state.llm.close()


app = FastAPI(title="Glitch RAG", lifespan=lifespan)

LLM_ERROR_RESPONSES: dict[type[LLMError], tuple[int, str]] = {
    LLMTimeoutError: (504, "LLM timeout"),
    LLMUnavailableError: (503, "LLM unavailable"),
    LLMInvalidOutputError: (502, "LLM returned invalid output"),
}


@app.exception_handler(LLMError)
async def handle_llm_error(request: Request, exc: LLMError) -> JSONResponse:
    status_code, detail = LLM_ERROR_RESPONSES.get(type(exc), (502, "LLM error"))
    return JSONResponse(status_code=status_code, content={"detail": detail})


def get_llm(request: Request) -> LLMClient:
    return request.app.state.llm


# --- Modelli ---


class Review(BaseModel):
    id: int
    rating: int
    comment: str | None = None


class AppInfo(BaseModel):
    app_name: str
    llm_model: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    model: str


# --- mock ---
dict_reviews: dict[int, dict] = {
    1: {"id": 1, "mail": "user1@mail.com", "rating": 5, "comment": ""},
    2: {"id": 2, "mail": "user2@mail.com", "rating": 4, "comment": "nice app!"},
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]) -> AppInfo:
    return AppInfo(app_name=settings.app_name, llm_model=settings.llm_model)


@app.get("/reviews/{review_id}")
async def get_reviews(review_id: int) -> Review:

    review = dict_reviews.get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return Review(**review)


@app.post("/chat")
async def chat(
    body: ChatRequest, llm: Annotated[LLMClient, Depends(get_llm)]
) -> ChatResponse:
    answer = await llm.chat(body.message)
    return ChatResponse(answer=answer, model=llm.model)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=4000)


@app.post("/reviews/analyze")
async def analyze(
    body: AnalyzeRequest, llm: Annotated[LLMClient, Depends(get_llm)]
) -> ReviewAnalysis:
    return await analyze_review(llm, body.text)
