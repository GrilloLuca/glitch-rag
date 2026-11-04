import numpy as np

from app.search import ReviewSearch, rrf, tokenize
from app.vector_index import normalize


def make_search() -> ReviewSearch:
    reviews = [
        {"id": "a", "text": "Datamosh is paid now"},
        {"id": "b", "text": "Great VHS effect"},
        {"id": "c", "text": "The app crashes on export"},
        {"id": "d", "text": "."},
    ]
    matrix = normalize(np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.5, 0.5]]))
    return ReviewSearch(reviews, matrix)


def test_tokenize_keeps_versions_and_lowercases():
    assert tokenize("Bug in 4.1.13, l'App crasha!") == [
        "bug",
        "in",
        "4.1.13",
        "l",
        "app",
        "crasha",
    ]


def test_reviews_without_letters_are_excluded():
    search = make_search()
    assert [r["id"] for r in search.reviews] == ["a", "b", "c"]
    assert search.matrix.shape == (3, 2)


def test_keyword_finds_exact_term():
    search = make_search()
    [(index, score)] = search.keyword("datamosh", k=5)
    assert search.reviews[index]["id"] == "a"
    assert score > 0


def test_keyword_returns_nothing_for_unknown_term():
    assert make_search().keyword("4.1.13", k=5) == []


def test_rrf_favours_documents_in_both_rankings():
    fused = rrf([[1, 2, 3], [3, 4, 5]])
    assert fused[0][0] == 3


def test_hybrid_combines_both_methods():
    search = make_search()
    query_vector = normalize(np.array([[0.0, 1.0]]))[0]
    hits = search.hybrid("datamosh", query_vector, k=3)
    ids = [search.reviews[i]["id"] for i, _ in hits]
    assert "a" in ids
    assert "b" in ids
