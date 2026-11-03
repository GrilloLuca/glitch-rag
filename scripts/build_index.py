import asyncio
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.llm import LLMClient
from app.reviews_source import load_reviews
from app.vector_index import normalize

INDEX_DIR = Path("data/index")


async def main(src_dir: Path) -> None:
    settings = get_settings()
    reviews = list({r.id: r for r in load_reviews(src_dir)}.values())
    print(f"{len(reviews)} recensioni con testo")

    llm = LLMClient(settings)
    vectors: list[list[float]] = []
    size = settings.embedding_batch_size
    started = time.perf_counter()
    try:
        for start in range(0, len(reviews), size):
            batch = reviews[start : start + size]
            vectors.extend(await llm.embed([r.text for r in batch]))
            print(f"\r{start + len(batch)}/{len(reviews)}", end="", flush=True)
    finally:
        await llm.close()

    matrix = normalize(np.array(vectors, dtype=np.float32))
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_DIR / "embeddings.npy", matrix)
    with (INDEX_DIR / "reviews.jsonl").open("w", encoding="utf-8") as out:
        for r in reviews:
            out.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    elapsed = time.perf_counter() - started
    print(
        f"\nIndice: {matrix.shape[0]} vettori da {matrix.shape[1]} dimensioni, {elapsed:.0f}s"
    )


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
