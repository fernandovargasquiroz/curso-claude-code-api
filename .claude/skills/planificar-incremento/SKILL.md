---
name: planificar-incremento
description: Genera un plan de implementación incremental para un cambio en la API, guardado en docs/, alineado con docs/contrato-api.md y docs/decisiones-ingenieria.md. Úsala cuando el usuario pida planificar una nueva capacidad o cambio antes de escribir código. Cada incremento declara su propia comprobación ejecutable, ninguna decisión queda aplazada y el alcance excluido se declara explícitamente. Esta skill planifica: no implementa, no escribe ni modifica código, no instala dependencias, no toca la base de datos.
argument-hint: [tema]
---

# Planificar Incremento

## Propósito

Producir, antes de escribir una sola línea de código, un plan de
implementación en incrementos pequeños y verificables para una capacidad o
cambio de la API — siguiendo el patrón ya establecido en
`docs/plan-persistencia.md`.

## Alcance

Permitido en esta skill:

- Leer `docs/contrato-api.md`, `docs/decisiones-ingenieria.md`, `CLAUDE.md`,
  `README.md`, y el código/tests existentes, para explorar qué ya hay.
- Preguntar al usuario cuando algo no se pueda decidir solo con lo que hay en
  el repositorio.
- Escribir un único archivo nuevo en `docs/`.

No permitido en esta skill:

- Crear ni modificar código de la aplicación (`app/`), migraciones
  (`alembic/`), tests, ni ningún archivo fuera de `docs/`.
- Instalar o actualizar dependencias (`uv add`, editar `pyproject.toml` o
  `uv.lock`).
- Tocar la base de datos: no ejecuta `alembic upgrade`/`downgrade`, no abre
  conexiones, no corre `docker compose`.
- Modificar `docs/contrato-api.md` o `docs/decisiones-ingenieria.md` — son
  fuente para planificar, no destino del plan.

Si durante la planificación parece necesario hacer algo de esta lista,
detente y dilo como una recomendación para después, no lo hagas.

## Procedimiento

1. **Documentos contra los que se planifica** — léelos siempre, en este
   orden, antes de escribir una sola línea del plan:
   - `docs/contrato-api.md`: fija el comportamiento observable. El plan no
     puede contradecirlo salvo que el usuario apruebe explícitamente que esa
     parte del contrato cambia.
   - `docs/decisiones-ingenieria.md`: decisiones vinculantes del equipo
     (base de datos, tests, datos locales). El plan las hereda, no las
     reabre.
   - `CLAUDE.md`: arquitectura y estado actual del repositorio.
   - `README.md`: comandos canónicos de instalación/test/lint/run, para que
     las comprobaciones del plan los reutilicen en vez de inventar otros.
   - El código y los tests existentes (`app/`, `tests/`, `alembic/`), para no
     planificar lo que ya está hecho.

2. **Dónde y cómo se llama el resultado** — un único archivo nuevo en
   `docs/`, nombrado `plan-<tema>.md`, donde `<tema>` dice de qué es el plan
   (por ejemplo, `docs/plan-proyectos.md`). No sobrescribas un plan existente
   sin que el usuario lo pida explícitamente.

3. **Incrementos numerados** — el plan se organiza en incrementos, cada uno
   con:
   - Un título breve que dice qué entrega.
   - Alcance lo bastante pequeño para confirmarse de forma aislada, sin
     depender de incrementos posteriores.
   - Su propia **comprobación ejecutable**: un comando o test concreto,
     nombrado, que falla mientras el incremento no existe y pasa cuando sí
     — siguiendo la regla de `docs/decisiones-ingenieria.md` de que una
     capacidad nueva arranca con un test que falla por su ausencia.

4. **Cero decisiones aplazadas** — si al planificar aparece algo que no se
   puede resolver solo con lo que hay en el repositorio (el contrato, las
   decisiones de ingeniería, el código existente), no lo escribas en
   condicional ("se podría", "probablemente") ni lo dejes anotado para
   después: pregúntaselo al usuario en ese momento, antes de seguir. Un plan
   terminado no debería necesitar un commit posterior de "cerrar decisión
   aplazada" (como ocurrió con el incremento 2 de `plan-persistencia.md`).

5. **Fuera de alcance explícito** — el plan nombra, en su propia sección,
   qué queda deliberadamente fuera: funcionalidad, documentos que no se
   tocan, decisiones que no aplican a este plan. Sigue el mismo patrón que la
   sección "Fuera de alcance" de `docs/plan-persistencia.md`.

6. **Aprobación antes de guardar** — muestra el archivo completo al usuario
   y espera su confirmación. Solo entonces escríbelo en `docs/`.

## Límite

Esta skill planifica, no implementa: no crea ni modifica código de la
aplicación, no instala ni actualiza dependencias, y no toca la base de datos
(sin migraciones, sin conexiones, sin `docker compose`). Si el usuario pide
implementar mientras esta skill está en curso, detente y remite esa parte a
una conversación o skill aparte.
