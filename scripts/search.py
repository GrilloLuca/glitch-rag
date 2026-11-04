import argparse
import asyncio
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.llm import LLMClient
from app.search import ReviewSearch
from app.vector_index import normalize

INDEX_DIR = Path("data/index")
MODES = ["keyword", "semantic", "hybrid"]


async def embed_query(query: str) -> np.ndarray:
    llm = LLMClient(get_settings())
    try:
        [vector] = await llm.embed([query])
    finally:
        await llm.close()
    return normalize(np.array([vector], dtype=np.float32))[0]


async def main(query: str, k: int, mode: str) -> None:
    search = ReviewSearch.load(INDEX_DIR)
    vector = await embed_query(query)
    modes = MODES if mode == "all" else [mode]

    for m in modes:
        if m == "keyword":
            hits = search.keyword(query, k)
        elif m == "semantic":
            hits = search.semantic(vector, k)
        else:
            hits = search.hybrid(query, vector, k)

        print(f"\n== {m} ==")
        if not hits:
            print("nessun risultato")
        for i, score in hits:
            r = search.reviews[i]
            print(
                f"{score:8.4f}  {r['rating']}★ {r['month']} {r['id']}  {r['text'][:110]}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ricerca nelle recensioni.")
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--mode", choices=[*MODES, "all"], default="all")
    args = parser.parse_args()
    asyncio.run(main(args.query, args.k, args.mode))
