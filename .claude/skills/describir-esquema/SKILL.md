---
name: describir-esquema
description: Genera docs/esquema.md a partir del estado real de los modelos (app/*.py) y las migraciones (alembic/versions/) — un diagrama de tablas y relaciones en Mermaid, y un diccionario de datos columna por columna. Enlaza docs/contrato-api.md en vez de repetirlo. Úsala cuando el usuario pida documentar, describir o actualizar la documentación del esquema de la base de datos. Esta skill describe: no modifica modelos, migraciones, el contrato ni la base de datos.
argument-hint: (sin argumentos)
---

# Describir Esquema

## Propósito

Producir un único documento, `docs/esquema.md`, que muestre el esquema real
de la base de datos —tablas, columnas, tipos, nulabilidad y relaciones—
leyendo el estado actual de `app/*.py` y `alembic/versions/` en el momento
de invocarla, no una versión recordada o supuesta de turnos anteriores de
la conversación.

## Alcance

Permitido en esta skill:

- Leer `app/database.py` y los módulos de dominio que declaran tablas
  (`app/projects.py`, `app/tasks.py`, `app/states.py`, y cualquier otro que
  declare un `sqlalchemy.Table`).
- Leer todos los archivos de `alembic/versions/`, siguiendo la cadena de
  `down_revision` en el orden real de aplicación, no el orden alfabético ni
  la fecha del archivo.
- Leer `docs/contrato-api.md`, solo para decidir qué NO repetir.
- Escribir un único archivo: `docs/esquema.md` (crearlo si no existe,
  reemplazarlo por completo si existe).

No permitido en esta skill:

- Modificar `app/`, `alembic/`, `docs/contrato-api.md`, ni ningún archivo
  que no sea `docs/esquema.md`.
- Ejecutar migraciones (`alembic upgrade`/`downgrade`), abrir una conexión a
  la base, o correr `docker compose`.
- Inferir el esquema desde una conexión viva a Postgres
  (`information_schema`, `psql \d`, etc.). La fuente de verdad de esta
  skill es el código —modelos y migraciones—, no una base que puede estar
  en cualquier estado intermedio (sin migrar, a mitad de un downgrade).

Si durante la descripción parece necesario hacer algo de esta lista,
detente y dilo como observación en el propio `docs/esquema.md`, no lo
hagas.

## Procedimiento

1. **Estado real, no supuesto** — antes de escribir nada:
   - `ls alembic/versions/*.py` para saber cuántas migraciones existen.
   - Extraer `revision`/`down_revision` de cada una para reconstruir la
     cadena real de aplicación (no confiar en el nombre del archivo ni en
     el orden de `ls`).
   - Ubicar, en `app/*.py`, qué módulos declaran un `Table(...)` y con qué
     nombre, antes de leer ninguno entero.

   Ninguna tabla ni columna se documenta por lo que dice
   `docs/contrato-api.md`, un plan de `docs/`, o un turno anterior de la
   conversación — solo por lo que hay ahora mismo en `app/*.py` y
   `alembic/versions/`.

2. **Leer en orden, cruzando ambas fuentes** — para cada tabla:
   - El `Table(...)` en `app/*.py`: columnas, tipo, `nullable`, `unique`,
     `ForeignKey`.
   - La migración (o migraciones, si la tabla cambió después de creada)
     que la originó, siguiendo la cadena de revisiones: tipo SQL real
     (`sa.String(length=32)`, `sa.DateTime(timezone=True)`, etc.),
     `unique`, `ondelete`, o la ausencia de restricciones (`CHECK`, largo
     máximo) que el modelo tampoco declara.
   - Si el modelo y la migración no coinciden en algo, documentar lo que
     dice la migración —es la que describe lo que existe en la base— y
     señalar la discrepancia en el diccionario de datos, sin resolverla ni
     corregir ningún archivo.

3. **Escribir `docs/esquema.md`** con exactamente dos partes:
   - **Diagrama**: un bloque ` ```mermaid ` con `erDiagram`, una entidad
     por tabla con sus columnas (nombre y tipo abreviado, marcando PK/FK) y
     las relaciones según las foreign keys reales. Es texto plano,
     versionable y diferenciable línea por línea, y se renderiza nativo en
     el repositorio (GitHub y la mayoría de los visores de Markdown lo
     soportan sin herramienta adicional).
   - **Diccionario de datos**: una tabla Markdown por cada tabla de la
     base, con columnas `Columna | Tipo | Nulo | Significado`. La columna
     "Significado" solo se completa cuando el nombre no alcanza para
     entenderla (por ejemplo, qué representa `sort_order`, por qué
     `due_at` es `timestamptz` y no `timestamp`, o que `priority` no tiene
     `CHECK` en la base pese al rango que valida la API) — si el nombre ya
     es autoexplicativo, se deja vacía en vez de rellenarla con relleno.

4. **No repetir el contrato** — antes de escribir cualquier explicación de
   comportamiento (qué significa cada estado, las reglas de `due_at`, el
   filtro `overdue`, la forma de los errores), buscar primero si
   `docs/contrato-api.md` ya lo dice. Si lo dice, enlazarlo (por ejemplo
   `[contrato-api.md](contrato-api.md)` o la sección puntual) en vez de
   copiar el texto. `docs/esquema.md` describe estructura; el contrato fija
   comportamiento observable — no se duplican.

5. **Mostrar y confirmar** — mostrar el archivo completo antes de
   guardarlo, y esperar aprobación explícita. Recién ahí escribir
   `docs/esquema.md`.

## Límite

Esta skill describe, no modifica: no toca `app/`, `alembic/`,
`docs/contrato-api.md`, no ejecuta migraciones ni abre conexión a la base.
Si al describir aparece una inconsistencia entre el modelo y la migración,
o entre el esquema y el contrato, se documenta como tal en
`docs/esquema.md` — no se corrige ahí ni en ningún otro archivo.
