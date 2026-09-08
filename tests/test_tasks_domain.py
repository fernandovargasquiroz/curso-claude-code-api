from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.projects import create_project
from app.states import list_states
from app.tasks import TaskValidationError, create_task, get_task, list_tasks, update_task


def _existing_state_id() -> int:
    return list_states()[0].id


def _state_id_with_code(code: str) -> int:
    return next(state.id for state in list_states() if state.code == code)


def _state_id_other_than(code: str) -> int:
    return next(state.id for state in list_states() if state.code != code)


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


def test_create_task_without_due_at_stores_none():
    project = create_project(name="Sin fecha")
    state_id = _existing_state_id()

    task = create_task(title="Sin due_at", project_id=project.id, state_id=state_id)

    assert task.due_at is None


def test_create_task_with_tz_aware_due_at_is_stored_and_read_back_in_utc():
    project = create_project(name="Con fecha")
    state_id = _existing_state_id()
    due_at = datetime(2026, 3, 1, 11, 0, 0, tzinfo=timezone(timedelta(hours=2)))

    task = create_task(
        title="Con due_at", project_id=project.id, state_id=state_id, due_at=due_at
    )

    assert task.due_at.astimezone(UTC) == due_at.astimezone(UTC)


def test_create_task_rejects_naive_due_at():
    project = create_project(name="Fecha ambigua")
    state_id = _existing_state_id()
    naive_due_at = datetime(2026, 3, 1, 9, 0, 0)

    with pytest.raises(TaskValidationError):
        create_task(
            title="Ambigua", project_id=project.id, state_id=state_id, due_at=naive_due_at
        )


def test_update_task_can_change_only_due_at():
    project = create_project(name="Patch fecha")
    state_id = _existing_state_id()
    task = create_task(
        title="Original",
        description="Descripción",
        project_id=project.id,
        state_id=state_id,
    )
    due_at = datetime(2026, 4, 1, tzinfo=UTC)

    updated = update_task(task.id, due_at=due_at)

    assert updated.due_at == due_at
    assert updated.title == "Original"
    assert updated.description == "Descripción"


def test_update_task_rejects_naive_due_at():
    project = create_project(name="Patch fecha ambigua")
    state_id = _existing_state_id()
    task = create_task(title="Tarea", project_id=project.id, state_id=state_id)

    with pytest.raises(TaskValidationError):
        update_task(task.id, due_at=datetime(2026, 4, 1))


def test_list_tasks_overdue_filter():
    project = create_project(name="Vencidas")
    not_done_state = _state_id_other_than("HECHA")
    done_state = _state_id_with_code("HECHA")
    past = datetime.now(UTC) - timedelta(days=1)
    future = datetime.now(UTC) + timedelta(days=1)

    overdue_task = create_task(
        title="Vencida", project_id=project.id, state_id=not_done_state, due_at=past
    )
    create_task(
        title="Vencida pero hecha",
        project_id=project.id,
        state_id=done_state,
        due_at=past,
    )
    create_task(
        title="Sin fecha", project_id=project.id, state_id=not_done_state
    )
    create_task(
        title="Futura", project_id=project.id, state_id=not_done_state, due_at=future
    )

    overdue = list_tasks(project_id=project.id, overdue=True)

    assert {task.id for task in overdue} == {overdue_task.id}
