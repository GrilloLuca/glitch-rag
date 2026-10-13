from fastapi import FastAPI

app = FastAPI(title="Glitch RAG")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
