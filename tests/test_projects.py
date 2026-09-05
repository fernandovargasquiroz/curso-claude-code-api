from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_project_returns_201_with_created_resource():
    response = client.post("/projects", json={"name": "Casa"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Casa"
    assert body["description"] is None
    assert isinstance(body["id"], int)


def test_get_projects_returns_created_projects_ordered_by_id():
    first = client.post("/projects", json={"name": "Uno"}).json()
    second = client.post("/projects", json={"name": "Dos", "description": "Segunda"}).json()

    response = client.get("/projects")

    assert response.status_code == 200
    ids = [project["id"] for project in response.json()]
    assert ids.index(first["id"]) < ids.index(second["id"])


def test_get_project_by_id_returns_200_or_404():
    created = client.post("/projects", json={"name": "Individual"}).json()

    found = client.get(f"/projects/{created['id']}")
    assert found.status_code == 200
    assert found.json() == created

    missing = client.get("/projects/0")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Proyecto no encontrado"}


def test_patch_project_updates_only_provided_fields():
    created = client.post(
        "/projects", json={"name": "Original", "description": "Descripción original"}
    ).json()

    response = client.patch(f"/projects/{created['id']}", json={"name": "Renombrado"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renombrado"
    assert body["description"] == "Descripción original"


def test_patch_project_returns_404_for_missing_id():
    response = client.patch("/projects/0", json={"name": "No existe"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Proyecto no encontrado"}
