from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.database import get_database_url

REPO_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    return Config(str(REPO_ROOT / "alembic.ini"))


def test_states_catalog_is_seeded_and_migrating_twice_does_not_duplicate():
    cfg = _alembic_config()
    engine = create_engine(get_database_url())

    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT code FROM states ORDER BY sort_order")
        ).fetchall()
    assert [row[0] for row in rows] == ["PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA"]

    command.downgrade(cfg, "base")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT to_regclass('public.states')")).scalar() is None

    engine.dispose()
