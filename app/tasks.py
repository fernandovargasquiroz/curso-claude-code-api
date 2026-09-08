import unicodedata
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, MetaData, String, Table, delete, select, update
from sqlalchemy.engine import Row
from sqlalchemy.schema import Column, ForeignKey

from app.database import engine
from app.projects import get_project
from app.states import get_state, states_table

INVISIBLE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


class TaskValidationError(ValueError):
    pass


def normalize_task_title(title: str) -> str:
    trimmed = title.strip()
    if all(unicodedata.category(char) in INVISIBLE_CATEGORIES for char in trimmed):
        raise TaskValidationError("El título no puede estar vacío")
    return trimmed


metadata = MetaData()

tasks_table = Table(
    "tasks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("description", String, nullable=True),
    Column("project_id", Integer, ForeignKey("projects.id"), nullable=False),
    Column("state_id", Integer, ForeignKey("states.id"), nullable=False),
    Column("due_at", DateTime(timezone=True), nullable=True),
)


def _validate_references(project_id: int, state_id: int) -> None:
    if get_project(project_id) is None:
        raise TaskValidationError(f"El proyecto {project_id} no existe")
    if get_state(state_id) is None:
        raise TaskValidationError(f"El estado {state_id} no existe")


def _validate_due_at(due_at: datetime | None) -> None:
    if due_at is not None and due_at.tzinfo is None:
        raise TaskValidationError("due_at debe incluir zona horaria")


def create_task(
    title: str,
    project_id: int,
    state_id: int,
    description: str | None = None,
    due_at: datetime | None = None,
) -> Row:
    _validate_references(project_id, state_id)
    _validate_due_at(due_at)
    normalized_title = normalize_task_title(title)
    statement = (
        tasks_table.insert()
        .values(
            title=normalized_title,
            description=description,
            project_id=project_id,
            state_id=state_id,
            due_at=due_at,
        )
        .returning(tasks_table)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).one()
        connection.commit()
        return row


def list_tasks(
    project_id: int | None = None,
    state_id: int | None = None,
    overdue: bool = False,
) -> list[Row]:
    statement = select(tasks_table)
    if project_id is not None:
        statement = statement.where(tasks_table.c.project_id == project_id)
    if state_id is not None:
        statement = statement.where(tasks_table.c.state_id == state_id)
    if overdue:
        not_done_state_ids = select(states_table.c.id).where(
            states_table.c.code != "HECHA"
        )
        statement = statement.where(
            tasks_table.c.due_at < datetime.now(UTC),
            tasks_table.c.state_id.in_(not_done_state_ids),
        )
    statement = statement.order_by(tasks_table.c.id)
    with engine.connect() as connection:
        return connection.execute(statement).fetchall()


def get_task(task_id: int) -> Row | None:
    statement = select(tasks_table).where(tasks_table.c.id == task_id)
    with engine.connect() as connection:
        return connection.execute(statement).one_or_none()


def update_task(task_id: int, **fields) -> Row | None:
    if not fields:
        return get_task(task_id)

    if "project_id" in fields and get_project(fields["project_id"]) is None:
        raise TaskValidationError(f"El proyecto {fields['project_id']} no existe")
    if "state_id" in fields and get_state(fields["state_id"]) is None:
        raise TaskValidationError(f"El estado {fields['state_id']} no existe")
    if "title" in fields:
        fields["title"] = normalize_task_title(fields["title"])
    if "due_at" in fields:
        _validate_due_at(fields["due_at"])

    statement = (
        update(tasks_table)
        .where(tasks_table.c.id == task_id)
        .values(**fields)
        .returning(tasks_table)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).one_or_none()
        connection.commit()
        return row


def delete_task(task_id: int) -> bool:
    statement = delete(tasks_table).where(tasks_table.c.id == task_id)
    with engine.connect() as connection:
        result = connection.execute(statement)
        connection.commit()
        return result.rowcount > 0
