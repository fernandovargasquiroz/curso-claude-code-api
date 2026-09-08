---
name: segmentar-commits
description: Reparte los cambios pendientes del repositorio en commits atómicos usando Conventional Commits, partiendo siempre del estado real del repo (git status --short + git diff --stat, nunca el diff completo) en el momento de invocarla. Cada commit tiene una sola intención y deja el repo en un estado comprobable; el prefijo (feat/fix/refactor/test/docs/chore/...) se elige según qué hace el commit, no según el tipo de archivo. Muestra el reparto propuesto y espera aprobación explícita antes de confirmar cualquier commit. Úsala cuando el usuario pida dividir cambios pendientes en varios commits.
argument-hint: [alcance opcional]
---

# Segmentar Commits

## Propósito

Repartir los cambios pendientes del working tree en commits atómicos,
cada uno con una sola intención, en un orden donde cada commit sea un punto
comprobable del repositorio — no una foto a medio terminar — y con el
prefijo de Conventional Commits que corresponde a esa intención.

## Paso 0 — Estado real, no supuesto

Primer paso siempre, sin excepción, y sin sustituirlo por lo que "debería"
haber cambiado según turnos anteriores de la conversación:

```bash
git status --short
git diff --stat
git diff --stat --cached
```

Nunca `git diff` a secas ni el contenido completo de un archivo en este
paso: lo que hace falta acá es el mapa del cambio — qué archivos, cuántas
líneas, en qué dirección — no su contenido línea por línea. Si más adelante
hace falta ver el contenido real de un archivo puntual (por ejemplo, para
decidir si dos cambios en el mismo archivo son la misma intención o dos
distintas), se lee con el diff acotado a ese archivo (`git diff -- <archivo>`)
recién en ese momento — nunca de entrada, y nunca para todos los archivos a
la vez.

## Paso 1 — Agrupar por intención, no por archivo ni por tipo

Cada commit tiene una sola intención (una funcionalidad, una corrección, un
cambio de estructura, una tarea de mantenimiento) — nunca "cambios varios".
Señales para separar dos cambios en dos commits distintos aunque toquen el
mismo archivo: resuelven objetivos distintos, uno depende de que el otro ya
exista, o uno es reversible sin afectar al otro.

## Paso 2 — Ordenar para que cada commit sea un estado comprobable

El orden no es arbitrario: cada commit, aplicado en secuencia, debe dejar el
repositorio en un punto donde se pueda correr la suite (`uv run pytest -q`)
sin romper por una referencia a algo que todavía no existe. Ejemplos:
una migración de Alembic va antes que el código que lee esa tabla; el
dominio que expone una función va antes que el endpoint que la usa; un test
que ejercita una capacidad va en el mismo commit que esa capacidad, nunca en
uno posterior — eso dejaría un commit intermedio con la capacidad sin
comprobar.

## Paso 3 — Elegir el prefijo de Conventional Commits por lo que hace, no por el archivo

No hay mapeo mecánico "archivo de test → `test:`", "archivo de config →
`chore:`". El prefijo depende de la intención real del commit completo:

- `feat`: agrega una capacidad observable nueva (puede incluir su
  migración, su dominio y su test — sigue siendo `feat` aunque toque tres
  archivos).
- `fix`: corrige un comportamiento incorrecto.
- `refactor`: cambia la estructura interna sin cambiar comportamiento
  observable.
- `test`: agrega o ajusta tests sin que cambie código de producción en ese
  mismo commit.
- `docs`: solo documentación (`docs/`, `README.md`, comentarios).
- `chore`: mantenimiento sin efecto en comportamiento (config local,
  `.gitignore`, dependencias).
- Otros prefijos estándar (`build`, `ci`, `perf`, `style`) cuando apliquen
  con precisión — no forzarlos si no encajan.

Un commit que agrega una migración **y** el código que la usa **y** su test
es `feat`, no tres tipos distintos — el tipo de archivo no decide el
prefijo, la intención sí.

## Paso 4 — Mostrar el reparto propuesto y esperar aprobación

Antes de tocar nada: lista numerada de commits, cada uno con los archivos
exactos y el mensaje Conventional Commits completo (tipo, alcance opcional,
descripción). Ningún `git add`/`git commit` se ejecuta hasta que el usuario
apruebe explícitamente ese reparto — "muéstrame" o "proponé" no es
aprobación.

## Reglas fijas (no negociables)

- Cada commit se arma exclusivamente con `git add` (archivo completo) o
  `git add -p` (fragmentos) sobre el cambio que ya existe en el working
  tree. Nunca se edita, reescribe ni regenera el contenido de un archivo
  para construir o simular un estado intermedio.
- `.env` nunca entra en ningún commit (`docs/decisiones-ingenieria.md`).
- Nunca `git push`, `git add -A` / `git add .`, `--amend`, ni reescritura de
  historia.
- Si un commit falla al confirmarse (p. ej. un hook), reportar la salida
  completa y detenerse — no seguir con los commits restantes ni usar
  `--no-verify`.

## Límite

Esta skill no decide qué cambiar en el código, ni lo edita ni lo reescribe:
solo reparte con `git add` (completo o `-p`) lo que ya existe en el working
tree. No hace `git push` bajo ninguna circunstancia.
