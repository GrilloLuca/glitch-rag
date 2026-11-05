import asyncio

import numpy as np

from app.config import get_settings
from app.llm import LLMClient
from app.vector_index import normalize

PHRASES = [
    "l'esportazione funziona benissimo",
    "l'esportazione non funziona",
    "the app crashes when I export a video",
    "si chiude quando salvo un video",
    "troppa pubblicità",
    "fantastic app",
    "🔥🔥🔥",
    "terrible app",
]


async def main() -> None:
    llm = LLMClient(get_settings())
    try:
        vectors = await llm.embed(PHRASES)
    finally:
        await llm.close()

    m = normalize(np.array(vectors, dtype=np.float32))
    similarity = m @ m.T

    for i, phrase in enumerate(PHRASES):
        print(f"{i}: {phrase}")
    print("\n    " + "".join(f"{j:>6}" for j in range(len(PHRASES))))
    for i, row in enumerate(similarity):
        print(f"{i:>3} " + "".join(f"{v:6.2f}" for v in row))


if __name__ == "__main__":
    asyncio.run(main())
