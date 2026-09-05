# Plan: Tareas (v1 CRUD + v2 Fechas Límite)

## Contexto

`docs/contrato-api.md` fija el comportamiento observable de **Tareas v1**
(CRUD completo: `POST/GET/GET{id}/PATCH/DELETE /tasks`, con `project_id` y
`state_id` obligatorios y validados) y **Tareas v2** (`due_at` opcional,
tz-aware, normalizado a UTC en la salida; filtro `GET /tasks?overdue=true`).
Nada de esto existe todavía en el repo — este plan implementa las dos
secciones completas, en incrementos pequeños, separando dominio de HTTP
igual que `docs/plan-proyectos.md`, y siguiendo la regla de
`docs/decisiones-ingenieria.md` de que una capacidad nueva arranca con un
test que falla por su ausencia.

**Decisiones ya tomadas con el usuario** (el contrato no las resolvía por sí
solo):

1. La normalización de `title` se implementa **completa desde el
   incremento de dominio**: `strip()` de los extremos y rechazo con `422`
   si no queda ningún carácter fuera de las categorías Unicode `Cc`, `Cf`,
   `Zl`, `Zp`, `Zs` — no se deja como regresión pendiente de una sesión
   futura.
2. Un `project_id` o `state_id` inexistente al crear o actualizar una tarea
   responde **`422`** (entrada inválida), no `404`.

## Qué existe ya (exploración)

- `app/projects.py`: patrón de dominio a seguir (`Table` Core +
  `create_*`/`list_*`/`get_*`/`update_*`, cada función abre su propia
  conexión). `create_project`/`update_project` ya muestran el patrón de
  `INSERT`/`UPDATE ... RETURNING`.
- `app/states.py`: solo tiene `list_states()`. **No existe** una función
  para obtener un estado por `id` — hace falta agregar `get_state(id)` para
  que el dominio de tareas valide `state_id`.
- `app/main.py`: endpoints de `health`, `states` y `projects` (`POST`,
  `GET`, `GET/{id}`, `PATCH` — sin `DELETE`, ver `docs/plan-proyectos.md`).
- `alembic/versions/0b1435f82fdb_...`: migración más reciente (tabla
  `projects`). Es el `down_revision` de la primera migración de este plan.
- `tests/conftest.py`: fixture `autouse` que corre `alembic upgrade head`
  antes de cada test — se hereda gratis.
- No existe `tasks_table`, módulo de dominio, esquema Pydantic, endpoint,
  ni migración de tareas.

## Fuera de alcance

- `DELETE /projects/{id}` con el chequeo real de `409` (sección
  "Proyectos" del contrato, no "Tareas"): queda desbloqueado porque la
  tabla `tasks` va a existir, pero es un plan aparte si se quiere retomarlo.
- Recordatorios, scheduler, zona horaria preferida del usuario y cambio
  automático de estado — explícitamente fuera de alcance en el propio
  contrato (sección Tareas v2).
- Modificar `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`,
  `CLAUDE.md`, `README.md`, `.gitignore` o `.env`.

## Incrementos

### Incremento 1 — Migración de la tabla `tasks` (v1)

