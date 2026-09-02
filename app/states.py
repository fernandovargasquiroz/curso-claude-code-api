from sqlalchemy import Integer, MetaData, String, Table, select
from sqlalchemy.engine import Row
from sqlalchemy.schema import Column

from app.database import engine

metadata = MetaData()

states_table = Table(
    "states",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String(length=32), nullable=False, unique=True),
    Column("sort_order", Integer, nullable=False),
)


def list_states() -> list[Row]:
    statement = select(states_table).order_by(
        states_table.c.sort_order, states_table.c.id
    )
    with engine.connect() as connection:
        return connection.execute(statement).fetchall()
