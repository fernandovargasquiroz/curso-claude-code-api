from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_states_returns_catalog_in_order():
    response = client.get("/states")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "code": "PENDIENTE"},
        {"id": 2, "code": "EN_CURSO"},
        {"id": 3, "code": "BLOQUEADA"},
        {"id": 4, "code": "HECHA"},
    ]