Nueva migración (`down_revision = "0b1435f82fdb"`) que crea
`tasks(id, title, description, project_id, state_id)`: `title` `String`
`NOT NULL`, `description` `String` `NULL`, `project_id` `Integer` `NOT NULL`
con FK a `projects.id`, `state_id` `Integer` `NOT NULL` con FK a
`states.id` (sin `ON DELETE CASCADE` — consistente con "no hay borrado en
cascada implícito" del contrato). `downgrade` hace `DROP TABLE`.

**Comprobación (aislada):** `tests/test_tasks_migration.py`, mismo patrón
que `tests/test_projects_migration.py`: downgrade a `0b1435f82fdb`,
verifica que `tasks` desaparece y `projects`/`states` siguen; upgrade a
`head`; verifica columnas y nulabilidad vía `information_schema.columns`, y
que existen las dos foreign keys vía `information_schema.table_constraints`
/ `key_column_usage`.

### Incremento 2 — Normalización de título (función pura)

`app/tasks.py` nuevo: `normalize_task_title(title: str) -> str` — recorta
extremos con `strip()` y levanta una excepción de dominio (`TaskValidationError`,
definida en este mismo módulo) si no queda ningún carácter fuera de las
categorías Unicode `Cc`, `Cf`, `Zl`, `Zp`, `Zs`. Sin base de datos, sin HTTP.

**Comprobación (aislada):** `tests/test_tasks_title_normalization.py` —
casos: `" Regar "` → `"Regar"`; `""` y `"   "` → rechazado; `"​"`
(espacio de ancho cero, invisible) solo → rechazado; un título con
caracteres visibles rodeados de invisibles → aceptado.

### Incremento 3 — Dominio de tareas v1: crear, listar, obtener

En `app/tasks.py`: `tasks_table` (Core, reflejando la migración) y
`create_task(title, project_id, state_id, description=None)` (valida
`project_id` con `app.projects.get_project`, `state_id` con la nueva
`app.states.get_state` — agregada en este incremento —, normaliza el
título con la función del incremento 2; cualquier fallo levanta
`TaskValidationError`), `list_tasks(project_id=None, state_id=None)`
(filtros solos o combinados, orden por `id` ascendente), `get_task(id)`.
Se agrega `get_state(state_id) -> Row | None` a `app/states.py` (única
adición a ese archivo). Sin endpoint todavía.

**Comprobación (aislada):** `tests/test_tasks_domain.py` — crea un
proyecto y usa un estado real del catálogo; `create_task` feliz; `project_id`
inexistente → `TaskValidationError`; `state_id` inexistente →
`TaskValidationError`; título inválido → `TaskValidationError`;
`list_tasks()` sin filtro devuelve todo ordenado por `id`; con `project_id`,
con `state_id`, y ambos combinados.

### Incremento 4 — Endpoint `POST /tasks`

Esquema Pydantic `TaskCreate` (`title: str`, `description: str | None = None`,
`project_id: int`, `state_id: int`) y el endpoint en `app/main.py`, que
traduce `TaskValidationError` a `422` con `{"detail": "<mensaje>"}`. `201`
con el recurso creado en el esquema exacto v1 (sin `due_at` todavía).

**Comprobación (aislada, TDD):** `tests/test_tasks.py` (nuevo) —
creación feliz (`201`); `project_id` inexistente (`422`); `state_id`
inexistente (`422`); título vacío/solo espacios (`422`). Falla antes de
implementar (RED), pasa después (GREEN).

### Incremento 5 — Endpoints `GET /tasks` y `GET /tasks/{id}`

`GET /tasks` admite `project_id` y `state_id` como query params, solos o
combinados, orden por `id`. `GET /tasks/{id}` → `200` o `404`.

**Comprobación (aislada, TDD):** en `tests/test_tasks.py` — lista sin
filtro, con `project_id`, con `state_id`, con ambos; `200` para id
existente, `404` para inexistente.

### Incremento 6 — Endpoint `PATCH /tasks/{id}`

`update_task(id, **fields)` en `app/tasks.py` (revalida `project_id`/`state_id`/
`title` si vienen en `fields`, igual que `create_task`; `None` si el `id`
no existe). Esquema `TaskUpdate` con los cuatro campos opcionales,
`exclude_unset=True`. `200` con el recurso actualizado; `404` si no existe;
`422` si algún campo provisto es inválido.

**Comprobación (aislada, TDD):** actualización parcial que no pisa campos
omitidos; `404` en id inexistente; `422` con `project_id`/`state_id`/`title`
inválido en la actualización.

### Incremento 7 — Endpoint `DELETE /tasks/{id}`

`delete_task(id) -> bool` en `app/tasks.py`. Endpoint: `204` sin cuerpo si
existía; `404` si no existe (aplicando la convención general del contrato
de `404` para recurso inexistente, igual que en `GET`/`PATCH`).

**Comprobación (aislada, TDD):** `DELETE` de una tarea existente → `204`
sin cuerpo, y `GET` posterior a ese id → `404`; `DELETE` de un id
inexistente → `404`.

### Incremento 8 — Migración v2: agregar `due_at`

Nueva migración (`down_revision` = la del incremento 1) que hace
`ALTER TABLE tasks ADD COLUMN due_at TIMESTAMP WITH TIME ZONE NULL`.
`downgrade` quita la columna.

**Comprobación (aislada):** `tests/test_tasks_migration.py` (ampliado) —
tras `upgrade head`, `due_at` existe, es nullable y de tipo con zona
horaria; tras `downgrade` a la revisión del incremento 1, la columna
desaparece sin afectar el resto de `tasks`.

### Incremento 9 — Dominio v2: aceptar y validar `due_at`

`create_task`/`update_task` aceptan `due_at: datetime | None = None`. Si
viene sin `tzinfo`, `TaskValidationError` (`422`, ambigua). Con `tzinfo`,
se guarda tal cual — Postgres `timestamptz` la normaliza a UTC
internamente, sin lógica adicional.

**Comprobación (aislada):** `tests/test_tasks_domain.py` (ampliado) —
crear con `due_at` con offset (`+02:00`) y verificar que se recupera en
UTC; crear con `due_at` naive (sin zona) → `TaskValidationError`; crear sin
`due_at` → `None`; actualizar solo `due_at` sin afectar el resto de campos.

### Incremento 10 — Serialización de `due_at` en las rutas de tareas

El serializador de tarea usado por `POST`/`GET` lista/`GET /{id}`/`PATCH`
incluye `due_at`, formateado siempre en UTC con `Z` y sin microsegundos
(`2026-03-01T09:00:00Z`), `null` cuando no está definido.

**Comprobación (aislada, TDD):** `tests/test_tasks.py` (ampliado) — crear
una tarea con `due_at` con offset y verificar el formato exacto de salida
en la respuesta de `POST`, `GET /tasks`, `GET /tasks/{id}` y `PATCH`;
crear sin `due_at` y verificar `"due_at": null`.

### Incremento 11 — Filtro `GET /tasks?overdue=true`

`list_tasks` admite `overdue: bool = False`: cuando es `True`, además de
los filtros existentes (combinable con `project_id`/`state_id`), devuelve
solo tareas con `due_at` anterior al instante de evaluación
(`datetime.now(timezone.utc)`) y cuyo estado (vía join con `states`) tenga
`code != "HECHA"`. Una tarea sin `due_at` nunca aparece.

**Comprobación (aislada, TDD):** tarea vencida con estado distinto de
`HECHA` → aparece en `overdue=true`; tarea vencida con estado `HECHA` → no
aparece; tarea sin `due_at` → no aparece; tarea con `due_at` futuro → no
aparece; `overdue=true` combinado con `project_id`.

## Verificación end-to-end (después de los once incrementos, no antes)

```bash
docker compose up -d
uv run alembic upgrade head
uv run pytest -q
uv run ruff check .
```

Todos los tests existentes (`health`, `states*`, `projects*`, `database`,
`migrations`) deben seguir en verde sin modificarlos.

## Cómo se ejecuta

Un incremento por turno. Al terminar cada uno, se detiene y se espera
aprobación antes de tocar el siguiente — no se encadenan.
