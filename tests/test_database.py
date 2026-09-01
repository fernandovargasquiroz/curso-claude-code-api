from sqlalchemy import text

from app.database import get_connection


def test_get_connection_executes_select_1():
    connections = get_connection()

    connection = next(connections)
    assert connection.execute(text("SELECT 1")).scalar() == 1

    exhausted = False
    try:
        next(connections)
    except StopIteration:
        exhausted = True
    assert exhausted
