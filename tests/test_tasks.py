from fastapi.testclient import TestClient

from app.main import app
from app.states import list_states

client = TestClient(app)


def _create_project(name: str) -> dict:
    return client.post("/projects", json={"name": name}).json()


def _existing_state_id() -> int:
    return list_states()[0].id


def test_create_task_returns_201_with_created_resource():
    project = _create_project("Casa")
    state_id = _existing_state_id()

    response = client.post(
        "/tasks",
        json={
            "title": "Regar las plantas",
            "project_id": project["id"],
            "state_id": state_id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Regar las plantas"
    assert body["description"] is None
    assert body["project_id"] == project["id"]
    assert body["state_id"] == state_id
    assert isinstance(body["id"], int)


def test_create_task_returns_422_for_nonexistent_project():
    state_id = _existing_state_id()

    response = client.post(
        "/tasks", json={"title": "Tarea", "project_id": 0, "state_id": state_id}
    )

    assert response.status_code == 422


def test_create_task_returns_422_for_nonexistent_state():
    project = _create_project("Trabajo")

    response = client.post(
        "/tasks", json={"title": "Tarea", "project_id": project["id"], "state_id": 0}
    )

    assert response.status_code == 422


def test_create_task_returns_422_for_blank_title():
    project = _create_project("Otro")
    state_id = _existing_state_id()

    response = client.post(
        "/tasks",
        json={"title": "   ", "project_id": project["id"], "state_id": state_id},
    )

    assert response.status_code == 422


def test_get_tasks_filters_by_project_and_state():
    states = list_states()
    project_a = _create_project("Filtro A")
    project_b = _create_project("Filtro B")

    task_a = client.post(
        "/tasks",
        json={"title": "A", "project_id": project_a["id"], "state_id": states[0].id},
    ).json()
    task_b = client.post(
        "/tasks",
        json={"title": "B", "project_id": project_b["id"], "state_id": states[1].id},
    ).json()

    only_project_a = client.get("/tasks", params={"project_id": project_a["id"]})
    assert only_project_a.status_code == 200
    assert {t["id"] for t in only_project_a.json()} == {task_a["id"]}

    only_state_b = client.get("/tasks", params={"state_id": states[1].id})
    assert task_b["id"] in {t["id"] for t in only_state_b.json()}
    assert task_a["id"] not in {t["id"] for t in only_state_b.json()}

    combined = client.get(
        "/tasks", params={"project_id": project_a["id"], "state_id": states[0].id}
    )
    assert {t["id"] for t in combined.json()} == {task_a["id"]}


def test_get_task_by_id_returns_200_or_404():
    project = _create_project("Individual")
    state_id = _existing_state_id()
    created = client.post(
        "/tasks",
        json={"title": "Única", "project_id": project["id"], "state_id": state_id},
    ).json()

    found = client.get(f"/tasks/{created['id']}")
    assert found.status_code == 200
    assert found.json() == created

    missing = client.get("/tasks/0")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Tarea no encontrada"}


def test_patch_task_updates_only_provided_fields():
    project = _create_project("Patch")
    state_id = _existing_state_id()
    created = client.post(
        "/tasks",
        json={
            "title": "Original",
            "description": "Descripción original",
            "project_id": project["id"],
            "state_id": state_id,
        },
    ).json()

    response = client.patch(f"/tasks/{created['id']}", json={"title": "Renombrada"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renombrada"
    assert body["description"] == "Descripción original"
    assert body["project_id"] == project["id"]
    assert body["state_id"] == state_id


def test_patch_task_returns_404_for_missing_id():
    response = client.patch("/tasks/0", json={"title": "No existe"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Tarea no encontrada"}


def test_patch_task_returns_422_for_invalid_references():
    project = _create_project("Patch invalido")
    state_id = _existing_state_id()
    created = client.post(
        "/tasks",
        json={"title": "Válida", "project_id": project["id"], "state_id": state_id},
    ).json()

    bad_project = client.patch(f"/tasks/{created['id']}", json={"project_id": 0})
    assert bad_project.status_code == 422

    bad_state = client.patch(f"/tasks/{created['id']}", json={"state_id": 0})
    assert bad_state.status_code == 422

    bad_title = client.patch(f"/tasks/{created['id']}", json={"title": "   "})
    assert bad_title.status_code == 422


def test_delete_task_returns_204_and_then_404_on_get():
    project = _create_project("Delete")
    state_id = _existing_state_id()
    created = client.post(
        "/tasks",
        json={"title": "Borrar", "project_id": project["id"], "state_id": state_id},
    ).json()

    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""

    after = client.get(f"/tasks/{created['id']}")
    assert after.status_code == 404


def test_delete_task_returns_404_for_missing_id():
    response = client.delete("/tasks/0")

    assert response.status_code == 404
    assert response.json() == {"detail": "Tarea no encontrada"}
