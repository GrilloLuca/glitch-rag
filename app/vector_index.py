import numpy as np


def normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def top_k(query: np.ndarray, matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    scores = matrix @ query
    best = np.argsort(-scores)[: min(k, len(scores))]
    return [(int(i), float(scores[i])) for i in best]
