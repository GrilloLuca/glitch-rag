import numpy as np
import pytest

from app.reviews_source import load_reviews, review_id
from app.vector_index import normalize, top_k


def test_normalize_gives_unit_vectors():
    vectors = normalize(np.array([[3.0, 4.0], [0.0, 2.0]]))
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)


def test_top_k_orders_by_similarity():
    matrix = normalize(np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]))
    query = normalize(np.array([[0.0, 1.0]]))[0]
    results = top_k(query, matrix, k=2)
    assert [i for i, _ in results] == [1, 2]
    assert results[0][1] == pytest.approx(1.0)


def test_top_k_with_k_larger_than_index():
    matrix = normalize(np.array([[1.0, 0.0], [0.0, 1.0]]))
    assert len(top_k(matrix[0], matrix, k=10)) == 2


def test_load_reviews_reads_utf16_and_skips_empty(tmp_path):
    header = "Star Rating,Reviewer Language,App Version Name,Review Submit Millis Since Epoch,Review Text\n"
    rows = "5,it,4.1.13,1700000000000,Bellissima app\n2,en,4.1.12,1700000000001,\n"
    (tmp_path / "reviews_com.example_202401.csv").write_text(
        header + rows, encoding="utf-16"
    )

    reviews = list(load_reviews(tmp_path))

    assert len(reviews) == 1
    assert reviews[0].text == "Bellissima app"
    assert reviews[0].month == "202401"
    assert reviews[0].id == review_id("1700000000000", "Bellissima app")
