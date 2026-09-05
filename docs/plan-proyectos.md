# Plan: Proyectos (CRUD sin borrado)

## Contexto

`docs/contrato-api.md` fija el comportamiento observable de la sección
**Proyectos**: campos mínimos `id`, `name`, `description` opcional; y cuatro
operaciones — `POST /projects`, `GET /projects`, `GET /projects/{id}`,
`PATCH /projects/{id}` — con esquema de respuesta exacto
`{"id": 1, "name": "Casa", "description": null}` y orden determinista por
`id` ascendente en la lista. Nada de esto existe todavía en el repo. Este
plan cierra esa brecha en incrementos pequeños, separando dominio de HTTP
igual que hizo `docs/plan-persistencia.md` para `states`, y siguiendo la
regla de `docs/decisiones-ingenieria.md` de que una capacidad nueva arranca
con un test que falla por su ausencia.

**Decisión ya tomada con el usuario:** `DELETE /projects/{id}` exige `409`
si el proyecto tiene tareas, pero la tabla `tasks` no existe aún en este
repo (es la siguiente sección del contrato, "Tareas v1", sin implementar).
Por eso `DELETE` queda completamente fuera de este plan — se planifica junto
con Tareas v1, cuando exista la tabla que hace real ese chequeo.

## Qué existe ya (exploración)

- `app/main.py`: solo `GET /health` y `GET /states`. Sin nada de proyectos.
- `app/database.py`: `engine` y `get_connection()` ya listos y reutilizables,
  sin tocar.
- `app/states.py`: patrón a seguir para el módulo de dominio — tabla Core
  con `sqlalchemy.Table` y funciones que abren su propia conexión. `states`
  es solo lectura; `projects` necesita además escritura (`INSERT`,
  `UPDATE`), que es terreno nuevo en este repo.
- `alembic/versions/94f759f184a1_...`: única migración existente, crea y
  siembra `states`. La migración de `projects` cuelga de ella
  (`down_revision = "94f759f184a1"`).
- `tests/conftest.py`: fixture `autouse` que corre `alembic upgrade head`
  antes de cada test — se hereda gratis, no hay que tocarlo.
- No existe `projects_table`, módulo de dominio, esquema Pydantic ni
  endpoint de proyectos.

## Fuera de alcance

- `DELETE /projects/{id}` y el chequeo `409` por tareas asociadas (ver
  decisión arriba): se planifica con Tareas v1.
- Tareas (todas sus versiones), `due_at`, filtros de `GET /tasks`.
- Cualquier normalización de `name`/`description` estilo la de `title` de
  tarea: el contrato solo exige esa regla Unicode para el título de tarea,
  no para el nombre de proyecto — un `name` vacío o solo espacios no se
  rechaza en este plan.
- Modificar `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
  `CLAUDE.md`, `README.md`, `.gitignore` o `.env`.

## Incrementos

### Incremento 1 — Migración de la tabla `projects`

Nueva migración de Alembic (`down_revision = "94f759f184a1"`) que crea
`projects(id, name, description)`: `id` entero autogenerado (PK), `name`
`String` `NOT NULL`, `description` `String` `NULL`. Sin seed — a diferencia
de `states`, `projects` no es catálogo fijo, nace vacía. `downgrade` hace
`DROP TABLE`.

**Comprobación (aislada):** `tests/test_projects_migration.py`, mismo patrón
que `tests/test_migrations.py`: parte de `head` (ya garantizado por el
fixture), hace `command.downgrade(cfg, "94f759f184a1")`, verifica con
`to_regclass('public.projects')` que la tabla desaparece y que `states`
sigue intacta, comprueba vía `information_schema.columns` que `name` es
`NOT NULL` y `description` admite `NULL` tras volver a `upgrade("head")`, y
termina en `head` para no dejar la base a mitad de camino.

### Incremento 2 — Dominio: crear y listar proyectos

`app/projects.py` nuevo: `projects_table` (SQLAlchemy Core, reflejando la
migración) y dos funciones — `create_project(name, description=None)`
(`INSERT ... RETURNING`, devuelve la fila insertada) y `list_projects()`
(filas ordenadas por `id` ascendente, tal como exige el contrato). Sin
Pydantic ni endpoint todavía.

**Comprobación (aislada):** `tests/test_projects_domain.py` — llama a
`create_project` dos veces y verifica que `list_projects()` devuelve ambas
filas en orden de `id`, con `description=None` cuando se omite. No pasa por
HTTP.

### Incremento 3 — Endpoint `POST /projects`

Esquema Pydantic de entrada (`name` requerido, `description` opcional) y de
salida (`id`, `name`, `description`), y el endpoint `POST /projects` en
`app/main.py` usando `create_project` del incremento 2. `201` con el
recurso creado, `description` como `null` si se omite (nunca ausente).

**Comprobación (aislada, TDD):**
`tests/test_projects.py::test_create_project_returns_201_with_created_resource`
— se agrega primero y falla (RED, ruta inexistente) antes de tocar
`app/main.py`; pasa (GREEN) después, con `TestClient` igual que
`tests/test_states.py`.

### Incremento 4 — Endpoints `GET /projects` y `GET /projects/{id}`

Se añade `get_project(id)` a `app/projects.py` (fila o `None` si no existe),
y los dos endpoints de lectura: `GET /projects` (lista completa, mismo
esquema) y `GET /projects/{id}` (`200` con el recurso, `404` con
`{"detail": "..."}` si no existe).

**Comprobación (aislada, TDD):** dos tests nuevos en `tests/test_projects.py`
— uno crea proyectos y verifica que `GET /projects` los devuelve en orden de
`id`; otro verifica `200` para un id existente y `404` para uno inexistente.
Fallan antes de implementar (RED), pasan después (GREEN).

### Incremento 5 — Dominio: actualización parcial

`update_project(id, **fields)` en `app/projects.py`: actualiza solo los
campos recibidos (el filtrado de "no enviado" ocurre en el llamador, no
aquí) y devuelve la fila actualizada, o `None` si el `id` no existe. Sin
endpoint todavía.

**Comprobación (aislada):** `tests/test_projects_domain.py` (ampliado) —
crea un proyecto, actualiza solo `name` y verifica que `description` no
cambió; actualiza solo `description` y verifica que `name` no cambió; llama
con un `id` inexistente y verifica que devuelve `None`. No pasa por HTTP.

### Incremento 6 — Endpoint `PATCH /projects/{id}`

Esquema Pydantic de entrada con ambos campos opcionales, leído con
`exclude_unset=True` para no pisar un campo no enviado, y el endpoint
`PATCH /projects/{id}` en `app/main.py` usando `update_project` del
incremento 5. `200` con el recurso actualizado; `404` si el `id` no existe.

**Comprobación (aislada, TDD):** en `tests/test_projects.py` — un test que
actualiza parcialmente y verifica que el campo no enviado no cambió; otro
que hace `PATCH` sobre un `id` inexistente y espera `404`. Fallan antes de
implementar (RED), pasan después (GREEN).

## Verificación end-to-end (después de los seis incrementos, no antes)

```bash
docker compose up -d
uv run alembic upgrade head
uv run pytest -q
uv run ruff check .
```

## Cómo se ejecuta

Un incremento por turno. Al terminar cada uno, se detiene y se espera
aprobación antes de tocar el siguiente — no se encadenan.
