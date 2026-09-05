from sqlalchemy import Integer, MetaData, String, Table, insert, select, update
from sqlalchemy.engine import Row
from sqlalchemy.schema import Column

from app.database import engine

metadata = MetaData()

projects_table = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
)


def create_project(name: str, description: str | None = None) -> Row:
    statement = (
        insert(projects_table)
        .values(name=name, description=description)
        .returning(projects_table)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).one()
        connection.commit()
        return row


def list_projects() -> list[Row]:
    statement = select(projects_table).order_by(projects_table.c.id)
    with engine.connect() as connection:
        return connection.execute(statement).fetchall()


def get_project(project_id: int) -> Row | None:
    statement = select(projects_table).where(projects_table.c.id == project_id)
    with engine.connect() as connection:
        return connection.execute(statement).one_or_none()


def update_project(project_id: int, **fields: str | None) -> Row | None:
    if not fields:
        return get_project(project_id)
    statement = (
        update(projects_table)
        .where(projects_table.c.id == project_id)
        .values(**fields)
        .returning(projects_table)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).one_or_none()
        connection.commit()
        return row
