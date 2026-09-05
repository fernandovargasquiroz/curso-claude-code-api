from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.database import get_database_url

REPO_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    return Config(str(REPO_ROOT / "alembic.ini"))


def test_projects_migration_creates_and_drops_table_with_expected_columns():
    cfg = _alembic_config()
    engine = create_engine(get_database_url())

    command.downgrade(cfg, "94f759f184a1")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.projects')")).scalar() is None
        assert conn.execute(text("SELECT to_regclass('public.states')")).scalar() is not None

    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        columns = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'projects'"
                )
            ).fetchall()
        }
    assert columns["name"] == "NO"
    assert columns["description"] == "YES"

    engine.dispose()
