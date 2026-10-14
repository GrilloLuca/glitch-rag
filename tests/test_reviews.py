from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_reviews():
    response = client.get("/reviews/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "rating": 5, "comment": ""}


def test_reviews_404():
    response = client.get("/reviews/0")
    assert response.status_code == 404


def test_reviews_no_user():
    response = client.get("/reviews/1")
    assert response.status_code == 200
    assert "mail" not in response.json()


def test_reviews_str_param():
    response = client.get("/reviews/aaa")
    assert response.status_code == 422
