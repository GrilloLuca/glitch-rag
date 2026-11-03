import argparse
import asyncio
import json
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.llm import LLMClient
from app.vector_index import normalize, top_k

INDEX_DIR = Path("data/index")


async def main(query: str, k: int) -> None:
    matrix = np.load(INDEX_DIR / "embeddings.npy")
    with (INDEX_DIR / "reviews.jsonl").open(encoding="utf-8") as f:
        reviews = [json.loads(line) for line in f]

    llm = LLMClient(get_settings())
    try:
        [vector] = await llm.embed([query])
    finally:
        await llm.close()

    query_vector = normalize(np.array([vector], dtype=np.float32))[0]
    for i, score in top_k(query_vector, matrix, k):
        r = reviews[i]
        print(
            f"{score:.3f}  {r['rating']}★ {r['language']} {r['month']}  {r['text'][:140]}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ricerca semantica nelle recensioni.")
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(main(args.query, args.k))
