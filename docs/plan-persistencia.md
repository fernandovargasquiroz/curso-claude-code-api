# Plan: Conectar la API a PostgreSQL (Salud y Estados)

## Contexto

`docs/contrato-api.md` fija el comportamiento observable de `GET /health`
(ya implementado) y de `GET /states` (todavía no). La migración inicial de
Alembic (`alembic/versions/94f759f184a1_create_states_catalog.py`, ya
aplicada y verificada en ambos sentidos) crea y siembra la tabla `states`
con el catálogo fijo `PENDIENTE, EN_CURSO, BLOQUEADA, HECHA`, cada uno con su
`sort_order`. Falta la pieza que le falta a la app: nunca abre una conexión
a Postgres por sí misma. Este plan cierra esa brecha en incrementos
pequeños, cada uno confirmable de forma aislada, siguiendo la regla de
`docs/decisiones-ingenieria.md` de que una capacidad nueva arranca con un
test que falla por su ausencia, y de que la persistencia se prueba contra
PostgreSQL real, nunca SQLite.

## Qué existe ya (exploración)

- `app/main.py`: solo `GET /health` → `{"status": "ok"}`. Sin dependencias
  de base de datos.
- `app/database.py`: ya existe `get_database_url()`, arma la URL
  `postgresql+psycopg://...` leyendo `POSTGRES_*` de variables de entorno
  (cargadas por `python-dotenv`, nunca abriendo `.env` directamente), con
  `POSTGRES_HOST` por defecto `localhost`. No crea ningún `Engine` todavía.
- `alembic/`: configurado, con una sola migración (`94f759f184a1`) que crea
  `states(id, code, sort_order)` y siembra las 4 filas fijas. `downgrade`
  hace `DROP TABLE`. Ya se verificó `upgrade`/`downgrade` en ambos sentidos
  contra Postgres real.
- `tests/test_health.py`: patrón de referencia con `TestClient`.
- `tests/test_migrations.py`: patrón de referencia para tests que requieren
  Postgres real (usa `alembic.command` + `create_engine(get_database_url())`).
- No hay ningún `Engine`/sesión de SQLAlchemy vivo en `app/`, ni tabla Core
  declarada para consultar `states` desde la aplicación, ni endpoint
  `GET /states`.

## Fuera de alcance

Proyectos, tareas, filtros, `due_at`, skills, hooks, CI. Tampoco se
modifican `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
`CLAUDE.md`, `.gitignore` ni `.env` (y `.env` no se abre en ningún
incremento).

## Incrementos

### Incremento 1 — Motor de conexión reutilizable en `app/`

Añadir a `app/database.py` un `Engine` de SQLAlchemy construido sobre
`get_database_url()` (ya existente, sin tocarlo) y una función/dependencia
que entregue una conexión y la cierre al terminar. Ningún endpoint la usa
todavía: es solo la tubería.

**Comprobación (aislada):** un test nuevo, `tests/test_database.py`, que
abre una conexión real contra Postgres (no SQLite, según
`docs/decisiones-ingenieria.md`) y ejecuta `SELECT 1`. Corre contra el
contenedor `db` ya levantado. No depende de la migración de `states` ni de
ningún endpoint.

### Incremento 2 — Lectura del catálogo `states` desde la app

Declarar en `app/database.py` (o un módulo nuevo pequeño, p.ej.
`app/states.py`) la tabla `states` como `sqlalchemy.Table` (Core, reflejando
exactamente las columnas de la migración: `id`, `code`, `sort_order` — sin
introducir una capa ORM/declarativa que nadie pidió) y una función que
devuelva las filas ordenadas por `sort_order` y `id` como desempate, tal
como exige `docs/contrato-api.md`. Sigue sin haber endpoint HTTP.

**Comprobación (aislada):** un test que, contra la base ya sembrada por la
migración (`uv run alembic upgrade head`), llama directamente a esa función
y verifica que devuelve los 4 códigos en el orden exacto
`PENDIENTE, EN_CURSO, BLOQUEADA, HECHA`. No pasa por HTTP ni por FastAPI.

### Incremento 3 — Endpoint `GET /states`

Siguiendo la regla de TDD del equipo: primero un test HTTP que falla porque
el endpoint no existe (`tests/test_states.py`, con el mismo patrón que
`tests/test_health.py`), después la implementación en `app/main.py` que usa
la función del incremento 2 y serializa exactamente el esquema del
contrato (`{"id": 1, "code": "PENDIENTE"}`, lista JSON en la raíz, sin
campo `sort_order` ni envoltorio).

**Comprobación (aislada):** el test de HTTP debe fallar antes de tocar
`app/main.py` (RED) y pasar después (GREEN): `GET /states` responde `200`
con los 4 estados en el orden del contrato y el esquema exacto — ni un
campo de más.

## Nota explícita sobre `GET /health`

`docs/contrato-api.md` no exige que `/health` dependa de la base de datos
("no expone credenciales ni detalles internos"), así que **no se modifica**
en ningún incremento de este plan. Se cita como fuente solo porque fija el
patrón de test (`TestClient`) que reutilizan los incrementos siguientes.

## Verificación end-to-end (después de los tres incrementos, no antes)

```bash
docker compose up -d
uv run alembic upgrade head
uv run pytest -q
uv run ruff check .
```

## Cómo se ejecuta

Un incremento por turno. Al terminar cada uno, se detiene y se espera
aprobación antes de tocar el siguiente — no se encadenan.
