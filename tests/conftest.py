from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def ensure_migrations_at_head():
    command.upgrade(Config(str(REPO_ROOT / "alembic.ini")), "head")
