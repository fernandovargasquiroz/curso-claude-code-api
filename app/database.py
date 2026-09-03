import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import Connection, create_engine

load_dotenv()


def get_database_url() -> str:
    user = os.environ.get("POSTGRES_USER", "appuser")
    password = os.environ.get("POSTGRES_PASSWORD", "app_local_pw")
    db = os.environ.get("POSTGRES_DB", "app_db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(get_database_url())


def get_connection() -> Iterator[Connection]:
    with engine.connect() as connection:
        yield connection
