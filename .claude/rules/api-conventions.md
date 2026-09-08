# API Conventions

Cualquier endpoint nuevo o modificado en `app/main.py` sigue el esquema de
respuesta exacto que define `docs/contrato-api.md`: ni un campo de más ni
de menos.

Cualquier campo nuevo en un recurso se añade en sus tres capas, en este
orden:

1. **Migración** (`alembic/versions/`): la columna en la tabla
   correspondiente, con `upgrade` y `downgrade`.
2. **Esquema** (el módulo de dominio en `app/`, por ejemplo `app/tasks.py`):
   la columna en la `Table` de SQLAlchemy y su paso a través de las
   funciones de dominio.
3. **Validación en el endpoint** (`app/main.py`): el campo en el esquema
   Pydantic de entrada (`TaskCreate`/`TaskUpdate` o el que corresponda),
   con la regla de validación que le toque.

Mismo patrón que `priority`: migración, esquema y validación en el
endpoint, sin saltarse ninguna capa.
