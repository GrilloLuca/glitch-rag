import json

import numpy as np
import pytest

from app.index_meta import IndexMismatchError, write_index_meta
from app.search import ReviewSearch


def make_index(path, rows=2, meta_model="bge-m3", meta_count=None):
    np.save(path / "embeddings.npy", np.eye(rows, 3, dtype=np.float32))
    with (path / "reviews.jsonl").open("w", encoding="utf-8") as f:
        for i in range(rows):
            f.write(json.dumps({"id": f"r{i}", "text": f"review number {i}"}) + "\n")
    if meta_model is not None:
        count = rows if meta_count is None else meta_count
        write_index_meta(path, meta_model, count=count, dimensions=3)
    return path


def test_load_with_matching_model(tmp_path):
    search = ReviewSearch.load(make_index(tmp_path), "bge-m3")
    assert [r["id"] for r in search.reviews] == ["r0", "r1"]


def test_load_refuses_other_model(tmp_path):
    with pytest.raises(IndexMismatchError, match="nomic-embed-text"):
        ReviewSearch.load(make_index(tmp_path), "nomic-embed-text")


def test_load_refuses_index_without_meta(tmp_path):
    with pytest.raises(IndexMismatchError, match="mancante"):
        ReviewSearch.load(make_index(tmp_path, meta_model=None), "bge-m3")


def test_load_refuses_incomplete_index(tmp_path):
    with pytest.raises(IndexMismatchError, match="incompleto"):
        ReviewSearch.load(make_index(tmp_path, meta_count=5), "bge-m3")