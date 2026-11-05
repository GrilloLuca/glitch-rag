import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from app.vector_index import top_k

TOKEN_RE = re.compile(r"\w+(?:\.\w+)*")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def is_searchable(text: str) -> bool:
    return any(c.isalpha() for c in text)


# Il 60 è la costante usata in letteratura:
# attenua la differenza tra le prime posizioni, così nessun metodo da solo domina.
def rrf(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


class ReviewSearch:
    def __init__(self, reviews: list[dict], matrix: np.ndarray) -> None:
        keep = [i for i, r in enumerate(reviews) if is_searchable(r["text"])]
        self.reviews = [reviews[i] for i in keep]
        self.matrix = matrix[keep]
        self._bm25 = BM25Okapi([tokenize(r["text"]) for r in self.reviews])

    @classmethod
    def load(cls, index_dir: Path, records: str = "reviews.jsonl") -> "ReviewSearch":
        matrix = np.load(index_dir / "embeddings.npy")
        with (index_dir / records).open(encoding="utf-8") as f:
            items = [json.loads(line) for line in f]
        return cls(items, matrix)

    def keyword(self, query: str, k: int) -> list[tuple[int, float]]:
        scores = self._bm25.get_scores(tokenize(query))
        best = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in best if scores[i] > 0]

    def semantic(self, query_vector: np.ndarray, k: int) -> list[tuple[int, float]]:
        return top_k(query_vector, self.matrix, k)

    def hybrid(
        self, query: str, query_vector: np.ndarray, k: int, candidates: int = 50
    ) -> list[tuple[int, float]]:
        by_keyword = [i for i, _ in self.keyword(query, candidates)]
        by_meaning = [i for i, _ in self.semantic(query_vector, candidates)]
        return rrf([by_keyword, by_meaning])[:k]
