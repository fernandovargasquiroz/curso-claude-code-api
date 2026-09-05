import pytest

from app.projects import create_project
from app.states import list_states
from app.tasks import TaskValidationError, create_task, get_task, list_tasks


def _existing_state_id() -> int:
    return list_states()[0].id


def test_create_task_persists_and_returns_the_task():
    project = create_project(name="Casa")
    state_id = _existing_state_id()

    task = create_task(
        title="Regar las plantas",
        project_id=project.id,
        state_id=state_id,
        description="Cada dos días",
    )

    assert task.title == "Regar las plantas"
    assert task.description == "Cada dos días"
    assert task.project_id == project.id
    assert task.state_id == state_id
    assert get_task(task.id).id == task.id


def test_create_task_rejects_nonexistent_project():
    state_id = _existing_state_id()

    with pytest.raises(TaskValidationError):
        create_task(title="Tarea", project_id=0, state_id=state_id)


def test_create_task_rejects_nonexistent_state():
    project = create_project(name="Trabajo")

    with pytest.raises(TaskValidationError):
        create_task(title="Tarea", project_id=project.id, state_id=0)


def test_create_task_rejects_invalid_title():
    project = create_project(name="Otro")
    state_id = _existing_state_id()

    with pytest.raises(TaskValidationError):
        create_task(title="   ", project_id=project.id, state_id=state_id)


def test_list_tasks_orders_by_id_and_filters_by_project_and_state():
    states = list_states()
    project_a = create_project(name="Proyecto A")
    project_b = create_project(name="Proyecto B")

    task_a1 = create_task(title="A1", project_id=project_a.id, state_id=states[0].id)
    task_a2 = create_task(title="A2", project_id=project_a.id, state_id=states[1].id)
    task_b1 = create_task(title="B1", project_id=project_b.id, state_id=states[0].id)

    all_tasks = list_tasks()
    ids = [task.id for task in all_tasks]
    assert ids.index(task_a1.id) < ids.index(task_a2.id) < ids.index(task_b1.id)

    only_project_a = list_tasks(project_id=project_a.id)
    assert {task.id for task in only_project_a} == {task_a1.id, task_a2.id}

    only_state_0 = list_tasks(state_id=states[0].id)
    assert {task.id for task in only_state_0} >= {task_a1.id, task_b1.id}

    combined = list_tasks(project_id=project_a.id, state_id=states[0].id)
    assert {task.id for task in combined} == {task_a1.id}
