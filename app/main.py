import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
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
from app.rag import AskRequest, AskResponse, answer_question
from app.search import ReviewSearch


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.llm = LLMClient(settings)
    try:
        app.state.search = ReviewSearch.load(settings.index_dir)
    except FileNotFoundError:
        app.state.search = None
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


def get_search(request: Request) -> ReviewSearch:
    search = getattr(request.app.state, "search", None)
    if search is None:
        raise HTTPException(status_code=503, detail="Search index not built")
    return search


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


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    llm: Annotated[LLMClient, Depends(get_llm)],
) -> StreamingResponse:
    tokens = llm.chat_stream(body.message)
    first_token = await anext(tokens, None)

    async def events() -> AsyncIterator[str]:
        if first_token is not None:
            yield sse_event("token", {"text": first_token})
        try:
            async for token in tokens:
                yield sse_event("token", {"text": token})
        except LLMError:
            yield sse_event("error", {"detail": "LLM stream interrupted"})
            return
        yield sse_event("done", {"model": llm.model})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=4000)


@app.post("/reviews/analyze")
async def analyze(
    body: AnalyzeRequest, llm: Annotated[LLMClient, Depends(get_llm)]
) -> ReviewAnalysis:
    return await analyze_review(llm, body.text)


@app.post("/ask")
async def ask(
    body: AskRequest,
    llm: Annotated[LLMClient, Depends(get_llm)],
    search: Annotated[ReviewSearch, Depends(get_search)],
) -> AskResponse:
    return await answer_question(llm, search, body)
