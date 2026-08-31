# Curso Claude Code API

API construida con FastAPI y administrada con [uv](https://docs.astral.sh/uv/).
El contrato de comportamiento observable vive en `docs/contrato-api.md`.

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose

## Recorrido canónico

1. Instalar dependencias exactas del lockfile:

   ```bash
   uv sync --locked
   ```

2. Ejecutar los tests:

   ```bash
   uv run pytest -q
   ```

3. Revisar el estilo con Ruff:

   ```bash
   uv run ruff check .
   ```

4. Levantar PostgreSQL (opcionalmente, copia `.env.example` a `.env` y ajusta
   los valores antes de este paso; si no lo haces, se usan los valores por
   defecto locales del propio `compose.yaml`):

   ```bash
   docker compose up -d
   ```

5. Ejecutar la API con Uvicorn:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

   Verifica que responde en <http://127.0.0.1:8000/health>.

6. Al terminar, detener los servicios:

   ```bash
   docker compose down
   ```
