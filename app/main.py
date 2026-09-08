from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.projects import create_project, get_project, list_projects, update_project
from app.states import list_states
from app.tasks import (
    TaskValidationError,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)

app = FastAPI()


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


def _serialize_project(project) -> dict[str, int | str | None]:
    return {"id": project.id, "name": project.name, "description": project.description}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None
    due_at: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=5)


def _serialize_due_at(due_at: datetime | None) -> str | None:
    if due_at is None:
        return None
    return due_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_task(task) -> dict[str, int | str | None]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "project_id": task.project_id,
        "state_id": task.state_id,
        "due_at": _serialize_due_at(task.due_at),
        "priority": task.priority,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states")
def states() -> list[dict[str, int | str]]:
    return [{"id": state.id, "code": state.code} for state in list_states()]


@app.post("/projects", status_code=201)
def create_project_endpoint(payload: ProjectCreate) -> dict[str, int | str | None]:
    project = create_project(name=payload.name, description=payload.description)
    return _serialize_project(project)


@app.get("/projects")
def projects() -> list[dict[str, int | str | None]]:
    return [_serialize_project(project) for project in list_projects()]


@app.get("/projects/{project_id}")
def get_project_endpoint(project_id: int) -> dict[str, int | str | None]:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _serialize_project(project)


@app.patch("/projects/{project_id}")
def update_project_endpoint(
    project_id: int, payload: ProjectUpdate
) -> dict[str, int | str | None]:
    fields = payload.model_dump(exclude_unset=True)
    project = update_project(project_id, **fields)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return _serialize_project(project)


@app.post("/tasks", status_code=201)
def create_task_endpoint(payload: TaskCreate) -> dict[str, int | str | None]:
    try:
        task = create_task(
            title=payload.title,
            project_id=payload.project_id,
            state_id=payload.state_id,
            description=payload.description,
            due_at=payload.due_at,
            priority=payload.priority,
        )
    except TaskValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _serialize_task(task)


@app.get("/tasks")
def tasks(
    project_id: int | None = None,
    state_id: int | None = None,
    overdue: bool = False,
) -> list[dict[str, int | str | None]]:
    return [
        _serialize_task(task)
        for task in list_tasks(project_id=project_id, state_id=state_id, overdue=overdue)
    ]


@app.get("/tasks/{task_id}")
def get_task_endpoint(task_id: int) -> dict[str, int | str | None]:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _serialize_task(task)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task_endpoint(task_id: int) -> None:
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return None


@app.patch("/tasks/{task_id}")
def update_task_endpoint(
    task_id: int, payload: TaskUpdate
) -> dict[str, int | str | None]:
    fields = payload.model_dump(exclude_unset=True)
    try:
        task = update_task(task_id, **fields)
    except TaskValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _serialize_task(task)
