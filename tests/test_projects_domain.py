from app.projects import create_project, list_projects, update_project


def test_list_projects_returns_created_projects_ordered_by_id():
    first = create_project(name="Casa")
    second = create_project(name="Trabajo", description="Tareas de oficina")

    projects = list_projects()

    ids = [project.id for project in projects]
    assert ids.index(first.id) < ids.index(second.id)

    by_id = {project.id: project for project in projects}
    assert by_id[first.id].name == "Casa"
    assert by_id[first.id].description is None
    assert by_id[second.id].name == "Trabajo"
    assert by_id[second.id].description == "Tareas de oficina"


def test_update_project_changes_only_provided_fields():
    project = create_project(name="Original", description="Descripción original")

    updated = update_project(project.id, name="Renombrado")
    assert updated.name == "Renombrado"
    assert updated.description == "Descripción original"

    updated = update_project(project.id, description="Nueva descripción")
    assert updated.name == "Renombrado"
    assert updated.description == "Nueva descripción"


def test_update_project_returns_none_for_missing_id():
    assert update_project(0, name="No existe") is None
