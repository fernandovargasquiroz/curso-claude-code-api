from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.projects import create_project, get_project, list_projects, update_project
from app.states import list_states

app = FastAPI()


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


def _serialize_project(project) -> dict[str, int | str | None]:
    return {"id": project.id, "name": project.name, "description": project.description}


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
