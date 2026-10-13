from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Glitch RAG")

class Review(BaseModel):
    id: int
    rating: int
    comment: str | None = None

dict_reviews: dict[int, dict] = {
    1: {"id": 1, "mail": "user1@mail.com", "rating": 5, "comment": ""},
    2: {"id": 2, "mail": "user2@mail.com", "rating": 4, "comment": "nice app!"}
}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/reviews/{review_id}")
async def get_reviews(review_id: int) -> Review:

    review = dict_reviews.get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return Review(**review)