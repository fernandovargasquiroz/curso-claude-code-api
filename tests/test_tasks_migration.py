from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.database import get_database_url

REPO_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    return Config(str(REPO_ROOT / "alembic.ini"))


def test_tasks_migration_creates_and_drops_table_with_expected_columns():
    cfg = _alembic_config()
    engine = create_engine(get_database_url())

    command.downgrade(cfg, "0b1435f82fdb")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.tasks')")).scalar() is None
        assert conn.execute(text("SELECT to_regclass('public.projects')")).scalar() is not None
        assert conn.execute(text("SELECT to_regclass('public.states')")).scalar() is not None

    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        columns = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    "SELECT column_name, is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'tasks'"
                )
            ).fetchall()
        }
        foreign_tables = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT ccu.table_name "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.constraint_column_usage ccu "
                    "ON tc.constraint_name = ccu.constraint_name "
                    "WHERE tc.table_name = 'tasks' AND tc.constraint_type = 'FOREIGN KEY'"
                )
            ).fetchall()
        }

    assert columns["title"] == "NO"
    assert columns["description"] == "YES"
    assert columns["project_id"] == "NO"
    assert columns["state_id"] == "NO"
    assert foreign_tables == {"projects", "states"}

    engine.dispose()


def test_due_at_migration_adds_and_drops_nullable_timestamptz_column():
    cfg = _alembic_config()
    engine = create_engine(get_database_url())

    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT is_nullable, data_type FROM information_schema.columns "
                "WHERE table_name = 'tasks' AND column_name = 'due_at'"
            )
        ).one()
    assert row[0] == "YES"
    assert row[1] == "timestamp with time zone"

    command.downgrade(cfg, "d1b5f0872ce7")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.tasks')")).scalar() is not None
        remaining_columns = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'tasks'"
                )
            ).fetchall()
        }
    assert "due_at" not in remaining_columns

    command.upgrade(cfg, "head")
    engine.dispose()
